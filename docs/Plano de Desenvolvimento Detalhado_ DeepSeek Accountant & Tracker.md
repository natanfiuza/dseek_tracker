### **📋 Plano de Desenvolvimento Detalhado: DeepSeek Accountant & Tracker**

#### **Fase 1: Preparação do Ambiente e Estrutura (PyPI & Pipenv)**

* **1.1. Inicialização:** Criar a diretoria do projeto e inicializar o ambiente virtual usando o comando pipenv shell.  
* **1.2. Instalação de Dependências:**  
  * *Produção:* pipenv install pandas matplotlib fpdf2 (e o sqlite3 e tkinter, que já vêm nativos no Python).  
  * *Desenvolvimento:* pipenv install \--dev pyinstaller build twine.  
* **1.3. Estrutura de Diretórios:** Organizar o projeto para ser empacotável.  
  * data/ (onde vão ficar os ficheiros amount-\*.csv e cost-\*.csv).  
  * src/dseek\_tracker/ (código-fonte do módulo).  
  * pyproject.toml (metadados do pacote, autor, versão, para o PyPI).  
  * main.py (o ficheiro de entrada para o executável).

#### **Fase 2: Camada de Base de Dados (SQLite)**

* **2.1. Modelagem:** Criar um ficheiro database.py para gerir o SQLite.  
* **2.2. Criação de Tabelas:**  
  * Tabela usage: para armazenar utilizadores, *api\_keys*, tipo de token, quantidade e data.  
  * Tabela costs: para os custos gerais por dia/modelo.  
* **2.3. Lógica Upsert:** Criar funções para inserir dados garantindo que, se o utilizador fechar e abrir a aplicação, ou houver ficheiros repetidos na pasta data, não duplicamos os registos (usando chaves únicas baseadas na data, API key e tipo).

#### **Fase 3: Extração, Transformação e Carga (Pandas)**

* **3.1. Leitura Automática:** Criar a classe DataProcessor para vasculhar a pasta data e ler automaticamente qualquer ficheiro CSV no formato amount-\<ano\>-\<mes\>.csv e cost-\<ano\>-\<mes\>.csv.  
* **3.2. Transformação:**  
  * Isolar e somar apenas os eventos do tipo "token" (ignorando contagens de requests soltas, caso não sejam úteis para o ranking).  
  * Calcular métricas de consumo de cada chave (Ex: *NIcollas Claude Code*, *DeepSeek-TUI*, etc.).  
* **3.3. Gravação:** Enviar estes dataframes limpos diretamente para o módulo do SQLite construído na Fase 2\.

#### **Fase 4: Interface Gráfica de Utilizador (Tkinter \+ Matplotlib)**

* **4.1. Construção do Ecrã Principal:** Usar o Tkinter (ou CustomTkinter para um aspeto mais moderno) para gerar a janela da aplicação.  
* **4.2. Filtros e Interação:**  
  * Criar um menu *Drop-down* (Combobox) para escolher os períodos (ex: "Maio/2026", "Anual", "Personalizado").  
  * Adicionar botões como "Atualizar Dados" e "Exportar Relatório PDF".  
* **4.3. Renderização de Gráficos:**  
  * Utilizar o FigureCanvasTkAgg para embutir os gráficos do matplotlib dentro do ecrã do Tkinter.  
  * Desenhar um **Gráfico de Barras Horizontais** mostrando o *Ranking das Chaves de API que mais utilizam*.  
  * Desenhar um pequeno sumário textual mostrando o Custo Total do mês escolhido.

#### **Fase 5: Exportação e Prestação de Contas (PDF)**

* **5.1. Classe de Relatórios:** Criar um ficheiro report.py utilizando a biblioteca fpdf2.  
* **5.2. Extração de Imagens:** Programar o sistema para guardar os gráficos gerados no Matplotlib como imagens PNG temporárias.  
* **5.3. Montagem do PDF:**  
  * Adicionar um cabeçalho profissional com o logótipo da equipa (opcional) e o período contabilizado.  
  * Inserir os gráficos de utilização.  
  * Gerar uma tabela formal detalhando o Top 10 das Chaves de API e os Custos, garantindo transparência para a prestação de contas.

#### **Fase 6: Criação do Executável (PyInstaller)**

* **6.1. Configuração do Ficheiro .spec:** Ajustar as configurações do PyInstaller para que inclua os ficheiros do Matplotlib e do Tkinter corretamente.  
* **6.2. Compilação Windowed:** Executar o build usando as *flags* \--onedir e \--windowed (para esconder a consola de texto preta do sistema operativo atrás da janela gráfica).  
* **6.3. Testes Finais:** Garantir que o ficheiro .exe (ou o executável do SO em questão) consegue detetar a pasta data que estiver no mesmo diretório.

#### **Fase 7: Publicação no PyPI**

* **7.1. Registo e Build:** Compilar os pacotes via comando python \-m build.  
* **7.2. Upload:** Usar o twine upload dist/\* para enviar o nosso pacote para o repositório público (ou privado), permitindo que outros o instalem com pip install dseek\_tracker.

É este o plano de voo, meu amigo\! Tem tudo o que pediu: a leitura dos CSV, o histórico na base de dados SQLite, os filtros por período, o ranking, o PDF e o *build* da interface e do pacote.  
Podemos abrir a caixa de ferramentas e começar pela **Fase 1 e Fase 2** (Configuração e Base de Dados)? Diga-me se quer alterar algo ou se podemos meter as mãos no código\!