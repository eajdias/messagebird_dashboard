import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from application.use_cases.sync_database import SyncDatabaseUseCase
from infrastructure.config.config_loader import load_and_configure_business, load_bsc_config

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

    parser = argparse.ArgumentParser(description="BD Sync Tool")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    sync_parser = subparsers.add_parser("sync", help="Sincronizar banco de dados (PostgreSQL)")
    sync_parser.add_argument("--full", action="store_true", help="Sync estrutural completo")
    sync_parser.add_argument("--full-messages", action="store_true", help="Sync completo incluindo todas mensagens")
    sync_parser.add_argument("--messages-days", type=int, default=None, help="Sync de mensagens dos últimos N dias")
    sync_parser.add_argument("--year", type=int, default=None, help="Ano para backfill mensal")
    sync_parser.add_argument("--month", type=int, default=None, help="Mês para backfill mensal")
    sync_parser.add_argument("--backfill-surveys", action="store_true", help="Re-extrair NPS e avaliações")
    sync_parser.add_argument("--config-path", default="business_config.yaml", help="Caminho para business_config.yaml")
    sync_parser.add_argument("--bsc-config-path", default="business_bsc.yaml", help="Caminho para business_bsc.yaml")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "sync":
        load_and_configure_business(args.config_path)
        load_bsc_config(args.bsc_config_path)

        has_year = args.year is not None
        has_month = args.month is not None
        if has_year != has_month:
            _print("[bold red]ERRO:[/] Use --year e --month juntos para sincronização mensal.")
            return
        if has_year and (args.month < 1 or args.month > 12):
            _print("[bold red]ERRO:[/] Mês deve estar entre 1 e 12.")
            return

        _print_panel("Iniciando Sincronização do Banco de Dados (PostgreSQL)", title="Database Sync")
        use_case = SyncDatabaseUseCase()
        is_full = args.full or args.full_messages
        result = await use_case.execute(
            full_sync=is_full,
            sync_messages=args.full_messages,
            messages_days=args.messages_days,
            year=args.year,
            month=args.month,
            backfill_surveys=args.backfill_surveys,
        )
        _print(f"[bold green]Resultado:[/] {result}")


if __name__ == "__main__":
    asyncio.run(main())
