# Relatório: Correção de Regex e Datas CSV — develop_natan

**Data:** 2026-07-28
**Tarefa:** Corrigir `DataProcessor` para reconhecer o novo formato de nome dos ficheiros CSV e normalizar datas para compatibilidade com SQLite

---

## Diagnóstico

### Problema 1: Regex de nomes de ficheiros desatualizada

Os ficheiros CSV na pasta `data/` mudaram de formato de nome:

| Formato | Exemplo |
|---|---|
| **Antigo** (esperado pelo código) | `amount-2026-5.csv` / `cost-2026-07.csv` |
| **Novo** (real na pasta) | `amount-2026-07-01_2026-07-29.csv` |

As regexes em [processor.py:14-15](src/dseek_tracker/processor.py#L14-L15) não davam match. Consequência: **nenhum ficheiro era encontrado**.

### Problema 2: Datas em formato não-ISO quebram `strftime` do SQLite

As datas nos CSVs estão no formato `20260701` (YYYYMMDD, sem hífens). O SQLite `strftime()` exige o formato ISO `2026-07-01`. Sem reconhecer a data, `strftime` retorna `NULL` → Python converte para `None`.

No [gui.py:104](src/dseek_tracker/gui.py#L104), `nomes_meses[mes]` com `mes=None` produzia o erro:

> **list indices must be integers or slices, not NoneType**

### Estrutura das colunas: ✅ Sem alterações

As colunas dos CSVs mantêm-se compatíveis com o `database.py`:

- **amount**: `user_id, utc_date, model, api_key_name, api_key, type, price, amount`
- **cost**: `user_id, utc_date, model, wallet_type, cost, currency`

---

## Correções Aplicadas

### 1. Regex — [processor.py:14-18](src/dseek_tracker/processor.py#L14-L18)

```python
# Antigo — só aceitava amount-YYYY-M.csv
PADRAO_AMOUNT = re.compile(r"amount-(\d{4})-(\d{1,2})\.csv$")

# Novo — aceita ambos os formatos (antigo + intervalo de datas)
PADRAO_AMOUNT = re.compile(r"amount-(\d{4})-(\d{1,2})(?:-\d{2}_\d{4}-\d{2}-\d{2})?\.csv$")
PADRAO_COST = re.compile(r"cost-(\d{4})-(\d{1,2})(?:-\d{2}_\d{4}-\d{2}-\d{2})?\.csv$")
```

O grupo opcional `(?:-\d{2}_\d{4}-\d{2}-\d{2})?` captura o sufixo `-01_2026-07-29` quando presente.

### 2. Normalização de datas — [processor.py:34-40](src/dseek_tracker/processor.py#L34-L40)

Método `_normalizar_data()` converte `20260701` → `2026-07-01` na leitura dos CSVs:

```python
@staticmethod
def _normalizar_data(data_str: str) -> str:
    data_str = str(data_str).strip()
    if len(data_str) == 8 and data_str.isdigit():
        return f"{data_str[:4]}-{data_str[4:6]}-{data_str[6:8]}"
    return data_str
```

Aplicado em `_ler_amount()` e `_ler_cost()`.

### 3. Migração da base de dados — [database.py:18-32](src/dseek_tracker/database.py#L18-L32)

Método `_migrar_datas()` corrige datas já existentes na BD. Executado automaticamente no `__init__` da classe `Database`. É seguro para execuções repetidas (só converte datas com 8 dígitos sem hífens).

```python
def _migrar_datas(self):
    cur = self._conexao.cursor()
    cur.execute(
        "UPDATE usage SET utc_date = substr(utc_date,1,4) || '-' || ... "
        "WHERE length(utc_date) = 8 AND utc_date NOT LIKE '%-%'"
    )
    # idem para costs
    self._conexao.commit()
```

---

## Validação

### Teste de regex (todos os formatos)

```
OK: amount-2026-07-01_2026-07-29.csv -> ano=2026, mes=07  (novo)
OK: amount-2026-5.csv                -> ano=2026, mes=5   (regressão)
```

### Teste de integração (BD temporária, 8 ficheiros CSV)

| Métrica | Resultado |
|---|---|
| Períodos detetados | `[(2026, 4), (2026, 5), (2026, 6), (2026, 7)]` ✅ |
| Usage carregados | 1758 novos, 0 ignorados |
| Costs carregados | 171 novos, 0 ignorados |
| Formato datas | `2026-04-29` (ISO) ✅ |
| Ranking (14 chaves) | ✅ |
| Custos por modelo | deepseek-v4-pro: $73.14 + deepseek-v4-flash: $9.96 |
| Combo períodos | `['Abr/2026', 'Mai/2026', 'Jun/2026', 'Jul/2026']` ✅ |

---

## Ficheiros Modificados

| Ficheiro | Alteração |
|---|---|
| [src/dseek_tracker/processor.py](src/dseek_tracker/processor.py) | Regex atualizada + `_normalizar_data()` + chamada em `_ler_amount`/`_ler_cost` |
| [src/dseek_tracker/database.py](src/dseek_tracker/database.py) | Adicionado `_migrar_datas()` para corrigir datas existentes |

## Ficheiros Presentes em `data/`

```
amount-2026-04-01_2026-05-01.csv    cost-2026-04-01_2026-05-01.csv
amount-2026-05-01_2026-06-01.csv    cost-2026-05-01_2026-06-01.csv
amount-2026-06-01_2026-07-01.csv    cost-2026-06-01_2026-07-01.csv
amount-2026-07-01_2026-07-29.csv    cost-2026-07-01_2026-07-29.csv
```
