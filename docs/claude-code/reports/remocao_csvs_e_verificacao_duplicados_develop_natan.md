# Relatório — Remoção de CSVs Pós-Processamento e Verificação de Duplicados

**Data:** 2026-05-21
**Branch:** develop_natan
**Tarefa:** Apagar CSVs cumulativos após processamento + verificação explícita de datas já existentes

---

## Contexto

Os ficheiros CSV na pasta `data/` são cumulativos — cada `amount-YYYY-M.csv` e `cost-YYYY-M.csv` contém **todos** os dados do mês até à data de exportação. Numa segunda execução, se o ficheiro ainda estiver na pasta, os mesmos registos seriam lidos novamente. O `INSERT OR IGNORE` já evitava duplicação real na BD, mas:

1. Os ficheiros ocupam espaço desnecessário após processamento
2. A interface não informava quantos registos eram realmente novos vs. já existentes
3. Não havia verificação explícita de duplicados por dia antes do processamento

---

## Alterações Realizadas

### `src/dseek_tracker/database.py`

**4 novos métodos:**

| Método | Descrição |
|---|---|
| `existe_uso_na_data(utc_date)` | Verifica se há registos de uso para uma data específica |
| `existe_custo_na_data(utc_date)` | Verifica se há registos de custos para uma data específica |
| `datas_uso_existentes()` | Devolve `set` com todas as datas que já têm registos de uso |
| `datas_custo_existentes()` | Devolve `set` com todas as datas que já têm registos de custos |

### `src/dseek_tracker/processor.py`

**Construtor:**
- Novo parâmetro `remover_apos: bool = True` — controla se os CSVs são apagados após processamento

**`processar_tudo()` reescrito:**
1. Antes de processar, carrega `datas_uso_existentes()` e `datas_custo_existentes()` da BD
2. Para cada CSV, cruza as datas do ficheiro com as datas já processadas
3. Aplica `upsert` (INSERT OR IGNORE mantém a proteção ao nível da linha)
4. Contabiliza separadamente registos **novos** vs. **ignorados** (já existentes)
5. Remove os ficheiros CSV da pasta `data/` após processamento com sucesso

**Nova assinatura de retorno:**
```python
novos_usage, novos_custos, ignorados_usage, ignorados_custos
```

### `src/dseek_tracker/gui.py`

Atualizadas as duas chamadas a `processar_tudo()`:

- `_carregar_dados_iniciais()` — mostra no status quantos registos são novos e quantos já existiam
- `_atualizar_dados()` — se não houver dados novos, informa que a pasta está vazia ou sem novidades

---

## Testes

### database.py — `TestExistenciaDatas` (6 novos testes)

| Teste | Resultado |
|---|---|
| `test_existe_uso_na_data` — datas com/sem registos | OK |
| `test_existe_custo_na_data` — datas com/sem registos | OK |
| `test_existe_em_bd_vazia` — BD sem dados retorna False | OK |
| `test_datas_uso_existentes` — conjunto correto de datas | OK |
| `test_datas_custo_existentes` — conjunto correto de datas | OK |
| `test_datas_vazias_sem_dados` — BD vazia retorna set vazio | OK |

### processor.py — Testes atualizados + novos

| Teste | Resultado |
|---|---|
| `test_processar_tudo_retorna_contagens` — 4 valores, todos novos | OK |
| `test_processar_tudo_carrega_na_bd` — dados persistem corretamente | OK |
| `test_segunda_execucao_detetava_ignorados` — 2ª execução: 0 novos, 100% ignorados | OK |
| `test_remover_apos_processamento` — CSVs são apagados após processar | OK |

**Total: 38/38 testes passando.**

---

## Comportamento em Execução

```
1ª execução:
  data/ contém amount-2026-5.csv e cost-2026-5.csv
  → processa 249 uso (0 ignorados) + 42 custos (0 ignorados)
  → apaga ambos os ficheiros
  → BD fica com todos os registos

2ª execução (no mesmo dia, sem novos CSVs):
  data/ está vazia
  → processa 0 uso + 0 custos
  → GUI mostra: "Nenhum dado novo encontrado"

3ª execução (dia seguinte, novo CSV cumulativo com +1 dia):
  data/ contém novo amount-2026-5.csv (com dados de 1-22 Mai)
  → processa apenas os registos do dia 22
  → dias 1-21 são contabilizados como ignorados
  → apaga o ficheiro
```
