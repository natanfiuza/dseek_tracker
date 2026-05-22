# DeepSeek Accountant & Tracker

Aplicação desktop para tracking de consumo de APIs (DeepSeek, Claude, etc.), ranking por utilizador/chave, visualização de custos e exportação de relatórios PDF para prestação de contas.

## Funcionalidades

- Leitura automática de CSVs de uso (`amount-YYYY-M.csv`) e custos (`cost-YYYY-M.csv`)
- Base de dados SQLite local com prevenção de duplicados (upsert)
- Interface gráfica com filtros por período (mensal / anual)
- Gráfico de barras — ranking de chaves de API por volume de tokens
- Sumário de custos totais e por modelo
- Exportação de relatório PDF com gráfico e tabela Top 10

## Stack

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.13 |
| Dependências | Pipenv |
| Dados | pandas, SQLite |
| Interface | Tkinter + matplotlib |
| PDF | fpdf2 |
| Executável | PyInstaller |
| Pacote | PyPI (setuptools) |

## Instalação

```bash
git clone <repositório>
cd dseek_tracker_project
pipenv install
```

## Uso

```bash
pipenv run python main.py
```

### Gerar executável

```bash
pipenv install --dev
pipenv run pyinstaller main.spec
```

O executável será criado em `dist/DeepSeek Tracker/`.

### Instalar como pacote

```bash
pip install dseek_tracker
dseek-tracker
```

## Estrutura

```
├── main.py                  # Ponto de entrada
├── main.spec                # Configuração PyInstaller
├── pyproject.toml           # Metadados do pacote
├── data/                    # CSVs de entrada
│   ├── amount-YYYY-M.csv
│   └── cost-YYYY-M.csv
└── src/dseek_tracker/
    ├── database.py          # SQLite — tabelas usage e costs
    ├── processor.py         # ETL com pandas
    ├── gui.py               # Interface Tkinter + matplotlib
    └── report.py            # Exportação PDF com fpdf2
```

## Formato dos CSVs

### amount-YYYY-M.csv

| Campo | Descrição |
|---|---|
| user_id | Identificador do utilizador |
| utc_date | Data (YYYY-MM-DD) |
| model | Modelo da API |
| api_key_name | Nome descritivo da chave |
| api_key | Chave de API (mascarada) |
| type | Tipo de evento (output_tokens, input_cache_hit_tokens, input_cache_miss_tokens, request_count) |
| price | Preço unitário em USD |
| amount | Quantidade de tokens |

### cost-YYYY-M.csv

| Campo | Descrição |
|---|---|
| user_id | Identificador do utilizador |
| utc_date | Data (YYYY-MM-DD) |
| model | Modelo da API |
| wallet_type | Tipo de carteira |
| cost | Custo em USD |
| currency | Moeda (USD) |

## Licença

MIT
