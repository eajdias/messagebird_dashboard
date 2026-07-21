import logging
import re
from datetime import datetime, timedelta

from infrastructure.api import config
from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_core import PgSyncManager

logger = logging.getLogger("m_bird.sync_pg")


async def update_conversation_surveys(manager: PgSyncManager, conn: PostgresSyncConnection, conversation_bird_id: str):
    from domain import constants

    cnvs_row = await conn.fetch_one(
        "SELECT cnvs_id, cnvs_status, cnvs_rating_agent, cnvs_rating_nps FROM conversations WHERE cnvs_bird = $1",
        (conversation_bird_id,),
    )
    if not cnvs_row:
        return
    cnvs_id = cnvs_row["cnvs_id"]

    questions = {
        "lang": r"(?:Escolha|Selecione) seu idioma",
        "software": r"Qual seria o sistema",
        "tax_id": r"Informe por favor o CNPJ de sua empresa ou CPF",
        "dept": r"Selecione o departamento desejado",
        "contact_reason": r"Qual o motivo do contato",
        "occurrence": r"Qual seria a ocorrência",
        "rating_agent": r"como você avalia o atendimento do técnico",
        "rating_nps": r"Avalie.*(?:nosso atendimento|a nossa Empresa)",
    }

    messages = await conn.fetch_all(
        "SELECT msgs_id, msgs_content, msgs_direction, msgs_created "
        "FROM messages WHERE msgs_cnvs = $1 ORDER BY msgs_created ASC",
        (cnvs_id,),
    )

    updates: dict[str, int | str] = {}
    for i, msg in enumerate(messages):
        content = msg["msgs_content"] or ""

        if msg["msgs_direction"] == "sent" and config.PHRASE_TICKET_HEADER in content:
            lines = [ln.strip() for ln in content.split("\n")]
            try:
                idx = next(j for j, ln in enumerate(lines) if config.PHRASE_TICKET_HEADER in ln)
                ticket_lines = [ln for ln in lines[idx + 1 :] if ln and not ln.startswith("===")]
                if len(ticket_lines) >= 4:
                    if "cnvs_contact_reason" not in updates:
                        reason_text = ticket_lines[2]
                        for _dept_id, reasons in constants.REASON_MAP.items():
                            for reason_id, reason_label in reasons.items():
                                if reason_label.lower() == reason_text.lower():
                                    updates["cnvs_contact_reason"] = int(reason_id)
                                    break
                    updates["cnvs_description"] = " ".join(ticket_lines[3:])
                elif ticket_lines:
                    updates["cnvs_description"] = ticket_lines[-1]
            except StopIteration:
                pass

        if msg["msgs_direction"] != "sent":
            continue

        matched_key = None
        for key, pattern in questions.items():
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                matched_key = key
                break

        if matched_key:
            timestamp = msg["msgs_created"]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            for j in range(i + 1, min(i + 10, len(messages))):
                next_msg = messages[j]
                if next_msg["msgs_direction"] != "received":
                    continue
                next_ts = next_msg["msgs_created"]
                if isinstance(next_ts, str):
                    next_ts = datetime.fromisoformat(next_ts.replace("Z", "+00:00"))
                if next_ts - timestamp > timedelta(minutes=60):
                    break
                resp = (next_msg["msgs_content"] or "").strip()
                if not resp:
                    continue

                found = False
                if matched_key == "tax_id":
                    val = re.sub(r"\D", "", resp)
                    if val:
                        updates["cnvs_tax_id"] = val
                        found = True
                elif matched_key == "software":
                    m = re.search(r"(\d+)", resp)
                    num = int(m.group(1)) if m else None
                    for name in config.SOFTWARE_NAMES:
                        if (num is not None and str(num) in resp) or name.upper() in resp.upper():
                            updates["cnvs_software"] = name
                            found = True
                            break
                    if not found:
                        updates["cnvs_software"] = config.DEFAULT_SOFTWARE
                        found = True
                else:
                    m = re.search(r"(\d+)", resp)
                    num = int(m.group(1)) if m else None
                    if num is not None:
                        if matched_key == "lang" and 1 <= num <= 3:
                            updates["cnvs_lang"] = num
                            found = True
                        elif matched_key == "dept" and 1 <= num <= 5:
                            updates["cnvs_dept"] = num
                            found = True
                        elif matched_key == "contact_reason" and 1 <= num <= 6:
                            updates["cnvs_contact_reason"] = num
                            found = True
                        elif matched_key == "occurrence" and 1 <= num <= 6:
                            updates["cnvs_occurrence"] = num
                            found = True
                        elif matched_key == "rating_agent" and 1 <= num <= 5:
                            updates["cnvs_rating_agent"] = num
                            found = True
                        elif matched_key == "rating_nps" and 0 <= num <= 10:
                            updates["cnvs_rating_nps"] = num
                            found = True
                if found:
                    break

    if updates:
        set_parts = []
        params = []
        for idx, (k, v) in enumerate(updates.items(), 1):
            set_parts.append(f"{k} = ${idx}")
            params.append(v)
        set_clause = ", ".join(set_parts)
        params.append(cnvs_id)
        await conn.execute_query(
            f"UPDATE conversations SET {set_clause} WHERE cnvs_id = ${len(params)}",
            tuple(params),
        )


async def backfill_surveys(manager: PgSyncManager, conn: PostgresSyncConnection) -> int:
    rows = await conn.fetch_all(
        "SELECT DISTINCT cv.cnvs_bird "
        "FROM conversations cv "
        "JOIN messages m ON m.msgs_cnvs = cv.cnvs_id "
        "WHERE m.msgs_direction = 'sent' "
        "AND ("
        "  m.msgs_content LIKE '%Avalie%' "
        "  OR m.msgs_content LIKE '%avalia o atendimento%' "
        "  OR m.msgs_content LIKE '%Qual o motivo do contato%' "
        "  OR m.msgs_content LIKE '%Selecione o departamento%'"
        ") "
        "AND ("
        "  cv.cnvs_rating_nps IS NULL "
        "  OR cv.cnvs_rating_agent IS NULL "
        "  OR cv.cnvs_contact_reason IS NULL "
        "  OR cv.cnvs_dept IS NULL"
        ") "
        "ORDER BY cv.cnvs_id"
    )
    total = len(rows)
    logger.info("Survey backfill: %d conversations to process...", total)
    for i, row in enumerate(rows):
        await update_conversation_surveys(manager, conn, row["cnvs_bird"])
        if (i + 1) % 200 == 0:
            logger.info("  ...%d/%d conversations processed", i + 1, total)
    logger.info("Survey backfill completed: %d conversations processed.", total)
    return total
