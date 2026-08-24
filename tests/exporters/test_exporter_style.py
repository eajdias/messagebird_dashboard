import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from domain.constants import AGENTS_HEADER, DEPARTMENTS_HEADER, KPI_CONFIG
from infrastructure.config.config_loader import load_and_configure_business, load_bsc_config
from infrastructure.exporters._bsc_writer import (
    _kpi_excel_formula,
)
from infrastructure.exporters.excel_exporter import (
    COLOR_ACCENT,
    COLOR_ALERT,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SURFACE,
    COLOR_TEXT_LIGHT,
    COLOR_WARNING,
    ExcelExporter,
    auto_width,
)


class TestExporterStyle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "business_config.yaml")
        bsc_path = os.path.join(os.path.dirname(__file__), "..", "..", "business_bsc.yaml")
        if os.path.exists(config_path):
            load_and_configure_business(config_path)
        if os.path.exists(bsc_path):
            load_bsc_config(bsc_path)

    def setUp(self):
        self.exporter = ExcelExporter()

    def test_palette_has_all_required_colors(self):
        self.assertTrue(COLOR_PRIMARY.startswith("#"))
        self.assertTrue(COLOR_SECONDARY.startswith("#"))
        self.assertTrue(COLOR_ACCENT.startswith("#"))
        self.assertTrue(COLOR_ALERT.startswith("#"))
        self.assertTrue(COLOR_WARNING.startswith("#"))
        self.assertTrue(COLOR_SURFACE.startswith("#"))
        self.assertTrue(COLOR_TEXT_LIGHT.startswith("#"))

    def test_agent_header_has_correct_columns(self):
        expected_headers = [
            "Dept maior atendimento",
            "Grupo",
            "Nome do Agente",
            "Total de Chats",
            "% do Departamento",
        ]
        for h in expected_headers:
            self.assertIn(h, AGENTS_HEADER)

    def test_department_header_has_correct_columns(self):
        self.assertIn("Departamento", DEPARTMENTS_HEADER)
        self.assertIn("Total de Chats", DEPARTMENTS_HEADER)
        self.assertIn("SLA Compliance (%)", DEPARTMENTS_HEADER)

    def test_kpi_config_has_penalidades_setoriais(self):
        penalidades = KPI_CONFIG.get("Suporte Tecnico", {}).get("penalidades_setoriais", [])
        self.assertGreater(len(penalidades), 0)
        self.assertIn("Liga", penalidades[0]["name"])

    def test_bsc_escalonado_percentual_formula(self):
        kpi = {
            "tipo": "escalonado_percentual",
            "meta": ">40%",
            "peso": 30,
            "niveis": [{"min": 40, "pts": 30, "extra_per_unit": 0.75}, {"min": 35, "pts": 15}, {"min": 30, "pts": 10}],
            "cap": 60,
        }
        formula = _kpi_excel_formula("A1", kpi)
        self.assertTrue(formula.startswith("=IF"))
        self.assertIn("A1", formula)
        self.assertIn("40", formula)
        self.assertIn("60", formula)

    def test_bsc_escalonado_nps_formula(self):
        kpi = {
            "tipo": "escalonado_nps",
            "meta": ">=70/63/50",
            "peso": 30,
            "niveis": [{"min": 70, "pts": 30}, {"min": 63, "pts": 15}, {"min": 50, "pts": 5}],
        }
        formula = _kpi_excel_formula("B2", kpi)
        self.assertTrue(formula.startswith("=IF"))
        self.assertIn("B2", formula)
        self.assertIn("70", formula)

    def test_bsc_penalidade_taxa_formula(self):
        kpi = {"tipo": "penalidade_taxa", "peso": -5, "threshold": 10, "extra_peso": -1, "cap": None}
        formula = _kpi_excel_formula("C3", kpi)
        self.assertTrue(formula.startswith("=IF"))
        self.assertIn("C3", formula)

    def test_bsc_sim_nao_assiduidade_formula(self):
        kpi = {"tipo": "sim_nao_assiduidade", "meta": 0, "peso": 35}
        formula = _kpi_excel_formula("D4", kpi)
        self.assertIn("D4", formula)
        self.assertIn("35", formula)

    def test_auto_width_no_error(self):
        import tempfile

        from xlsxwriter import Workbook

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test.xlsx")
            wb = Workbook(filename)
            ws = wb.add_worksheet()
            header = ["Name", "Value"]
            data = [["Alice", 100], ["Bob", 200]]
            auto_width(ws, header, data)
            wb.close()

    def test_tab_names_no_special_chars(self):
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwXYZ0123456789 _-çãáàâéêíóôúü")
        safe_names = ["Visão Geral", "BSC", "Desempenho Agentes", "Qualidade", "Demanda", "_data"]
        for name in safe_names:
            for c in name:
                self.assertIn(c, allowed, f"Character '{c}' not allowed in tab name '{name}'")

    def test_metadata_exists_in_dto(self):
        from application.interfaces.exporter import DashboardDTO

        self.assertTrue(hasattr(DashboardDTO, "prev_month_metrics"))
        self.assertTrue(hasattr(DashboardDTO, "tabular_header"))
        self.assertTrue(hasattr(DashboardDTO, "bsc_kpi_config"))

    def test_bsc_config_no_old_jira_references(self):
        t1 = KPI_CONFIG.get("Suporte Tecnico", {}).get("t1", [])
        t2 = KPI_CONFIG.get("Suporte Tecnico", {}).get("t2", [])
        all_names = [m["name"] for m in t1 + t2]
        for name in all_names:
            self.assertNotIn("JIRA", name, f"Found old JIRA reference: {name}")
        self.assertNotIn("Contribuição para base Conhecimento", [m["name"] for m in t1])

    def test_nps_threshold_updated(self):
        t1 = KPI_CONFIG.get("Suporte Tecnico", {}).get("t1", [])
        nps = next(m for m in t1 if "NPS" in m["name"])
        niveis = nps.get("niveis", [])
        self.assertEqual(niveis[-1]["min"], 50)

    def test_atendimentos_peso_updated(self):
        t1 = KPI_CONFIG.get("Suporte Tecnico", {}).get("t1", [])
        atd = next(m for m in t1 if "Atendimentos" in m["name"])
        self.assertEqual(atd["peso"], 10)


if __name__ == "__main__":
    unittest.main()
