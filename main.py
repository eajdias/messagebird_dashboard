import argparse
import asyncio
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from application.use_cases.data_quality_report import DataQualityReportUseCase
from application.use_cases.generate_report import GenerateReportUseCase
from application.use_cases.sync_database import SyncDatabaseUseCase
from infrastructure.config.config_loader import load_and_configure_business, load_bsc_config
from infrastructure.database.connection import DatabaseConnection
from infrastructure.database.sqlite_repository import SqliteReportRepository
from infrastructure.exporters.excel_exporter import ExcelExporter

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    def _print_panel(msg, title="Info"):
        console.print(Panel(msg, title=title))
    def _print(msg, style=None):
        console.print(msg, style=style)
except ImportError:
    console = None
    def _print_panel(msg, title="Info"):
        print(f"=== {title} ===\n{msg}")
    def _print(msg, style=None):
        print(msg)

async def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Standalone Report & Sync Tool")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    report_parser = subparsers.add_parser("report", help="Gerar relatórios")
    report_parser.add_argument("--year", type=int, default=datetime.now().year, help="Ano do relatório")
    report_parser.add_argument("--month", type=int, default=None, help="Mês (1-12). Omitir para relatório anual.")
    report_parser.add_argument("--from-date", type=str, default=None, help="Data inicial (YYYY-MM-DD)")
    report_parser.add_argument("--to-date", type=str, default=None, help="Data final (YYYY-MM-DD)")
    report_parser.add_argument("--output-dir", default="reports", help="Pasta de saída")
    report_parser.add_argument("--db-path", default="m_bird.db", help="Caminho para o arquivo .db")
    report_parser.add_argument("--config-path", default="business_config.yaml", help="Caminho para business_config.yaml")
    report_parser.add_argument("--bsc-config-path", default="business_bsc.yaml", help="Caminho para business_bsc.yaml")
    report_parser.add_argument("--skip-os", action="store_true", help="Pular Ordens de Serviço")
    report_parser.add_argument("--sector", default=None, help="Filtrar por um setor/grupo específico")

    total_parser = subparsers.add_parser("total", help="Gerar relatório total do sistema")
    total_parser.add_argument("--output-dir", default="reports", help="Pasta de saída")
    total_parser.add_argument("--db-path", default="m_bird.db", help="Caminho para o arquivo .db")
    total_parser.add_argument("--config-path", default="business_config.yaml", help="Caminho para business_config.yaml")
    total_parser.add_argument("--bsc-config-path", default="business_bsc.yaml", help="Caminho para business_bsc.yaml")
    total_parser.add_argument("--skip-os", action="store_true", help="Pular Ordens de Serviço")
    total_parser.add_argument("--sector", default=None, help="Filtrar por um setor/grupo específico")

    sync_parser = subparsers.add_parser("sync", help="Sincronizar banco de dados")
    sync_parser.add_argument("--full", action="store_true", help="Sync estrutural completo")
    sync_parser.add_argument("--full-messages", action="store_true", help="Sync completo incluindo todas mensagens")
    sync_parser.add_argument("--messages-days", type=int, default=None, help="Sync de mensagens dos últimos N dias")
    sync_parser.add_argument("--lookback", type=int, default=60, help="Minutos de retrocesso para sync incremental")
    sync_parser.add_argument("--year", type=int, default=None, help="Ano para backfill mensal")
    sync_parser.add_argument("--month", type=int, default=None, help="Mês para backfill mensal")
    sync_parser.add_argument("--backfill-surveys", action="store_true", help="Re-extrair NPS e avaliações")
    sync_parser.add_argument("--db-path", default="m_bird.db", help="Caminho para o arquivo .db")

    quality_parser = subparsers.add_parser("quality", help="Gerar relatório de qualidade de dados")
    quality_parser.add_argument("--output-dir", default="reports", help="Pasta de saída")
    quality_parser.add_argument("--db-path", default="m_bird.db", help="Caminho para o arquivo .db")
    quality_parser.add_argument("--config-path", default="business_config.yaml", help="Caminho para business_config.yaml")
    quality_parser.add_argument("--from-date", type=str, default=None, help="Data inicial (YYYY-MM-DD)")
    quality_parser.add_argument("--to-date", type=str, default=None, help="Data final (YYYY-MM-DD)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "report":
        load_and_configure_business(args.config_path)
        load_bsc_config(args.bsc_config_path)

        db_conn = DatabaseConnection(args.db_path)
        repository = SqliteReportRepository(db_conn)
        exporter = ExcelExporter()
        use_case = GenerateReportUseCase(repository, exporter)

        has_from = args.from_date is not None
        has_to = args.to_date is not None
        if has_from or has_to:
            if not has_from or not has_to:
                _print("[bold red]ERRO:[/] Use --from-date e --to-date juntos.")
                return
            report_type = "custom_range"
            period_label = f"{args.from_date} a {args.to_date}"
        elif args.month:
            report_type = "monthly"
            period_label = f"{args.year}-{args.month:02d}"
        else:
            report_type = "annual"
            period_label = str(args.year)

        _print_panel(
            f"Iniciando Geração de Relatório Standalone\n"
            f"Período: {period_label}\n"
            f"Setor: {args.sector if args.sector else 'Todos'}\n"
            f"DB: {args.db_path}",
            title="Master Report"
        )

        result = await use_case.execute(
            args.year, args.month, args.output_dir, args.skip_os, args.sector,
            report_type=report_type,
            start_date=args.from_date,
            end_date=args.to_date,
        )

        if result:
            unmapped_agents, unmapped_depts = result["unmapped"]
            if unmapped_agents > 0 or unmapped_depts > 0:
                _print(f"[bold yellow]AVISO:[/] Existem {unmapped_agents} chats com agentes não mapeados e {unmapped_depts} sem departamento.")

        print(f"\nRelatórios gerados em: {args.output_dir}")

    elif args.command == "total":
        load_and_configure_business(args.config_path)
        load_bsc_config(args.bsc_config_path)

        db_conn = DatabaseConnection(args.db_path)
        repository = SqliteReportRepository(db_conn)
        exporter = ExcelExporter()
        use_case = GenerateReportUseCase(repository, exporter)

        _print_panel(
            f"Iniciando Relatório Total do Sistema\nDB: {args.db_path}",
            title="Master Report — Total"
        )

        result = await use_case.execute(
            year=None, month=None, output_dir=args.output_dir,
            skip_os=args.skip_os, sector=args.sector,
            report_type="total",
        )

        if result:
            unmapped_agents, unmapped_depts = result["unmapped"]
            if unmapped_agents > 0 or unmapped_depts > 0:
                _print(f"[bold yellow]AVISO:[/] Existem {unmapped_agents} chats com agentes não mapeados e {unmapped_depts} sem departamento.")

        print(f"\nRelatórios gerados em: {args.output_dir}")

    elif args.command == "sync":
        has_year = args.year is not None
        has_month = args.month is not None
        if has_year != has_month:
            _print("[bold red]ERRO:[/] Use --year e --month juntos para sincronização mensal.")
            return
        if has_year and (args.month < 1 or args.month > 12):
            _print("[bold red]ERRO:[/] Mês deve estar entre 1 e 12.")
            return
        _print_panel(
            f"Iniciando Sincronização do Banco de Dados\nDB: {args.db_path}",
            title="Database Sync"
        )
        use_case = SyncDatabaseUseCase()
        is_full = args.full or args.full_messages
        result = await use_case.execute(
            full_sync=is_full,
            sync_messages=args.full_messages,
            messages_days=args.messages_days,
            lookback_minutes=args.lookback,
            year=args.year,
            month=args.month,
            backfill_surveys=args.backfill_surveys,
            db_path=args.db_path
        )
        _print(f"[bold green]Resultado:[/] {result}")

    elif args.command == "quality":
        load_and_configure_business(args.config_path)

        db_conn = DatabaseConnection(args.db_path)
        repository = SqliteReportRepository(db_conn)
        exporter = ExcelExporter()
        use_case = DataQualityReportUseCase(repository, exporter)

        _print_panel(
            f"Gerando Relatório de Qualidade de Dados\nDB: {args.db_path}",
            title="Data Quality Report"
        )

        result = await use_case.execute(
            args.output_dir,
            start_date=args.from_date,
            end_date=args.to_date
        )

        if result:
            _print("[bold green]Relatório de qualidade de dados gerado com sucesso![/]")

if __name__ == "__main__":
    asyncio.run(main())
