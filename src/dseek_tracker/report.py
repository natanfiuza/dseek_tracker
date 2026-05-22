"""Exportação de relatórios PDF com fpdf2."""

import os

from fpdf import FPDF


class Relatorio(FPDF):
    """PDF formal para prestação de contas do consumo de APIs."""

    def __init__(self, periodo: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.periodo = periodo
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            self.set_font("Helvetica", "B", 18)
            self.set_text_color(27, 82, 118)
            self.cell(0, 12, "DeepSeek Accountant & Tracker", align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 11)
            self.set_text_color(100, 100, 100)
            self.cell(0, 7, f"Relatorio de Consumo - {self.periodo}", align="C", new_x="LMARGIN", new_y="NEXT")
            self.line(self.l_margin, self.get_y() + 1, self.w - self.r_margin, self.get_y() + 1)
            self.ln(6)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}  |  Gerado por DeepSeek Accountant & Tracker", align="C")


def _escrever_seccao(pdf, titulo, ranking, custo_total):
    """Escreve uma secção de ranking + custo no PDF."""
    # -- Sumário de custo ------------------------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(27, 82, 118)
    pdf.cell(0, 8, f"{titulo}  |  Custo: US$ {custo_total:,.2f}", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    if not ranking:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 6, "  Sem dados de uso neste periodo.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    # -- Tabela de ranking -----------------------------------------------
    col_nome = 110
    col_tokens = 35
    col_custo = 35

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(235, 240, 245)
    pdf.cell(col_nome, 7, "  Chave API", fill=True)
    pdf.cell(col_tokens, 7, "Tokens", align="R", fill=True)
    pdf.cell(col_custo, 7, "Custo Est. USD", align="R", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for i, (nome, tokens, custo_est) in enumerate(ranking[:10]):
        if i % 2 == 0:
            pdf.set_fill_color(248, 248, 248)
        else:
            pdf.set_fill_color(255, 255, 255)

        if tokens >= 1_000_000:
            txt_tokens = f"{tokens / 1_000_000:,.1f}M"
        elif tokens >= 1_000:
            txt_tokens = f"{tokens / 1_000:,.0f}K"
        else:
            txt_tokens = str(tokens)

        pdf.cell(col_nome, 6, f"  {nome}", fill=True)
        pdf.cell(col_tokens, 6, txt_tokens, align="R", fill=True)
        pdf.cell(col_custo, 6, f"$ {custo_est or 0.0:,.2f}", align="R", fill=True)
        pdf.ln()
    pdf.ln(4)


def gerar_pdf(caminho_saida: str, periodo: str, seccoes, png_grafico: str = None):
    """Gera o PDF final com cabeçalho, gráfico e secções por período.

    Args:
        caminho_saida: Caminho onde guardar o PDF.
        periodo: String descritiva do período agregado (ex: "05/2026" ou "2026 (anual)").
        seccoes: Lista de tuplos (titulo, ranking, custo_total).
                 Para visão mensal: 1 elemento.
                 Para visão anual: 1 elemento por mês.
        png_grafico: Caminho para PNG do gráfico a embutir no topo do PDF.
    """
    pdf = Relatorio(periodo)
    pdf.alias_nb_pages()
    pdf.add_page()

    # -- Gráfico (visão geral) -------------------------------------------
    if png_grafico and os.path.isfile(png_grafico):
        pdf.image(png_grafico, x=pdf.l_margin, w=pdf.w - pdf.l_margin - pdf.r_margin, h=105)
        pdf.ln(4)

    # -- Secções por período ---------------------------------------------
    pdf.set_text_color(50, 50, 50)
    for titulo, ranking, custo_total in seccoes:
        _escrever_seccao(pdf, titulo, ranking, custo_total)

    pdf.output(caminho_saida)
