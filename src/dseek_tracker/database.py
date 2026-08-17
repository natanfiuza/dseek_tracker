"""Camada de base de dados SQLite para armazenar uso e custos de APIs."""

import sqlite3
from pathlib import Path


class Database:
    """Gere a base de dados SQLite com tabelas usage e costs."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent.parent.parent / "dseek_tracker.db")
        self.db_path = db_path
        self._conexao = sqlite3.connect(db_path)
        self._criar_tabelas()
        self._migrar_datas()

    def _migrar_datas(self):
        """Converte datas YYYYMMDD → YYYY-MM-DD nas tabelas usage e costs.

        Executada automaticamente ao abrir a base de dados.
        Segura para execuções repetidas — só converte datas com 8 dígitos.
        """
        cur = self._conexao.cursor()
        # usage
        cur.execute(
            "UPDATE usage SET utc_date = substr(utc_date,1,4) || '-' || substr(utc_date,5,2) || '-' || substr(utc_date,7,2) "
            "WHERE length(utc_date) = 8 AND utc_date NOT LIKE '%-%'"
        )
        # costs
        cur.execute(
            "UPDATE costs SET utc_date = substr(utc_date,1,4) || '-' || substr(utc_date,5,2) || '-' || substr(utc_date,7,2) "
            "WHERE length(utc_date) = 8 AND utc_date NOT LIKE '%-%'"
        )
        self._conexao.commit()

    def _criar_tabelas(self):
        cur = self._conexao.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                utc_date TEXT NOT NULL,
                model TEXT NOT NULL,
                api_key_name TEXT NOT NULL,
                api_key TEXT NOT NULL,
                type TEXT NOT NULL,
                price REAL,
                amount INTEGER NOT NULL,
                UNIQUE(utc_date, api_key, model, type)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                utc_date TEXT NOT NULL,
                model TEXT NOT NULL,
                wallet_type TEXT NOT NULL,
                cost REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                UNIQUE(utc_date, model)
            )
        """)
        self._conexao.commit()

    def upsert_usage(self, df):
        """Insere ou ignora registos de uso a partir de um DataFrame.

        O DataFrame deve ter as colunas:
        user_id, utc_date, model, api_key_name, api_key, type, price, amount
        """
        cur = self._conexao.cursor()
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT OR IGNORE INTO usage (user_id, utc_date, model, api_key_name, api_key, type, price, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["user_id"], row["utc_date"], row["model"],
                    row["api_key_name"], row["api_key"], row["type"],
                    row["price"] if row["price"] else None, row["amount"],
                ),
            )
        self._conexao.commit()

    def upsert_costs(self, df):
        """Insere ou ignora registos de custos a partir de um DataFrame.

        O DataFrame deve ter as colunas:
        user_id, utc_date, model, wallet_type, cost, currency
        """
        cur = self._conexao.cursor()
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT OR IGNORE INTO costs (user_id, utc_date, model, wallet_type, cost, currency)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["user_id"], row["utc_date"], row["model"],
                    row["wallet_type"], row["cost"], row["currency"],
                ),
            )
        self._conexao.commit()

    def consultar_ranking(self, ano: int = None, mes: int = None):
        """Ranking de consumo por api_key_name, opcionalmente filtrado por ano/mês.

        Retorna uma lista de tuplos (api_key_name, total_tokens, custo_estimado).
        """
        cur = self._conexao.cursor()
        condicoes = []
        params = []
        if ano:
            condicoes.append("strftime('%Y', utc_date) = ?")
            params.append(str(ano))
        if mes:
            condicoes.append("strftime('%m', utc_date) = ?")
            params.append(f"{mes:02d}")

        where = ""
        if condicoes:
            where = "WHERE " + " AND ".join(condicoes)

        cur.execute(
            f"""
            SELECT
                api_key_name,
                SUM(CASE WHEN type != 'request_count' THEN amount ELSE 0 END) as total_tokens,
                SUM(CASE WHEN type != 'request_count' THEN amount * price ELSE 0 END) as custo_estimado
            FROM usage
            {where}
            GROUP BY api_key_name
            ORDER BY total_tokens DESC
            """
        , params)
        return cur.fetchall()

    def consultar_custos(self, ano: int = None, mes: int = None):
        """Custos totais por modelo, opcionalmente filtrado por ano/mês.

        Retorna uma lista de tuplos (model, custo_total).
        """
        cur = self._conexao.cursor()
        condicoes = []
        params = []
        if ano:
            condicoes.append("strftime('%Y', utc_date) = ?")
            params.append(str(ano))
        if mes:
            condicoes.append("strftime('%m', utc_date) = ?")
            params.append(f"{mes:02d}")

        where = ""
        if condicoes:
            where = "WHERE " + " AND ".join(condicoes)

        cur.execute(
            f"""
            SELECT model, SUM(cost) as custo_total
            FROM costs
            {where}
            GROUP BY model
            ORDER BY custo_total DESC
            """
        , params)
        return cur.fetchall()

    def consultar_total_custo_mes(self, ano: int, mes: int):
        """Custo total para um mês específico."""
        cur = self._conexao.cursor()
        cur.execute(
            """
            SELECT COALESCE(SUM(cost), 0)
            FROM costs
            WHERE strftime('%Y', utc_date) = ? AND strftime('%m', utc_date) = ?
            """,
            (str(ano), f"{mes:02d}"),
        )
        return cur.fetchone()[0]

    def existe_uso_na_data(self, utc_date: str) -> bool:
        """Verifica se já existem registos de uso para uma determinada data."""
        cur = self._conexao.cursor()
        cur.execute("SELECT COUNT(*) FROM usage WHERE utc_date = ?", (utc_date,))
        return cur.fetchone()[0] > 0

    def existe_custo_na_data(self, utc_date: str) -> bool:
        """Verifica se já existem registos de custos para uma determinada data."""
        cur = self._conexao.cursor()
        cur.execute("SELECT COUNT(*) FROM costs WHERE utc_date = ?", (utc_date,))
        return cur.fetchone()[0] > 0

    def datas_uso_existentes(self) -> set:
        """Conjunto de datas (utc_date) que já têm registos de uso."""
        cur = self._conexao.cursor()
        cur.execute("SELECT DISTINCT utc_date FROM usage")
        return {r[0] for r in cur.fetchall()}

    def datas_custo_existentes(self) -> set:
        """Conjunto de datas (utc_date) que já têm registos de custos."""
        cur = self._conexao.cursor()
        cur.execute("SELECT DISTINCT utc_date FROM costs")
        return {r[0] for r in cur.fetchall()}

    def periodos_disponiveis(self):
        """Devolve lista de tuplos (ano, mes) com dados na BD."""
        cur = self._conexao.cursor()
        cur.execute("""
            SELECT DISTINCT
                CAST(strftime('%Y', utc_date) AS INTEGER) as ano,
                CAST(strftime('%m', utc_date) AS INTEGER) as mes
            FROM usage
            UNION
            SELECT DISTINCT
                CAST(strftime('%Y', utc_date) AS INTEGER) as ano,
                CAST(strftime('%m', utc_date) AS INTEGER) as mes
            FROM costs
            ORDER BY ano, mes
        """)
        return [(r[0], r[1]) for r in cur.fetchall()]

    def fechar(self):
        self._conexao.close()
