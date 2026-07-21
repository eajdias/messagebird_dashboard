import os
import unittest

from domain import constants
from infrastructure.config.config_loader import load_and_configure_business


class TestResolveConversationGroup(unittest.TestCase):
    """Testes unitários para resolve_conversation_group com DEPT_ROUTING."""

    AGENTS_BACKUP: dict = {}
    DEPT_ROUTING_BACKUP: dict = {}
    DEPT_MAP_BACKUP: dict = {}

    @classmethod
    def setUpClass(cls):
        cls.AGENTS_BACKUP = constants.AGENTS.copy()
        cls.DEPT_ROUTING_BACKUP = constants.DEPT_ROUTING.copy()
        cls.DEPT_MAP_BACKUP = constants.DEPT_MAP.copy()

        # Load business config so DEPT_MAP has real values
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "business_config.yaml")
        if os.path.exists(config_path):
            load_and_configure_business(config_path)

        constants.AGENTS = {
            "id_1": {"name": "Alice Suporte", "group": "Suporte Técnico"},
            "id_2": {"name": "Bruno CS", "group": "CS | Instalação | Migração | Ouvidoria"},
            "id_3": {"name": "Carlos Vendas", "group": "Comercial"},
        }

    @classmethod
    def tearDownClass(cls):
        constants.AGENTS = cls.AGENTS_BACKUP
        constants.DEPT_ROUTING = cls.DEPT_ROUTING_BACKUP
        constants.DEPT_MAP = cls.DEPT_MAP_BACKUP

    def setUp(self):
        # começa cada teste com DEPT_ROUTING vazio
        constants.DEPT_ROUTING = {}

    # ── DEPT_ROUTING vazio (compatibilidade retroativa) ───────────────────

    def test_empty_routing_fallback_to_agent_group(self):
        """Sem DEPT_ROUTING, o grupo é sempre o do agente."""
        g = constants.resolve_conversation_group("Alice Suporte", "Ouvidoria")
        self.assertEqual(g, "Suporte Técnico")

    def test_empty_routing_with_na_dept(self):
        """Sem DEPT_ROUTING, N/A também usa o grupo do agente."""
        g = constants.resolve_conversation_group("Alice Suporte", "N/A")
        self.assertEqual(g, "Suporte Técnico")

    def test_empty_routing_unmapped_agent(self):
        """Agente desconhecido retorna OUTROS."""
        g = constants.resolve_conversation_group("Zeca Ninguém", "Suporte Técnico")
        self.assertEqual(g, "OUTROS")

    def test_empty_routing_none_agent(self):
        """Agent None retorna N/A com DEPT_ROUTING vazio."""
        g = constants.resolve_conversation_group(None, "Ouvidoria")
        self.assertEqual(g, "N/A")

    # ── DEPT_ROUTING populado ─────────────────────────────────────────────

    def test_routing_redirects_by_dept_label(self):
        """DEPT_ROUTING redireciona conversas para o grupo mapeado."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        g = constants.resolve_conversation_group("Alice Suporte", "Ouvidoria")
        self.assertEqual(g, "Ouvidoria")

    def test_routing_keeps_agent_group_for_unmapped_dept(self):
        """Departamento não mapeado em DEPT_ROUTING usa grupo do agente."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        g = constants.resolve_conversation_group("Alice Suporte", "Financeiro")
        self.assertEqual(g, "Suporte Técnico")

    def test_routing_multiple_depts(self):
        """Múltiplos departamentos mapeados corretamente."""
        constants.DEPT_ROUTING = {
            "Comercial": "Comercial",
            "Financeiro": "Financeiro",
        }
        g1 = constants.resolve_conversation_group("Alice Suporte", "Comercial")
        g2 = constants.resolve_conversation_group("Alice Suporte", "Financeiro")
        self.assertEqual(g1, "Comercial")
        self.assertEqual(g2, "Financeiro")

    def test_routing_na_dept_goes_to_sem_departamento(self):
        """Com DEPT_ROUTING ativo, N/A vai para 'Sem Departamento'."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        g = constants.resolve_conversation_group("Alice Suporte", "N/A")
        self.assertEqual(g, "Sem Departamento")

    def test_routing_none_dept_goes_to_sem_departamento(self):
        """Mesmo comportamento para None."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        g = constants.resolve_conversation_group("Alice Suporte", None)  # type: ignore
        self.assertEqual(g, "Sem Departamento")

    def test_routing_agent_none_with_known_dept(self):
        """Agent None mas departamento em DEPT_ROUTING → grupo do dept."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        g = constants.resolve_conversation_group(None, "Ouvidoria")
        self.assertEqual(g, "Ouvidoria")

    def test_routing_agent_none_with_na_dept(self):
        """Agent None e N/A → Sem Departamento."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        g = constants.resolve_conversation_group(None, "N/A")
        self.assertEqual(g, "Sem Departamento")

    def test_routing_maps_to_different_group_name(self):
        """DEPT_ROUTING pode mapear para um grupo com nome diferente."""
        constants.DEPT_ROUTING = {"Nova Instalação | Migração": "CS | Instalação | Migração | Ouvidoria"}
        g = constants.resolve_conversation_group("Alice Suporte", "Nova Instalação | Migração")
        self.assertEqual(g, "CS | Instalação | Migração | Ouvidoria")

    # ── DEPT_ROUTING ativo com agente de grupo diferente ──────────────────

    def test_routing_overrides_agent_group(self):
        """DEPT_ROUTING sobrepõe o grupo do agente."""
        constants.DEPT_ROUTING = {"Ouvidoria": "Ouvidoria"}
        # Agente do Suporte Técnico atende conversa de Ouvidoria
        g = constants.resolve_conversation_group("Alice Suporte", "Ouvidoria")
        self.assertEqual(g, "Ouvidoria")

    # ── resolve_dept (mantendo cobertura) ─────────────────────────────────

    def test_resolve_dept_known_int(self):
        self.assertEqual(constants.resolve_dept(1), constants.DEPT_MAP.get(1, "1"))

    def test_resolve_dept_unknown_int(self):
        self.assertEqual(constants.resolve_dept(99), "99")

    def test_resolve_dept_none(self):
        self.assertEqual(constants.resolve_dept(None), "N/A")


if __name__ == "__main__":
    unittest.main()
