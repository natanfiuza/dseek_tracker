# Relatório: Correção do erro `'utc_date'` ao processar CSVs — develop_natan

**Data:** 2026-08-17
**Tarefa:** Corrigir `KeyError: 'utc_date'` exibido ao iniciar a aplicação e ao clicar em "Atualizar Dados"

---

## Diagnóstico

### Problema: CSVs da DeepSeek mudaram de colunas

A exportação de usage/costs da API DeepSeek deixou de incluir a coluna `utc_date`. Os CSVs atuais em `data/` usam colunas de intervalo de tempo ISO:

| Ficheiro | Formato novo (atual) | Formato antigo (esperado pelo código) |
|---|---|---|
| **amount** | `user_id, start_time_iso, end_time_iso, model, api_key_name, api_key, type, price, amount` | `user_id, utc_date, model, api_key_name, api_key, type, price, amount` |
| **cost** | `user_id, start_time_iso, end_time_iso, model, wallet_type, cost, currency` | `user_id, utc_date, model, wallet_type, cost, currency` |

Exemplo real: `2026-08-01T00:00:00-03:00,2026-08-02T00:00:00-03:00,...`

Como [processor.py](src/dseek_tracker/processor.py) fazia `df["utc_date"]` diretamente em `_ler_amount()` e `_ler_cost()`, o pandas lançava `KeyError: 'utc_date'`. O erro propagava para a GUI nos dois pontos reportados pelo utilizador:

- Ao iniciar — [gui.py:92](src/dseek_tracker/gui.py#L92): "Falha ao processar CSVs: 'utc_date'"
- Ao clicar em "Atualizar Dados" — [gui.py:148](src/dseek_tracker/gui.py#L148): "Falha ao atualizar: 'utc_date'"

---

## Correções Aplicadas

### Novo método `_extrair_utc_date()` — [processor.py:48-61](src/dseek_tracker/processor.py#L48-L61)

Deriva a coluna `utc_date` consoante o formato do CSV, mantendo retrocompatibilidade:

```python
def _extrair_utc_date(self, df):
    if "utc_date" in df.columns:
        return df["utc_date"].apply(self._normalizar_data)
    if "start_time_iso" in df.columns:
        datas_utc = pd.to_datetime(df["start_time_iso"], utc=True)
        return datas_utc.dt.strftime("%Y-%m-%d")
    raise KeyError("utc_date")
```

- **Formato antigo** (`utc_date` presente): normalização `YYYYMMDD` → `YYYY-MM-DD`, como antes.
- **Formato novo** (`start_time_iso` presente): o timestamp é convertido para UTC (`utc=True`, tratando corretamente o offset, ex.: `-03:00`) e truncado à data, preservando a semântica de `utc_date` e o formato ISO exigido pelo `strftime()` do SQLite.

`_ler_amount()` e `_ler_cost()` passaram a usar `df["utc_date"] = self._extrair_utc_date(df)`.

---

## Validação

Teste executado com BD e pasta `data/` temporárias (cópia dos CSVs reais, `remover_apos=False`):

### Formato novo (CSVs de agosto reais)

| Métrica | Resultado |
|---|---|
| `processar_tudo()` | `(479, 34, 0, 0)` ✅ |
| Períodos detetados | `[(2026, 8)]` ✅ |
| Datas usage | `2026-08-01` … `2026-08-17` (ISO) ✅ |
| Datas costs | `2026-08-01` … `2026-08-17` (ISO) ✅ |
| Ranking (top 5) | Natan - Claude Code: 571M tokens / US$ 11,30 ✅ |
| Custos por modelo | deepseek-v4-pro: US$ 26,91 + deepseek-v4-flash: US$ 4,27 ✅ |

### Regressão — formato antigo (CSV com coluna `utc_date`)

| Métrica | Resultado |
|---|---|
| `processar_tudo()` | `(1, 1, 0, 0)` ✅ |
| Datas | `20260501` → `2026-05-01` (normalizadas) ✅ |

---

## Ficheiros Modificados

| Ficheiro | Alteração |
|---|---|
| [src/dseek_tracker/processor.py](src/dseek_tracker/processor.py) | Adicionado `_extrair_utc_date()`; `_ler_amount`/`_ler_cost` usam-no em vez de aceder diretamente a `df["utc_date"]` |

## Observações

- Os ficheiros CSV mantêm o padrão de nome já suportado pela regex (`amount-2026-08-01_2026-08-17.csv`) — sem alterações nessa parte.
- `request_count` (price vazio) continua a ser tratado por `pd.to_numeric(..., errors="coerce")` e filtrado em `_ler_amount()`.
- Recomendação futura: atualizar a secção "Convenções" do [CLAUDE.md](CLAUDE.md) para documentar os dois formatos de colunas (antigo com `utc_date` e novo com `start_time_iso`/`end_time_iso`).
