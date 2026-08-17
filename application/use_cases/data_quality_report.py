import os
from datetime import datetime
from typing import Any

from application.interfaces.exporter import ReportExporter
from application.interfaces.repository import ReportRepository


class DataQualityReportUseCase:
    """Use case para gerar relatório de qualidade de dados do banco."""

    def __init__(self, repository: ReportRepository, exporter: ReportExporter):
        self.repository = repository
        self.exporter = exporter

    async def execute(self, output_dir: str, start_date: str | None = None, end_date: str | None = None):
        """Gera relatório de qualidade de dados."""
        # Buscar dados brutos
        if start_date and end_date:
            raw_data = await self.repository.fetch_raw_data_range(start_date, end_date)
            period_label = f"{start_date} a {end_date}"
        else:
            raw_data = await self.repository.fetch_raw_data_all()
            period_label = "Todo o histórico"

        if not raw_data:
            print("Warning: Nenhum dado encontrado.")
            return None

        # Analisar qualidade
        quality_data = self._analyze_quality(raw_data)

        # Gerar relatório
        report_subdir = os.path.join(output_dir, "qualidade_dados")
        os.makedirs(report_subdir, exist_ok=True)

        # Exportar Excel
        header = ["Métrica", "Total", "Válidos", "Inválidos/Ausentes", "% Qualidade", "Observação"]

        rows = []
        for metric in quality_data:
            rows.append(
                [
                    metric["name"],
                    metric["total"],
                    metric["valid"],
                    metric["invalid"],
                    f"{metric['quality_pct']:.1f}%",
                    metric["observation"],
                ]
            )

        self.exporter.export_excel(
            os.path.join(report_subdir, "qualidade_dados.xlsx"), header, rows, "Qualidade de Dados"
        )

        # Gerar README resumido
        self._export_summary(report_subdir, quality_data, period_label)

        print(f"Relatório de qualidade de dados gerado em: {report_subdir}")
        return quality_data

    def _analyze_quality(self, raw_data: list) -> list[dict[str, Any]]:
        """Analisa a qualidade dos dados."""
        total = len(raw_data)

        # Métricas de qualidade
        metrics = []

        # 1. Departamento preenchido
        valid_dept = sum(
            1 for r in raw_data if r.dept_label and r.dept_label not in ("N/A", "None", "", "Sem Departamento")
        )
        metrics.append(
            {
                "name": "Departamento Preenchido",
                "total": total,
                "valid": valid_dept,
                "invalid": total - valid_dept,
                "quality_pct": (valid_dept / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_dept} conversas sem departamento",
            }
        )

        # 2. Agente preenchido (via metadata)
        valid_agent = sum(
            1
            for r in raw_data
            if r.metadata.get("agent_name") and r.metadata.get("agent_name") not in ("N/A", "None", "", "OUTROS")
        )
        metrics.append(
            {
                "name": "Agente Preenchido",
                "total": total,
                "valid": valid_agent,
                "invalid": total - valid_agent,
                "quality_pct": (valid_agent / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_agent} conversas sem agente",
            }
        )

        # 3. Avaliação do agente
        valid_rating = sum(1 for r in raw_data if r.rating is not None)
        metrics.append(
            {
                "name": "Avaliação do Agente",
                "total": total,
                "valid": valid_rating,
                "invalid": total - valid_rating,
                "quality_pct": (valid_rating / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_rating} conversas sem avaliação",
            }
        )

        # 4. NPS preenchido
        valid_nps = sum(1 for r in raw_data if r.nps is not None)
        metrics.append(
            {
                "name": "NPS",
                "total": total,
                "valid": valid_nps,
                "invalid": total - valid_nps,
                "quality_pct": (valid_nps / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_nps} conversas sem NPS",
            }
        )

        # 5. Motivo do contato
        valid_reason = sum(1 for r in raw_data if r.contact_reason and r.contact_reason != "N/A")
        metrics.append(
            {
                "name": "Motivo do Contato",
                "total": total,
                "valid": valid_reason,
                "invalid": total - valid_reason,
                "quality_pct": (valid_reason / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_reason} conversas sem motivo",
            }
        )

        # 6. Ocorrência
        valid_occurrence = sum(1 for r in raw_data if r.occurrence and r.occurrence != "N/A")
        metrics.append(
            {
                "name": "Ocorrência",
                "total": total,
                "valid": valid_occurrence,
                "invalid": total - valid_occurrence,
                "quality_pct": (valid_occurrence / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_occurrence} conversas sem ocorrência",
            }
        )

        # 7. Software
        valid_software = sum(
            1 for r in raw_data if r.metadata.get("software") and r.metadata.get("software") != "UNKNOWN"
        )
        metrics.append(
            {
                "name": "Software",
                "total": total,
                "valid": valid_software,
                "invalid": total - valid_software,
                "quality_pct": (valid_software / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_software} conversas com software desconhecido",
            }
        )

        # 8. Canal preenchido
        valid_channel = sum(
            1 for r in raw_data if r.metadata.get("channel_name") and r.metadata.get("channel_name") != "Desconhecido"
        )
        metrics.append(
            {
                "name": "Canal",
                "total": total,
                "valid": valid_channel,
                "invalid": total - valid_channel,
                "quality_pct": (valid_channel / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_channel} conversas sem canal mapeado",
            }
        )

        # 9. Descrição do problema
        valid_description = sum(
            1 for r in raw_data if r.metadata.get("description") and str(r.metadata.get("description")).strip()
        )
        metrics.append(
            {
                "name": "Descrição do Problema",
                "total": total,
                "valid": valid_description,
                "invalid": total - valid_description,
                "quality_pct": (valid_description / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_description} conversas sem descrição",
            }
        )

        # 10. Telefone do cliente
        valid_phone = sum(1 for r in raw_data if r.phone and r.phone.strip())
        metrics.append(
            {
                "name": "Telefone do Cliente",
                "total": total,
                "valid": valid_phone,
                "invalid": total - valid_phone,
                "quality_pct": (valid_phone / total * 100) if total > 0 else 0,
                "observation": f"{total - valid_phone} conversas sem telefone",
            }
        )

        return metrics

    def _export_summary(self, report_dir: str, quality_data: list[dict], period_label: str):
        """Exporta README resumido."""
        readme_path = os.path.join(report_dir, "README.md")

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# Relatório de Qualidade de Dados\n\n")
            f.write(f"**Período:** {period_label}\n")
            f.write(f"**Data de Geração:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("## Resumo\n\n")
            f.write("| Métrica | % Qualidade | Observação |\n")
            f.write("|---------|-------------|------------|\n")

            for metric in quality_data:
                f.write(f"| {metric['name']} | {metric['quality_pct']:.1f}% | {metric['observation']} |\n")

            f.write("\n## Arquivos Gerados\n\n")
            f.write("- `qualidade_dados.xlsx`: Planilha detalhada com todas as métricas\n")
            f.write("- `README.md`: Este resumo\n")
