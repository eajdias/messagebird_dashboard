from datetime import datetime
from typing import Any


class MarkdownExporter:
    def export_summary(self, filename: str, title: str, start_date: str, end_date: str, data: dict[str, Any], report_type: str = "monthly"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Período:** {start_date} a {end_date}  \n")
            f.write(f"**Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
            f.write("**Fonte:** Omnichannel MCP\n\n")
            f.write("---\n\n")

            # ── Resumo Executivo ──────────────────────────────────────────────
            f.write("## Resumo Executivo\n\n")
            agent_data = data.get("agent_data", [])
            totals = next((r for r in agent_data if r[2] == "TOTAIS"), None)
            if totals:
                f.write(
                    f"Neste período, foram realizados **{totals[3]} atendimentos**, "
                    f"com **{totals[9]} mensagens** enviadas pelos agentes.  \n"
                    f"O NPS Real médio foi de **{totals[13]}**, com ART de **{totals[14]} min** "
                    f"e conformidade de SLA de **{totals[15]}%**.\n\n"
                )

            # ── Indicadores Principais ────────────────────────────────────────
            f.write("### Indicadores\n\n")
            f.write("| Indicador | Valor |\n")
            f.write("| :-------- | :--- |\n")
            if totals:
                f.write(f"| Total de Chats | {totals[3]} |\n")
                f.write(f"| NPS Real | {totals[13]} |\n")
                f.write(f"| ART Médio | {totals[14]} min |\n")
                f.write(f"| SLA Compliance | {totals[15]}% |\n")
                f.write(f"| Duração Média | {totals[16]} min |\n")
            f.write("\n")

            if report_type in ("annual", "total"):
                monthly_evolution = data.get("monthly_evolution", [])
                if monthly_evolution:
                    f.write("## Evolução Mensal\n\n")
                    f.write("| Mês | Chats | NPS | ART (min) | SLA % |\n")
                    f.write("| :--- | :--- | :--- | :--- | :--- |\n")
                    for entry in monthly_evolution:
                        m = entry.get("month", "")
                        chats = entry.get("total_chats", "N/A")
                        nps = entry.get("real_nps", "N/A")
                        art = entry.get("avg_art", "N/A")
                        sla = entry.get("sla_compliance", "N/A")
                        f.write(f"| {m} | {chats} | {nps} | {art} | {sla} |\n")
                    f.write("\n")

            # ── Performance por Grupo ─────────────────────────────────────────
            group_data = data.get("group_data", [])
            if group_data:
                f.write("## Performance por Grupo\n\n")
                f.write("| Grupo | Chats | Msgs | ART Médio | SLA | NPS Real |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
                for row in group_data:
                    if row[0] == "TOTAIS":
                        continue
                    name = str(row[0]).replace("|", "\\|")
                    f.write(f"| {name} | {row[1]} | {row[2]} | {row[3]} min | {row[4]}% | {row[7]} |\n")
                f.write("\n")

            # ── Top Agentes ───────────────────────────────────────────────────
            if agent_data:
                f.write("## Top Agentes\n\n")
                f.write("| # | Agente | Grupo | Chats | NPS Real | ART | SLA |\n")
                f.write("| :-: | :--- | :--- | :--- | :--- | :--- | :--- |\n")

                sorted_agents = sorted(
                    [r for r in agent_data if r[2] != "TOTAIS"],
                    key=lambda r: r[13] if isinstance(r[13], (int, float)) else 0,
                    reverse=True
                )
                for idx, row in enumerate(sorted_agents[:10]):
                    name = str(row[2]).replace("|", "\\|")
                    group = str(row[1]).replace("|", "\\|")
                    f.write(f"| {idx+1} | {name} | {group} | {row[3]} | {row[13]} | {row[14]} min | {row[15]}% |\n")

                f.write("\n")

            # ── Arquivos Gerados ──────────────────────────────────────────────
            f.write("## Arquivos Gerados\n\n")
            if report_type == "annual":
                f.write("- `Dashboard_Executivo_ANUAL_*.xlsx`: Dashboard anual consolidado com abas de evolução mensal.\n")
            elif report_type == "total":
                f.write("- `Dashboard_Executivo_TOTAL_SISTEMA.xlsx`: Dashboard total do sistema com todo o histórico.\n")
            else:
                f.write("- `Dashboard_Executivo_GLOBAL_*.xlsx`: Dashboard consolidado com todas as abas.\n")
            f.write("- Pastas por grupo: cada uma contém dashboard individual, auditoria de contatos e OS.\n")
            f.write("- `auditoria_contatos.xlsx`: Detalhamento de clientes com mais interações.\n")
            f.write("- `auditoria_os.xlsx`: Relatório completo de Ordens de Serviço.\n")
            f.write("- `OS/`: PDFs individuais de cada Ordem de Serviço.\n")
            if report_type == "total":
                f.write(f"\n*Período total dos dados: {start_date} a {end_date}*\n")
            f.write("\n")
            f.write("---\n")
            f.write(f"*Relatório gerado automaticamente pelo sistema Omnichannel MCP em {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n")
