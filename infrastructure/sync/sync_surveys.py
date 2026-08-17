import logging
import re
from datetime import datetime, timedelta
from typing import Any

from infrastructure.api import config
from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_core import PgSyncManager

logger = logging.getLogger("m_bird.sync_pg")


async def update_conversation_surveys(
    manager: PgSyncManager,
    conn: PostgresSyncConnection,
    conversation_bird_id: str,
    raw_messages: list[dict[str, Any]] | None = None,
) -> None:
    """Update survey data for a conversation.

    If raw_messages is provided, use it directly instead of re-fetching from DB.
    """
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

    if raw_messages is not None:
        # Convert API raw messages to the format expected by the survey processor
        messages = []
        for rm in raw_messages:
            content_obj = rm.get("content")
            content_text = ""
            if isinstance(content_obj, dict):
                content_text = content_obj.get("text", "") or content_obj.get("hsm", {}).get("elementName", "")
            else:
                content_text = str(content_obj) if content_obj else ""
            messages.append(
                {
                    "msgs_id": rm.get("id"),
                    "msgs_content": content_text,
                    "msgs_direction": rm.get("direction"),
                    "msgs_created": rm.get("createdDatetime"),
                }
            )
    else:
        # Fallback: fetch from DB (used by backfill_surveys)
        messages = await conn.fetch_all(
            "SELECT msgs_id, msgs_content, msgs_direction, msgs_created "
            "FROM messages WHERE msgs_cnvs = $1 ORDER BY msgs_created ASC",
            (cnvs_id,),
        )

    # Normalize timestamps and sort chronologically. The Bird API can return
    # messages in a different order than the actual conversation flow; pairing
    # questions with answers only works with a strict chronological order.
    def _to_datetime(value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except TypeError, ValueError:
            return None

    typed_messages: list[dict[str, Any]] = []
    for row in messages:
        ts = _to_datetime(row["msgs_created"])
        if ts is None:
            continue
        typed_messages.append(
            {
                "msgs_content": row["msgs_content"] or "",
                "msgs_direction": row["msgs_direction"],
                "msgs_created": ts,
            }
        )
    typed_messages.sort(key=lambda row: row["msgs_created"])
    messages = typed_messages

    updates: dict[str, int | str | None] = {}
    missing_answers: dict[str, None] = {}
    question_patterns = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in questions.values()]
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
            found_answer = False
            for j in range(i + 1, min(i + 10, len(messages))):
                next_msg = messages[j]
                next_ts = next_msg["msgs_created"]
                if next_ts - timestamp > timedelta(minutes=60):
                    break
                if next_msg["msgs_direction"] != "received":
                    # The answer must come before the next question of the flow;
                    # otherwise an answer for a later question could be captured.
                    nxt_content = next_msg["msgs_content"]
                    if nxt_content and any(pat.search(nxt_content) for pat in question_patterns):
                        break
                    continue
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
                            updates["cnvs_lang"] = str(num)
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
                    found_answer = True
                    break
            if not found_answer:
                missing_answers[matched_key] = None

    # Infer missing contact_reason from dept + occurrence (reverse lookup via OCCURRENCE_MAP)
    if "cnvs_dept" in updates and "cnvs_occurrence" in updates and "cnvs_contact_reason" not in updates:
        dept = updates["cnvs_dept"]
        occ = updates["cnvs_occurrence"]
        for reason_id, reason_occs in constants.OCCURRENCE_MAP.get(dept, {}).items():
            if occ in reason_occs:
                updates["cnvs_contact_reason"] = reason_id
                break

    # Questions asked without a usable answer must be reset to NULL, so stale
    # values from previous (mis-ordered) parses are healed on re-runs.
    question_columns = {
        "lang": "cnvs_lang",
        "software": "cnvs_software",
        "tax_id": "cnvs_tax_id",
        "dept": "cnvs_dept",
        "contact_reason": "cnvs_contact_reason",
        "occurrence": "cnvs_occurrence",
        "rating_agent": "cnvs_rating_agent",
        "rating_nps": "cnvs_rating_nps",
    }
    for key in missing_answers:
        updates.setdefault(question_columns[key], None)

    if updates:
        # Use parameterized query to prevent SQL injection
        set_parts = []
        params = []
        for idx, (k, v) in enumerate(updates.items(), 1):
            set_parts.append(f"{k} = ${idx}")
            params.append(v)
        params.append(cnvs_id)
        set_clause = ", ".join(set_parts)
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
        "  OR m.msgs_content LIKE '%Qual o motivo del contato%' "
        "  OR m.msgs_content LIKE '%Qual a sua dúvida%' "
        "  OR m.msgs_content LIKE '%Selecione o departamento%'"
        ")"
    )
    total = len(rows)
    logger.info("Survey backfill: %d conversations to process...", total)
    for i, row in enumerate(rows):
        await update_conversation_surveys(manager, conn, row["cnvs_bird"])
        if (i + 1) % 200 == 0:
            logger.info("  ...%d/%d conversations processed", i + 1, total)
    logger.info("Survey backfill completed: %d conversations processed.", total)
    return total
