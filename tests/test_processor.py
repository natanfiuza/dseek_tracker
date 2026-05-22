"""Testes para o módulo processor.py."""

import tempfile
import os
from pathlib import Path

from dseek_tracker.database import Database
from dseek_tracker.processor import DataProcessor


def _db_temporaria():
    """Cria uma BD em ficheiro temporário para isolamento entre testes."""
    fd, caminho = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Database(caminho), caminho


class TestListarFicheiros:
    """Testes de listagem de CSVs na pasta data/."""

    def test_listar_amount(self, pasta_dados_tmp):
        proc = DataProcessor(data_dir=str(pasta_dados_tmp))
        ficheiros = proc._listar_ficheiros(proc.PADRAO_AMOUNT)
        assert len(ficheiros) == 1
        caminho, ano, mes = ficheiros[0]
        assert ano == 2026
        assert mes == 5
        assert caminho.name == "amount-2026-5.csv"

    def test_listar_cost(self, pasta_dados_tmp):
        proc = DataProcessor(data_dir=str(pasta_dados_tmp))
        ficheiros = proc._listar_ficheiros(proc.PADRAO_COST)
        assert len(ficheiros) == 1
        caminho, ano, mes = ficheiros[0]
        assert ano == 2026
        assert mes == 5
        assert caminho.name == "cost-2026-5.csv"

    def test_ignora_ficheiros_fora_padrao(self, pasta_dados_tmp):
        (pasta_dados_tmp / "outro.csv").write_text("a,b,c\n1,2,3")
        proc = DataProcessor(data_dir=str(pasta_dados_tmp))
        ficheiros = proc._listar_ficheiros(proc.PADRAO_AMOUNT)
        nomes = {f[0].name for f in ficheiros}
        assert "outro.csv" not in nomes


class TestLerAmount:
    """Testes de leitura e transformação de amount-*.csv."""

    def test_filtra_request_count(self, pasta_dados_tmp):
        proc = DataProcessor(data_dir=str(pasta_dados_tmp))
        ficheiros = proc._listar_ficheiros(proc.PADRAO_AMOUNT)
        df = proc._ler_amount(ficheiros[0][0])
        # 3 linhas no CSV, 1 é request_count -> 2 devem ficar
        assert len(df) == 2
        assert "request_count" not in df["type"].values

    def test_price_nulo_vira_nan(self, pasta_dados_tmp):
        proc = DataProcessor(data_dir=str(pasta_dados_tmp))
        ficheiros = proc._listar_ficheiros(proc.PADRAO_AMOUNT)
        df = proc._ler_amount(ficheiros[0][0])
        # Todos os prices das linhas de token são numéricos
        assert df["price"].notna().all()


class TestLerCost:
    """Testes de leitura de cost-*.csv."""

    def test_ler_cost_simples(self, pasta_dados_tmp):
        proc = DataProcessor(data_dir=str(pasta_dados_tmp))
        ficheiros = proc._listar_ficheiros(proc.PADRAO_COST)
        df = proc._ler_cost(ficheiros[0][0])
        assert len(df) == 2
        assert list(df.columns) == ["user_id", "utc_date", "model", "wallet_type", "cost", "currency"]


class TestProcessarTudo:
    """Testes de integração do processamento completo."""

    def test_processar_tudo_retorna_contagens(self, pasta_dados_tmp):
        db, db_path = _db_temporaria()
        try:
            proc = DataProcessor(data_dir=str(pasta_dados_tmp), db=db, remover_apos=False)
            novos_uso, novos_custos, ign_uso, ign_custos = proc.processar_tudo()
            # 3 linhas no CSV - 1 request_count = 2 usage, 2 costs (todos novos)
            assert novos_uso == 2
            assert novos_custos == 2
            assert ign_uso == 0
            assert ign_custos == 0
        finally:
            db.fechar()
            os.remove(db_path)

    def test_processar_tudo_carrega_na_bd(self, pasta_dados_tmp):
        db, db_path = _db_temporaria()
        try:
            proc = DataProcessor(data_dir=str(pasta_dados_tmp), db=db, remover_apos=False)
            proc.processar_tudo()

            cur = db._conexao.cursor()
            cur.execute("SELECT COUNT(*) FROM usage")
            assert cur.fetchone()[0] == 2
            cur.execute("SELECT COUNT(*) FROM costs")
            assert cur.fetchone()[0] == 2
        finally:
            db.fechar()
            os.remove(db_path)

    def test_segunda_execucao_detetava_ignorados(self, pasta_dados_tmp):
        """Numa segunda execução com os mesmos CSVs, tudo deve ser ignorado."""
        db, db_path = _db_temporaria()
        try:
            proc = DataProcessor(data_dir=str(pasta_dados_tmp), db=db, remover_apos=False)
            proc.processar_tudo()
            # Segunda execução — mesmos ficheiros, mesmas datas
            novos_uso, novos_custos, ign_uso, ign_custos = proc.processar_tudo()
            assert novos_uso == 0
            assert novos_custos == 0
            assert ign_uso == 2
            assert ign_custos == 2
        finally:
            db.fechar()
            os.remove(db_path)

    def test_remover_apos_processamento(self, pasta_dados_tmp):
        """Com remover_apos=True, os CSVs são apagados após processamento."""
        db, db_path = _db_temporaria()
        try:
            proc = DataProcessor(data_dir=str(pasta_dados_tmp), db=db, remover_apos=True)
            assert len(proc._listar_ficheiros(proc.PADRAO_AMOUNT)) == 1
            assert len(proc._listar_ficheiros(proc.PADRAO_COST)) == 1

            proc.processar_tudo()

            # Após processamento, ficheiros devem ter sido removidos
            assert len(proc._listar_ficheiros(proc.PADRAO_AMOUNT)) == 0
            assert len(proc._listar_ficheiros(proc.PADRAO_COST)) == 0
        finally:
            db.fechar()
            os.remove(db_path)


class TestPeriodosDisponiveis:
    """Testes de deteção de períodos."""

    def test_periodos_disponiveis(self, pasta_dados_tmp):
        proc = DataProcessor(data_dir=str(pasta_dados_tmp))
        periodos = proc.periodos_disponiveis()
        assert (2026, 5) in periodos

    def test_sem_ficheiros(self):
        db, db_path = _db_temporaria()
        try:
            proc = DataProcessor(data_dir="/tmp/pasta_inexistente_xyz", db=db)
            periodos = proc.periodos_disponiveis()
            assert periodos == []
        finally:
            db.fechar()
            os.remove(db_path)
