"""Processador de dados: leitura de CSVs, transformação e carga no SQLite."""

import re
from pathlib import Path

import pandas as pd

from .database import Database


class DataProcessor:
    """Vasculha a pasta data/, lê CSVs e alimenta a base de dados."""

    PADRAO_AMOUNT = re.compile(r"amount-(\d{4})-(\d{1,2})\.csv$")
    PADRAO_COST = re.compile(r"cost-(\d{4})-(\d{1,2})\.csv$")

    def __init__(self, data_dir: str = None, db: Database = None, remover_apos: bool = True):
        if data_dir is None:
            data_dir = str(Path(__file__).resolve().parent.parent.parent / "data")
        self.data_dir = Path(data_dir)
        self.db = db or Database()
        self.remover_apos = remover_apos

    def _listar_ficheiros(self, padrao):
        """Lista ficheiros CSV que batem com o padrão (amount ou cost)."""
        ficheiros = []
        for f in self.data_dir.glob("*.csv"):
            m = padrao.match(f.name)
            if m:
                ano, mes = int(m.group(1)), int(m.group(2))
                ficheiros.append((f, ano, mes))
        return sorted(ficheiros, key=lambda x: (x[1], x[2]))

    def _ler_amount(self, caminho):
        """Lê um ficheiro amount-*.csv e devolve DataFrame limpo."""
        df = pd.read_csv(caminho)
        # Converter price: strings vazias -> None
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        # Filtrar apenas eventos de tokens (excluir request_count)
        df_tokens = df[df["type"] != "request_count"].copy()
        return df_tokens

    def _ler_cost(self, caminho):
        """Lê um ficheiro cost-*.csv e devolve DataFrame limpo."""
        df = pd.read_csv(caminho)
        return df

    def processar_tudo(self):
        """Processa todos os CSVs e carrega na base de dados.

        CSVs são cumulativos — contêm todos os dados do mês.
        Após processamento com sucesso, os ficheiros são removidos
        para evitar reprocessamento na próxima execução.

        Retorna (novos_usage, novos_costs, ignorados_usage, ignorados_costs).
        """
        datas_uso_antes = self.db.datas_uso_existentes()
        datas_custo_antes = self.db.datas_custo_existentes()

        novos_usage = 0
        ignorados_usage = 0
        ficheiros_uso = []

        for caminho, ano, mes in self._listar_ficheiros(self.PADRAO_AMOUNT):
            df = self._ler_amount(caminho)
            datas_no_csv = set(df["utc_date"].unique())
            datas_novas = datas_no_csv - datas_uso_antes

            self.db.upsert_usage(df)
            novos_usage += len(df[df["utc_date"].isin(datas_novas)])
            ignorados_usage += len(df[~df["utc_date"].isin(datas_novas)])
            datas_uso_antes |= datas_no_csv
            ficheiros_uso.append(caminho)

        novos_costs = 0
        ignorados_costs = 0
        ficheiros_cost = []

        for caminho, ano, mes in self._listar_ficheiros(self.PADRAO_COST):
            df = self._ler_cost(caminho)
            datas_no_csv = set(df["utc_date"].unique())
            datas_novas = datas_no_csv - datas_custo_antes

            self.db.upsert_costs(df)
            novos_costs += len(df[df["utc_date"].isin(datas_novas)])
            ignorados_costs += len(df[~df["utc_date"].isin(datas_novas)])
            datas_custo_antes |= datas_no_csv
            ficheiros_cost.append(caminho)

        if self.remover_apos:
            for caminho in ficheiros_uso + ficheiros_cost:
                try:
                    caminho.unlink()
                except OSError:
                    pass

        return novos_usage, novos_costs, ignorados_usage, ignorados_costs

    def periodos_disponiveis(self):
        """Devolve lista de tuplos (ano, mes) com dados disponíveis.

        Une períodos detetados nos CSVs da pasta data/ com os já armazenados na BD.
        """
        periodos = set()
        for _, ano, mes in self._listar_ficheiros(self.PADRAO_AMOUNT):
            periodos.add((ano, mes))
        for _, ano, mes in self._listar_ficheiros(self.PADRAO_COST):
            periodos.add((ano, mes))
        for ano, mes in self.db.periodos_disponiveis():
            periodos.add((ano, mes))
        return sorted(periodos)
