"""Fixtures partilhadas para os testes."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from dseek_tracker.database import Database
from dseek_tracker.processor import DataProcessor


@pytest.fixture
def db_memoria():
    """Base de dados em ficheiro temporário (apagado no final)."""
    fd, caminho = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(caminho)
    yield db
    db.fechar()
    os.remove(caminho)


@pytest.fixture
def df_usage_sample():
    """DataFrame de exemplo com dados de uso."""
    return pd.DataFrame([
        {
            "user_id": "user-1",
            "utc_date": "2026-05-01",
            "model": "deepseek-v4-pro",
            "api_key_name": "Natan - Claude Code",
            "api_key": "sk-abc123",
            "type": "output_tokens",
            "price": 0.00000087,
            "amount": 10000,
        },
        {
            "user_id": "user-1",
            "utc_date": "2026-05-01",
            "model": "deepseek-v4-pro",
            "api_key_name": "Natan - Claude Code",
            "api_key": "sk-abc123",
            "type": "input_cache_hit_tokens",
            "price": 0.000000003625,
            "amount": 5000000,
        },
        {
            "user_id": "user-1",
            "utc_date": "2026-05-01",
            "model": "deepseek-v4-pro",
            "api_key_name": "Natan - Claude Code",
            "api_key": "sk-abc123",
            "type": "request_count",
            "price": None,
            "amount": 5,
        },
        {
            "user_id": "user-1",
            "utc_date": "2026-05-02",
            "model": "deepseek-v4-pro",
            "api_key_name": "GitPR",
            "api_key": "sk-xyz789",
            "type": "output_tokens",
            "price": 0.00000087,
            "amount": 20000,
        },
    ])


@pytest.fixture
def df_cost_sample():
    """DataFrame de exemplo com dados de custos."""
    return pd.DataFrame([
        {
            "user_id": "user-1",
            "utc_date": "2026-05-01",
            "model": "deepseek-v4-pro",
            "wallet_type": "Paid",
            "cost": 0.05,
            "currency": "USD",
        },
        {
            "user_id": "user-1",
            "utc_date": "2026-05-02",
            "model": "deepseek-v4-flash",
            "wallet_type": "Paid",
            "cost": 0.01,
            "currency": "USD",
        },
    ])


@pytest.fixture
def pasta_dados_tmp():
    """Pasta temporária com CSVs simulados para testar o DataProcessor."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # amount CSV
        amount_csv = base / "amount-2026-5.csv"
        amount_csv.write_text(
            "user_id,utc_date,model,api_key_name,api_key,type,price,amount\n"
            "user-1,2026-05-01,deepseek-v4-pro,Chave A,sk-aaa,output_tokens,0.00000087,10000\n"
            "user-1,2026-05-01,deepseek-v4-pro,Chave A,sk-aaa,request_count,,5\n"
            "user-1,2026-05-02,deepseek-v4-flash,Chave B,sk-bbb,output_tokens,0.00000028,5000\n"
        )

        # cost CSV
        cost_csv = base / "cost-2026-5.csv"
        cost_csv.write_text(
            "user_id,utc_date,model,wallet_type,cost,currency\n"
            "user-1,2026-05-01,deepseek-v4-pro,Paid,0.05,USD\n"
            "user-1,2026-05-02,deepseek-v4-flash,Paid,0.01,USD\n"
        )

        yield base
