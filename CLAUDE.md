# CLAUDE.md — DeepSeek Accountant & Tracker

Aplicação desktop para tracking de consumo de APIs (DeepSeek, Claude, etc.), ranking por chave/utilizador, custos, e exportação de relatórios PDF para prestação de contas.

## Tech Stack

- **Python 3.13** com **Pipenv** para gestão de dependências
- **pandas** — leitura e transformação de CSVs
- **matplotlib** — gráficos (barras horizontais, sumários)
- **fpdf2** — exportação de relatórios PDF
- **sqlite3** (built-in) — base de dados local
- **tkinter** (built-in) — interface gráfica (podendo migrar para CustomTkinter)
- Dev: **pyinstaller** (gerar .exe), **build** + **twine** (publicação PyPI)

## Estrutura do Projeto

```
dseek_tracker_project/
├── main.py                  # Ponto de entrada do executável
├── pyproject.toml           # Metadados do pacote PyPI
├── Pipfile                  # Dependências (pipenv)
├── data/                    # CSVs de entrada (amount-YYYY-M.csv, cost-YYYY-M.csv)
├── src/dseek_tracker/       # Código-fonte do módulo empacotável
│   ├── __init__.py
│   ├── database.py          # Fase 2: SQLite — tabelas usage + costs, lógica upsert
│   ├── processor.py         # Fase 3: DataProcessor — leitura, transformação, carga
│   ├── gui.py               # Fase 4: Tkinter + matplotlib embutido
│   └── report.py            # Fase 5: Exportação PDF com fpdf2
├── docs/                    # Documentação e plano de desenvolvimento
└── dist/                    # Builds do PyInstaller (ignorado no git)
```

## Estado Atual (Fase 1)

- [x] `.gitignore`
- [x] `Pipfile` com pandas, matplotlib, fpdf2
- [x] `data/` com CSVs de exemplo (`amount-2026-5.csv`, `cost-2026-5.csv`)
- [ ] `main.py`
- [ ] `src/dseek_tracker/` com `__init__.py`, `database.py`, `processor.py`, `gui.py`, `report.py`
- [ ] `pyproject.toml`
- [ ] Dev dependencies (pyinstaller, build, twine)
- [ ] Executável PyInstaller

## Comandos

```bash
pipenv install                  # Instalar dependências de produção
pipenv install --dev            # Instalar dev dependencies
pipenv run python main.py       # Executar a aplicação
pipenv run pyinstaller main.spec  # Gerar executável
pipenv run python -m build      # Build do pacote PyPI
pipenv run twine upload dist/*  # Publicar no PyPI
```

## Modelo de Dados (SQLite)

Tabela **usage**: utilizador, api_key, tipo de token, quantidade, data
Tabela **costs**: custos por dia/modelo

Chaves únicas compostas (data + api_key + tipo) para evitar duplicação com upsert.

## Convenções

- Código em português (nomes de variáveis, funções, comentários)
- CSVs na pasta `data/` seguem o padrão `amount-YYYY-M.csv` e `cost-YYYY-M.csv`
- O executável final deve detetar a pasta `data/` no mesmo diretório
- Interface gráfica usa `FigureCanvasTkAgg` para embutir matplotlib no Tkinter
- Build com `--onedir --windowed` (sem console preto atrás da janela)


## Regras IMPORTANTES

- Ao final de toda tarefa elabore um relatório detalhado e grave em `docs/claude-code/reports/<nome_tarefa>_{branch}.md`, onde {branch} deve ser substituida pela branch atual