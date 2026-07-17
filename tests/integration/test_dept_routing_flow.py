import unittest

from application.services.report_aggregator import ReportAggregator
from domain import constants
from domain.entities.report_data import RawConversationData, RawMessageData
from domain.metrics.art import ARTCalculator
from domain.metrics.duration import DurationCalculator
from domain.metrics.frt import FRTCalculator


class TestDeptRoutingFlow(unittest.TestCase):
    """Testes de integração do fluxo DEPT_ROUTING no ReportAggregator."""

    AGENTS_BACKUP: dict = {}
    DEPT_ROUTING_BACKUP: dict = {}

    @classmethod
    def setUpClass(cls):
        cls.AGENTS_BACKUP = constants.AGENTS.copy()
        cls.DEPT_ROUTING_BACKUP = constants.DEPT_ROUTING.copy()

        constants.AGENTS = {
            "id_1": {"name": "Alice Suporte", "group": "Suporte Técnico"},
            "id_2": {"name": "Bruno CS",     "group": "CS | Instalação | Migração | Ouvidoria"},
            "id_3": {"name": "Carlos Vendas", "group": "Comercial"},
        }

    @classmethod
    def tearDownClass(cls):
        constants.AGENTS = cls.AGENTS_BACKUP
        constants.DEPT_ROUTING = cls.DEPT_ROUTING_BACKUP

    def setUp(self):
        constants.DEPT_ROUTING = {}
        self.aggregator = ReportAggregator(strategies=[
            FRTCalculator(), DurationCalculator(), ARTCalculator(),
        ])

    # ── helpers ───────────────────────────────────────────────────────────

    def _conv(self, cid: str, agent: str, dept_label: str = "Suporte Técnico",
              rating: int = None) -> RawConversationData:
        return RawConversationData(
            id=cid,
            contact="Cliente Teste",
            phone="5511999999999",
            start_time="2026-06-01 10:00:00",
            end_time="2026-06-01 10:30:00",
            raw_created="2026-06-01 10:00:00",
            raw_updated="2026-06-01 10:30:00",
            msgs=[
                RawMessageData("2026-06-01 10:00:00", "received", None, agent),
                RawMessageData("2026-06-01 10:05:00", "sent", "1", agent),
            ],
            metadata={"agent_name": agent},
            rating=rating,
            dept_label=dept_label,
        )

    # ── _build_groups_rows ───────────────────────────────────────────────

    def test_groups_rows_without_dept_routing(self):
        """Sem DEPT_ROUTING, grupos são definidos pelo agente."""
        data = [
            self._conv("1", "Alice Suporte", "Ouvidoria"),
            self._conv("2", "Alice Suporte", "Suporte Técnico"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="groups")
        groups = [r[0] for r in rows]
        # Alice está em "Suporte Técnico", então ambas as conversas vão para lá
        self.assertIn("Suporte Técnico", groups)
        suporte_row = [r for r in rows if r[0] == "Suporte Técnico"][0]
        self.assertEqual(suporte_row[1], 2)

    def test_groups_rows_with_dept_routing(self):
        """Com DEPT_ROUTING, conversas de Ouvidoria vão para grupo Ouvidoria."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        data = [
            self._conv("1", "Alice Suporte", "Ouvidoria"),
            self._conv("2", "Alice Suporte", "Suporte Técnico"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="groups")
        groups = {r[0]: r[1] for r in rows}  # group -> total_chats
        # Conversa de Ouvidoria deve estar em "Ouvidoria"
        self.assertIn("Ouvidoria", groups)
        self.assertEqual(groups["Ouvidoria"], 1)
        # Conversa de Suporte Técnico continua em "Suporte Técnico"
        self.assertIn("Suporte Técnico", groups)
        self.assertEqual(groups["Suporte Técnico"], 1)

    def test_groups_rows_dept_routing_all_same_dept(self):
        """Todas as conversas de Ouvidoria vão para o mesmo grupo."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        data = [
            self._conv("1", "Alice Suporte", "Ouvidoria"),
            self._conv("2", "Bruno CS", "Ouvidoria"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="groups")
        groups = {r[0]: r[1] for r in rows}
        self.assertEqual(groups.get("Ouvidoria"), 2)

    def test_groups_rows_partial_routing(self):
        """Só departamentos em DEPT_ROUTING são redirecionados."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        data = [
            self._conv("1", "Alice Suporte", "Ouvidoria"),
            self._conv("2", "Alice Suporte", "Financeiro"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="groups")
        groups = {r[0]: r[1] for r in rows}
        # Financeiro não está em DEPT_ROUTING → cai no grupo do agente
        self.assertIn("Suporte Técnico", groups)
        self.assertEqual(groups["Suporte Técnico"], 1)
        self.assertIn("Ouvidoria", groups)
        self.assertEqual(groups["Ouvidoria"], 1)

    def test_groups_rows_routing_to_different_group_name(self):
        """DEPT_ROUTING pode redirecionar para grupo com nome diferente do dept."""
        constants.DEPT_ROUTING = {
            "Nova Instalação | Migração": "CS | Instalação | Migração | Ouvidoria",
        }
        data = [
            self._conv("1", "Alice Suporte", "Nova Instalação | Migração"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="groups")
        groups = [r[0] for r in rows]
        self.assertIn("CS | Instalação | Migração | Ouvidoria", groups)
        self.assertNotIn("Suporte Técnico", groups)

    def test_groups_rows_na_dept_with_routing_active(self):
        """Com DEPT_ROUTING ativo, N/A vai para 'Sem Departamento'."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        data = [
            self._conv("1", "Alice Suporte", "N/A"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="groups")
        groups = [r[0] for r in rows]
        self.assertIn("Sem Departamento", groups)

    # ── _build_agents_rows ────────────────────────────────────────────────

    def test_agents_rows_group_column_reflects_dept_routing(self):
        """A coluna 'Grupo' no relatório de agentes reflete o DEPT_ROUTING."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        data = [
            self._conv("1", "Alice Suporte", "Ouvidoria"),
            self._conv("2", "Alice Suporte", "Ouvidoria"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="agents")
        # rows[0] = TOTAIS, rows[1] = Alice Suporte
        self.assertEqual(len(rows), 2)
        group_col = rows[1][1]  # AGENTS_HEADER index 1 = "Grupo"
        self.assertEqual(group_col, "Ouvidoria")

    def test_agents_rows_group_agent_default_without_routing(self):
        """Sem DEPT_ROUTING, grupo do agente é o padrão."""
        data = [
            self._conv("1", "Alice Suporte", "Ouvidoria"),
        ]
        processed = self.aggregator.process_all(data)
        rows = self.aggregator.build_excel_rows(processed, report_type="agents")
        group_col = rows[1][1]
        self.assertEqual(group_col, "Suporte Técnico")

    # ── ───────────────────────────────────────────────────────────────────

    def test_dashboard_general_metrics_unchanged(self):
        """Métricas gerais não são afetadas pelo DEPT_ROUTING."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        data = [
            self._conv("1", "Alice Suporte", "Ouvidoria", rating=5),
            self._conv("2", "Alice Suporte", "Suporte Técnico", rating=3),
        ]
        processed = self.aggregator.process_all(data)
        stats = self.aggregator.aggregate_statistics(processed)
        self.assertEqual(stats["total_chats"], 2)


if __name__ == "__main__":
    unittest.main()
