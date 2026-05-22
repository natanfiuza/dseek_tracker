"""Testes para o módulo report.py."""

import os
import tempfile

import pytest

from dseek_tracker.report import gerar_pdf, Relatorio


class TestRelatorio:
    """Testes da classe Relatorio (FPDF)."""

    def test_criar_relatorio(self):
        pdf = Relatorio("05/2026")
        assert pdf.periodo == "05/2026"
        assert pdf.page_no() == 0  # ainda não tem páginas

    def test_header_adicionado(self):
        pdf = Relatorio("05/2026")
        pdf.add_page()
        # O header foi chamado automaticamente na add_page
        assert pdf.page_no() == 1


class TestGerarPdf:
    """Testes da função gerar_pdf."""

    @pytest.fixture
    def ranking(self):
        return [
            ("Natan - Claude Code", 50_000_000, 1.50),
            ("GitPR", 10_000_000, 2.48),
            ("DeepSeek-TUI", 5_000_000, 1.20),
        ]

    def test_gerar_pdf_seccao_unica(self, ranking):
        """PDF com uma única secção (visão mensal)."""
        fd, caminho = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        try:
            seccoes = [("Maio/2026", ranking, 5.18)]
            gerar_pdf(caminho, "05/2026", seccoes)
            assert os.path.isfile(caminho)
            assert os.path.getsize(caminho) > 0
        finally:
            os.remove(caminho)

    def test_gerar_pdf_multiplas_seccoes(self, ranking):
        """PDF com várias secções (visão anual)."""
        fd, caminho = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        try:
            seccoes = [
                ("Janeiro/2026", ranking[:1], 1.50),
                ("Fevereiro/2026", ranking[:2], 3.98),
            ]
            gerar_pdf(caminho, "2026 (anual)", seccoes)
            assert os.path.isfile(caminho)
            assert os.path.getsize(caminho) > 0
        finally:
            os.remove(caminho)

    def test_seccao_sem_dados_nao_falha(self):
        """Secção com ranking vazio não deve quebrar o PDF."""
        fd, caminho = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        try:
            seccoes = [("Marco/2026", [], 0.0)]
            gerar_pdf(caminho, "03/2026", seccoes)
            assert os.path.isfile(caminho)
            assert os.path.getsize(caminho) > 0
        finally:
            os.remove(caminho)

    def test_gerar_pdf_com_grafico_inexistente_nao_falha(self, ranking):
        """Se o PNG não existe, o PDF é gerado na mesma (sem gráfico)."""
        fd, caminho = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        try:
            seccoes = [("Maio/2026", ranking, 5.18)]
            gerar_pdf(caminho, "05/2026", seccoes, png_grafico="/tmp/inexistente_xyz.png")
            assert os.path.isfile(caminho)
            assert os.path.getsize(caminho) > 0
        finally:
            os.remove(caminho)

    def test_pdf_cresce_com_mais_seccoes(self, ranking):
        """PDF com mais secções deve ser maior."""
        fd1, caminho1 = tempfile.mkstemp(suffix=".pdf")
        fd2, caminho2 = tempfile.mkstemp(suffix=".pdf")
        os.close(fd1)
        os.close(fd2)

        try:
            seccoes1 = [("Maio/2026", ranking[:1], 1.50)]
            gerar_pdf(caminho1, "05/2026", seccoes1)
            tamanho1 = os.path.getsize(caminho1)

            seccoes2 = [
                ("Maio/2026", ranking, 5.18),
                ("Abril/2026", ranking[:2], 3.98),
            ]
            gerar_pdf(caminho2, "2026 (anual)", seccoes2)
            tamanho2 = os.path.getsize(caminho2)

            assert tamanho2 >= tamanho1
        finally:
            os.remove(caminho1)
            os.remove(caminho2)
