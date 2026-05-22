"""Testes para o módulo database.py."""

import pytest


class TestDatabaseCriacao:
    """Testes de criação das tabelas."""

    def test_criar_tabelas_existem(self, db_memoria):
        cur = db_memoria._conexao.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tabelas = [r[0] for r in cur.fetchall()]
        assert "usage" in tabelas
        assert "costs" in tabelas

    def test_tabela_usage_colunas(self, db_memoria):
        cur = db_memoria._conexao.cursor()
        cur.execute("PRAGMA table_info(usage)")
        colunas = {r[1]: r[2] for r in cur.fetchall()}
        for col in ["user_id", "utc_date", "model", "api_key_name", "api_key", "type", "price", "amount"]:
            assert col in colunas

    def test_tabela_costs_colunas(self, db_memoria):
        cur = db_memoria._conexao.cursor()
        cur.execute("PRAGMA table_info(costs)")
        colunas = {r[1]: r[2] for r in cur.fetchall()}
        for col in ["user_id", "utc_date", "model", "wallet_type", "cost", "currency"]:
            assert col in colunas


class TestUpsertUsage:
    """Testes de inserção de dados de uso."""

    def test_inserir_registos(self, db_memoria, df_usage_sample):
        # Filtrar só tokens (como o processor faz)
        df_tokens = df_usage_sample[df_usage_sample["type"] != "request_count"]
        db_memoria.upsert_usage(df_tokens)

        cur = db_memoria._conexao.cursor()
        cur.execute("SELECT COUNT(*) FROM usage")
        assert cur.fetchone()[0] == 3

    def test_nao_duplica_mesma_chave(self, db_memoria, df_usage_sample):
        df_tokens = df_usage_sample[df_usage_sample["type"] != "request_count"]
        db_memoria.upsert_usage(df_tokens)
        # Segunda inserção dos mesmos dados
        db_memoria.upsert_usage(df_tokens)

        cur = db_memoria._conexao.cursor()
        cur.execute("SELECT COUNT(*) FROM usage")
        assert cur.fetchone()[0] == 3  # mesmo valor, sem duplicação

    def test_request_count_nao_inserido(self, db_memoria, df_usage_sample):
        """request_count é filtrado pelo DataProcessor; se chegar à BD é inserido mas com price=NULL."""
        df_req = df_usage_sample[df_usage_sample["type"] == "request_count"]
        db_memoria.upsert_usage(df_req)

        cur = db_memoria._conexao.cursor()
        cur.execute("SELECT price FROM usage WHERE type='request_count'")
        row = cur.fetchone()
        assert row[0] is None


class TestUpsertCosts:
    """Testes de inserção de dados de custos."""

    def test_inserir_custos(self, db_memoria, df_cost_sample):
        db_memoria.upsert_costs(df_cost_sample)

        cur = db_memoria._conexao.cursor()
        cur.execute("SELECT COUNT(*) FROM costs")
        assert cur.fetchone()[0] == 2

    def test_nao_duplica_custos(self, db_memoria, df_cost_sample):
        db_memoria.upsert_costs(df_cost_sample)
        db_memoria.upsert_costs(df_cost_sample)

        cur = db_memoria._conexao.cursor()
        cur.execute("SELECT COUNT(*) FROM costs")
        assert cur.fetchone()[0] == 2


class TestConsultas:
    """Testes das consultas analíticas."""

    @pytest.fixture
    def db_com_dados(self, db_memoria, df_usage_sample, df_cost_sample):
        df_tokens = df_usage_sample[df_usage_sample["type"] != "request_count"]
        db_memoria.upsert_usage(df_tokens)
        db_memoria.upsert_costs(df_cost_sample)
        return db_memoria

    def test_ranking_sem_filtro(self, db_com_dados):
        ranking = db_com_dados.consultar_ranking()
        assert len(ranking) == 2  # Natan - Claude Code e GitPR
        # Ordenado por total_tokens DESC
        assert ranking[0][1] >= ranking[1][1]

    def test_ranking_filtro_mes(self, db_com_dados):
        ranking = db_com_dados.consultar_ranking(ano=2026, mes=5)
        assert len(ranking) == 2

    def test_ranking_filtro_mes_sem_dados(self, db_com_dados):
        ranking = db_com_dados.consultar_ranking(ano=2026, mes=1)
        assert ranking == []

    def test_custos_sem_filtro(self, db_com_dados):
        custos = db_com_dados.consultar_custos()
        assert len(custos) == 2

    def test_custos_filtro_mes(self, db_com_dados):
        custos = db_com_dados.consultar_custos(ano=2026, mes=5)
        assert len(custos) == 2

    def test_total_custo_mes(self, db_com_dados):
        total = db_com_dados.consultar_total_custo_mes(ano=2026, mes=5)
        assert total == pytest.approx(0.06)

    def test_total_custo_mes_sem_dados(self, db_com_dados):
        total = db_com_dados.consultar_total_custo_mes(ano=2026, mes=1)
        assert total == 0.0


class TestExistenciaDatas:
    """Testes de verificação de datas já processadas."""

    @pytest.fixture
    def db_com_dados(self, db_memoria, df_usage_sample, df_cost_sample):
        df_tokens = df_usage_sample[df_usage_sample["type"] != "request_count"]
        db_memoria.upsert_usage(df_tokens)
        db_memoria.upsert_costs(df_cost_sample)
        return db_memoria

    def test_existe_uso_na_data(self, db_com_dados):
        assert db_com_dados.existe_uso_na_data("2026-05-01") is True
        assert db_com_dados.existe_uso_na_data("2026-05-02") is True
        assert db_com_dados.existe_uso_na_data("2026-01-15") is False

    def test_existe_custo_na_data(self, db_com_dados):
        assert db_com_dados.existe_custo_na_data("2026-05-01") is True
        assert db_com_dados.existe_custo_na_data("2026-05-02") is True
        assert db_com_dados.existe_custo_na_data("2026-01-15") is False

    def test_existe_em_bd_vazia(self, db_memoria):
        assert db_memoria.existe_uso_na_data("2026-05-01") is False
        assert db_memoria.existe_custo_na_data("2026-05-01") is False

    def test_datas_uso_existentes(self, db_com_dados):
        datas = db_com_dados.datas_uso_existentes()
        assert "2026-05-01" in datas
        assert "2026-05-02" in datas
        assert "2026-01-15" not in datas

    def test_datas_custo_existentes(self, db_com_dados):
        datas = db_com_dados.datas_custo_existentes()
        assert "2026-05-01" in datas
        assert "2026-05-02" in datas

    def test_datas_vazias_sem_dados(self, db_memoria):
        assert db_memoria.datas_uso_existentes() == set()
        assert db_memoria.datas_custo_existentes() == set()
