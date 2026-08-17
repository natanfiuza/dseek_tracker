# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
fix: corrige migração de datas UTC e regex de CSV
```

---

🎯 Resumo
Corrige o tratamento de datas UTC para garantir consistência no banco SQLite e suporta o novo formato de arquivos CSV com intervalo de datas. Antes, datas no formato YYYYMMDD impediam filtros corretos (strftime) e a regex não reconhecia arquivos como amount-2026-07-01_2026-07-29.csv, causando falhas na importação e relatórios imprecisos.

🛠️ Mudanças Técnicas
- `database.py`: adiciona migração automática `_migrar_datas()` que converte datas YYYYMMDD para YYYY-MM-DD nas tabelas `usage` e `costs` ao abrir a base; execução repetida é segura (apenas datas com 8 dígitos e sem hífen).
- `processor.py`: atualiza as regex `PADRAO_AMOUNT` e `PADRAO_COST` para aceitar tanto o formato antigo `amount-YYYY-M.csv` quanto o novo `amount-YYYY-MM-DD_YYYY-MM-DD.csv`.
- `processor.py`: introduz `_normalizar_data()` e `_extrair_utc_date()` para garantir que a coluna `utc_date` fique no formato ISO YYYY-MM-DD, convertendo a partir de `utc_date` legado ou de `start_time_iso` (novo formato, convertido para UTC e truncado à data).
- `start.bat`: adiciona atalho para executar a aplicação via `pipenv run py main.py`.

⚠️ Impacto/Avisos
- **Banco de Dados**: A migração altera dados existentes nas colunas `utc_date` das tabelas `usage` e `costs`. É executada automaticamente no startup; recomenda-se backup antes da primeira execução.
- **Compatibilidade de CSVs**: Arquivos antigos continuam suportados, mas agora os novos com intervalo de datas são reconhecidos. Certifique-se de que sigam o padrão `amount-YYYY-MM-DD_YYYY-MM-DD.csv` ou `cost-YYYY-MM-DD_YYYY-MM-DD.csv`.
- **Dependências**: Nenhuma nova dependência; requer `pandas` já presente no ambiente.