import logging
import os
from typing import Any

from fpdf import FPDF
from rich.console import Console

logger = logging.getLogger("m_bird.exporter.pdf")
console = Console()

_HEADER_COLOR = (26, 58, 92)  # Dark Blue MessageBird style
_SECTION_COLOR = (235, 240, 245)  # Very light blue for section headers
_LABEL_COLOR = (245, 245, 245)  # Light gray for labels
_BRAND_COLOR = (0, 102, 204)  # Primary Brand Blue
_SUCCESS_COLOR = (34, 139, 34)  # Green for promoters
_DANGER_COLOR = (220, 53, 69)  # Red for detractors/complaints
_DANGER_BG = (255, 230, 230)  # Light red background

# Chat history colors
_CLIENT_BG = (230, 240, 250)  # Light blue for client messages
_AGENT_BG = (240, 240, 240)  # Light gray for agent messages
_CLIENT_TEXT = (26, 58, 92)  # Dark blue for client text
_AGENT_TEXT = (80, 80, 80)  # Dark gray for agent text


def _sanitize(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    # Remove all non-Latin-1 characters (including emojis)
    result = []
    for char in text:
        try:
            char.encode("latin-1")
            result.append(char)
        except UnicodeEncodeError:
            pass
    return "".join(result)


class _OSPDF(FPDF):
    def header(self):
        self.set_fill_color(*_HEADER_COLOR)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 12, " ORDEM DE SERVIÇO - ASSISTÊNCIA TÉCNICA", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0, 0, 0)

    def _section(self, title: str):
        self.set_fill_color(*_SECTION_COLOR)
        self.set_text_color(*_HEADER_COLOR)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"  {_sanitize(title).upper()}", fill=True, border="B", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def _row(self, label: str, value: str, label_w: float = 45, val_color=None, bg_color=None):
        self.set_fill_color(*_LABEL_COLOR)
        self.set_font("Helvetica", "B", 9)
        self.cell(label_w, 7, f" {_sanitize(label)}", fill=True, border="B")

        self.set_font("Helvetica", "", 9)
        if val_color:
            self.set_text_color(*val_color)
        if bg_color:
            self.set_fill_color(*bg_color)

        fill = bool(bg_color)
        self.multi_cell(
            self.epw - label_w, 7, f" {_sanitize(value)}", border="B", fill=fill, new_x="LMARGIN", new_y="NEXT"
        )
        self.set_text_color(0, 0, 0)

    def _two_cols(self, l1: str, v1: str, l2: str, v2: str, label_w: float = 45, v1_color=None, v2_color=None):
        half = self.epw / 2

        # Col 1
        self.set_fill_color(*_LABEL_COLOR)
        self.set_font("Helvetica", "B", 9)
        self.cell(label_w, 7, f" {_sanitize(l1)}", fill=True, border="B")

        self.set_font("Helvetica", "", 9)
        if v1_color:
            self.set_text_color(*v1_color)
        self.cell(half - label_w, 7, f" {_sanitize(v1)}", border="B")
        self.set_text_color(0, 0, 0)

        # Col 2
        self.set_fill_color(*_LABEL_COLOR)
        self.set_font("Helvetica", "B", 9)
        self.cell(label_w, 7, f" {_sanitize(l2)}", fill=True, border="B")

        self.set_font("Helvetica", "", 9)
        if v2_color:
            self.set_text_color(*v2_color)
        self.cell(
            self.epw - 2 * label_w - (half - label_w), 7, f" {_sanitize(v2)}", border="B", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_text_color(0, 0, 0)

    def _protocol_header(self, protocolo: str):
        self.set_fill_color(*_BRAND_COLOR)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(40, 8, " ID DA OS: ", fill=True)

        self.set_fill_color(240, 248, 255)  # Light brand blue
        self.set_text_color(*_HEADER_COLOR)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, f"  {_sanitize(protocolo)}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def _chat_history_header(self, protocolo: str, client_name: str, phone: str):
        self.set_fill_color(*_HEADER_COLOR)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, " HISTÓRICO DE MENSAGENS", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

        # Client info bar
        self.set_fill_color(*_SECTION_COLOR)
        self.set_font("Helvetica", "B", 9)
        self.cell(25, 7, " OS:", fill=True, border="B")
        self.set_font("Helvetica", "", 9)
        self.cell(50, 7, f" {_sanitize(protocolo)}", border="B")

        self.set_fill_color(*_LABEL_COLOR)
        self.set_font("Helvetica", "B", 9)
        self.cell(25, 7, " Cliente:", fill=True, border="B")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 7, f" {_sanitize(client_name)}", border="B", new_x="LMARGIN", new_y="NEXT")

        self.set_fill_color(*_SECTION_COLOR)
        self.set_font("Helvetica", "B", 9)
        self.cell(25, 7, " Telefone:", fill=True, border="B")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 7, f" {_sanitize(phone)}", border="B", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def _chat_message(self, sender: str, content: str, timestamp: str, is_client: bool = True):
        # Calculate available width
        margin = 15
        max_width = self.epw - 2 * margin

        # Sender and timestamp line
        self.set_font("Helvetica", "B", 8)
        if is_client:
            self.set_text_color(*_CLIENT_TEXT)
            label = f"[CLIENTE] {sender}"
        else:
            self.set_text_color(*_AGENT_TEXT)
            label = f"[AGENTE] {sender}"

        time_label = timestamp
        self.cell(0, 5, f"{_sanitize(label)}  |  {_sanitize(time_label)}", new_x="LMARGIN", new_y="NEXT")

        # Message bubble
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)

        if is_client:
            self.set_fill_color(*_CLIENT_BG)
        else:
            self.set_fill_color(*_AGENT_BG)

        # Calculate message height
        lines = self.multi_cell(max_width - 10, 5, _sanitize(content), dry_run=True, output="LINES")
        msg_height = len(lines) * 5 + 4

        # Check if we need a new page
        if self.get_y() + msg_height > self.h - 20:
            self.add_page()

        # Draw message bubble
        self.get_y()
        self.set_x(margin + 5)
        self.multi_cell(max_width - 10, 5, _sanitize(content), fill=True, border="B", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


class PDFExporter:
    def export_os_pdfs(
        self,
        output_dir: str,
        header: list[str],
        data: list[list[Any]],
        messages_dict: dict[int, list[dict[str, Any]]] = None,
    ):
        os.makedirs(output_dir, exist_ok=True)
        generated = 0

        def _val(v):
            v = str(v).strip()
            if not v or v.lower() in ("none", "nan", "n/d", ""):
                return "N/A"
            return v

        for row in data:
            try:
                protocolo = str(row[0])
                if not protocolo:
                    continue

                pdf_path = os.path.join(output_dir, f"OS_{protocolo}.pdf")

                pdf = _OSPDF(orientation="P", unit="mm", format="A4")
                pdf.alias_nb_pages()
                pdf.set_margins(15, 15, 15)
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()

                # 1. Protocolo Destacado
                pdf._protocol_header(protocolo)

                # 2. Dados do Cliente
                pdf._section("Dados do Cliente")
                pdf._row("Cliente:", _val(row[3]))
                pdf._row("Telefone:", _val(row[4]))
                # Documento is row[5] (cnvs_tax_id), ID BD is row[15] (cnvs_id)
                pdf._two_cols("Documento:", _val(row[5]), "ID BD:", _val(row[15]))
                pdf.ln(4)

                # 3. Equipamento ou Sistema
                pdf._section("Equipamento / Sistema")
                sistema = _val(row[6])
                # Redundancy fix: if we only have one field for system/product,
                # keep product as N/A to avoid repeating the same value.
                produto = "N/A"
                pdf._two_cols("Sistema:", sistema, "Produto:", produto)
                pdf.ln(4)

                # 4. Detalhamento dos Defeitos
                pdf._section("Detalhamento do Atendimento")
                pdf._two_cols("Motivo:", _val(row[8]), "Ocorrência:", _val(row[9]))

                desc = str(row[13])
                if not desc.strip():
                    desc = "Sem descrição detalhada."
                if len(desc) > 800:
                    desc = desc[:797] + "..."

                pdf.set_font("Helvetica", "B", 9)
                pdf.set_fill_color(*_LABEL_COLOR)
                pdf.cell(0, 7, " Descrição relatada:", fill=True, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 6, f"{_sanitize(desc)}", border="B", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(4)

                # Reclamação com Alerta Visual
                reclamacao_row = row[12] if isinstance(row[12], str) else "Sim" if (row[12] or 0) > 0 else "Não"
                reclamacao = "SIM" if reclamacao_row == "Sim" else "NÃO"
                rec_bg = _DANGER_BG if reclamacao == "SIM" else None
                rec_color = _DANGER_COLOR if reclamacao == "SIM" else None

                pdf._row("Houve Reclamação?", reclamacao, val_color=rec_color, bg_color=rec_bg)
                pdf._row("Retornante no mês?", "N/A")
                pdf.ln(4)

                # 5. Métricas e Análise
                pdf._section("Métricas e Análise (GP/GQ)")

                # Formatação Condicional NPS
                nps_val = _val(row[11])
                nps_color = None
                try:
                    nps_int = int(nps_val)
                    if nps_int >= 9:
                        nps_color = _SUCCESS_COLOR
                    elif nps_int <= 6:
                        nps_color = _DANGER_COLOR
                except:
                    pass

                pdf._two_cols("Nota do Técnico:", _val(row[10]), "Nota NPS:", nps_val, v2_color=nps_color)
                pdf._two_cols("Agente:", _val(row[2]), "Departamento:", _val(row[7]))
                pdf._two_cols("Data Início:", _val(row[1]), "Duração (min):", _val(row[14]))
                pdf._row("Abrir Ação Corretiva:", "NÃO")

                # 6. Chat History (Page 2+)
                if messages_dict:
                    cnvs_id = row[15]  # ID BD
                    messages = messages_dict.get(cnvs_id, [])

                    if messages:
                        pdf.add_page()
                        pdf._chat_history_header(protocolo, _val(row[3]), _val(row[4]))

                        for msg in messages:
                            # Messages are now dictionaries
                            timestamp = msg.get("msgs_created", "")
                            content = msg.get("msgs_content", "")
                            direction = msg.get("msgs_direction", "")
                            agnt_name = msg.get("agnt_name", "")
                            cnts_name = msg.get("cnts_name", "Cliente")

                            if timestamp:
                                # Format timestamp to show only time
                                try:
                                    if " " in str(timestamp):
                                        timestamp = str(timestamp).split(" ")[1][:5]
                                except:
                                    pass

                            if not content:
                                continue

                            is_client = direction == "received"
                            sender = cnts_name if is_client else agnt_name if agnt_name else "Agente"

                            pdf._chat_message(sender, str(content), str(timestamp), is_client)

                pdf.output(pdf_path)
                generated += 1

            except Exception as e:
                logger.error(f"Failed to generate PDF for row {row}: {e}")

        logger.info(f"Generated {generated} OS PDFs in {output_dir}")
