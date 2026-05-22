"""Interface gráfica Tkinter + matplotlib para o DeepSeek Accountant & Tracker."""

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .database import Database
from .processor import DataProcessor
from .report import gerar_pdf


class App:
    """Janela principal da aplicação."""

    def __init__(self):
        self.db = Database()
        self.processor = DataProcessor(db=self.db)

        self.root = tk.Tk()
        self.root.title("DeepSeek Accountant & Tracker")
        self.root.geometry("1024x680")
        self.root.minsize(900, 600)

        self._ano_atual = None
        self._mes_atual = None
        self._fig = None
        self._canvas = None

        self._criar_widgets()
        self._carregar_dados_iniciais()

    # ------------------------------------------------------------------ #
    #  Construção da UI                                                   #
    # ------------------------------------------------------------------ #

    def _criar_widgets(self):
        # -- Barra superior ----------------------------------------------
        barra = ttk.Frame(self.root, padding=8)
        barra.pack(fill=tk.X)

        ttk.Label(barra, text="Período:").pack(side=tk.LEFT, padx=(0, 4))
        self._combo_periodo = ttk.Combobox(barra, state="readonly", width=24)
        self._combo_periodo.pack(side=tk.LEFT, padx=4)
        self._combo_periodo.bind("<<ComboboxSelected>>", self._ao_selecionar_periodo)

        self._btn_atualizar = ttk.Button(barra, text="Atualizar Dados", command=self._atualizar_dados)
        self._btn_atualizar.pack(side=tk.LEFT, padx=8)

        self._btn_pdf = ttk.Button(barra, text="Exportar Relatório PDF", command=self._exportar_pdf)
        self._btn_pdf.pack(side=tk.RIGHT, padx=4)

        # -- Área principal ----------------------------------------------
        area = ttk.Frame(self.root)
        area.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Painel esquerdo — gráfico
        self._frame_grafico = ttk.LabelFrame(area, text="Ranking de Chaves de API (tokens)", padding=4)
        self._frame_grafico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Painel direito — sumário de custos
        painel_dir = ttk.Frame(area, width=280)
        painel_dir.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        painel_dir.pack_propagate(False)

        self._frame_custos = ttk.LabelFrame(painel_dir, text="Custos do Período", padding=8)
        self._frame_custos.pack(fill=tk.BOTH, expand=True)

        self._texto_custos = tk.Text(self._frame_custos, font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT, bg="#f5f5f5")
        self._texto_custos.pack(fill=tk.BOTH, expand=True)

        # -- Barra de estado ---------------------------------------------
        self._status = ttk.Label(self.root, text="Pronto.", relief=tk.SUNKEN, anchor=tk.W, padding=4)
        self._status.pack(fill=tk.X, side=tk.BOTTOM)

    # ------------------------------------------------------------------ #
    #  Lógica de dados                                                    #
    # ------------------------------------------------------------------ #

    def _carregar_dados_iniciais(self):
        """Processa CSVs e popula a interface pela primeira vez."""
        self._definir_status("A processar ficheiros CSV...")
        try:
            n_uso, n_custos, ign_uso, ign_custos = self.processor.processar_tudo()
            self._popular_combo_periodos()
            self._definir_status(
                f"Pronto — {n_uso} uso (+{ign_uso} já existentes), "
                f"{n_custos} custos (+{ign_custos} já existentes)."
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao processar CSVs:\n{e}")
            self._definir_status("Erro no processamento.")

    def _popular_combo_periodos(self):
        periodos = self.processor.periodos_disponiveis()
        nomes_meses = [
            "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez",
        ]
        opcoes = []
        for ano, mes in periodos:
            opcoes.append(f"{nomes_meses[mes]}/{ano}")
        # Adicionar opção "Anual" para cada ano distinto
        anos_vistos = sorted({a for a, _ in periodos})
        for ano in anos_vistos:
            opcoes.append(f"{ano} (anual)")

        self._combo_periodo["values"] = opcoes
        if opcoes:
            self._combo_periodo.current(len(opcoes) - 1)
            self._ao_selecionar_periodo()

    def _ao_selecionar_periodo(self, event=None):
        selecionado = self._combo_periodo.get()
        if not selecionado:
            return

        nomes_meses = {
            "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
            "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12,
        }

        if "(anual)" in selecionado:
            self._ano_atual = int(selecionado.replace(" (anual)", ""))
            self._mes_atual = None
        else:
            partes = selecionado.split("/")
            self._mes_atual = nomes_meses.get(partes[0], 1)
            self._ano_atual = int(partes[1])

        self._atualizar_grafico()
        self._atualizar_custos()

    def _atualizar_dados(self):
        self._definir_status("A reprocessar CSVs...")
        try:
            n_uso, n_custos, ign_uso, ign_custos = self.processor.processar_tudo()
            self._popular_combo_periodos()
            if n_uso == 0 and n_custos == 0:
                self._definir_status("Nenhum dado novo encontrado — a pasta data/ está vazia ou só contém datas já processadas.")
            else:
                self._definir_status(
                    f"Dados atualizados — {n_uso} uso (+{ign_uso} já existentes), "
                    f"{n_custos} custos (+{ign_custos} já existentes)."
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar:\n{e}")

    # ------------------------------------------------------------------ #
    #  Gráfico                                                            #
    # ------------------------------------------------------------------ #

    def _atualizar_grafico(self):
        ranking = self.db.consultar_ranking(ano=self._ano_atual, mes=self._mes_atual)
        if not ranking:
            self._definir_status("Sem dados de uso para o período selecionado.")
            return

        nomes = [r[0] for r in ranking]
        tokens = [r[1] for r in ranking]

        if self._canvas:
            self._canvas.get_tk_widget().destroy()
        if self._fig:
            plt.close(self._fig)

        self._fig, ax = plt.subplots(figsize=(8, 5))
        cores = ["#2b5b84" if "Code" in n else "#3fb5a3" for n in nomes]
        barras = ax.barh(nomes, tokens, color=cores, edgecolor="#ffffff", linewidth=0.5)
        ax.set_xlabel("Total de Tokens")
        ax.invert_yaxis()

        for barra, val in zip(barras, tokens):
            if val >= 1_000_000:
                rotulo = f"{val / 1_000_000:.1f}M"
            elif val >= 1_000:
                rotulo = f"{val / 1_000:.1f}K"
            else:
                rotulo = str(val)
            ax.text(val + max(tokens) * 0.01, barra.get_y() + barra.get_height() / 2,
                    rotulo, va="center", fontsize=8, color="#333333")

        self._fig.tight_layout(pad=2)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self._frame_grafico)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------ #
    #  Custos                                                             #
    # ------------------------------------------------------------------ #

    def _atualizar_custos(self):
        custos_modelo = self.db.consultar_custos(ano=self._ano_atual, mes=self._mes_atual)
        custo_total = sum(c[1] for c in custos_modelo) if custos_modelo else 0.0

        self._texto_custos.configure(state=tk.NORMAL)
        self._texto_custos.delete("1.0", tk.END)

        self._texto_custos.insert(tk.END, f"Custo Total:  US$ {custo_total:,.2f}\n\n", "destaque")
        self._texto_custos.insert(tk.END, "Por modelo:\n", "subtitulo")

        for modelo, custo in custos_modelo:
            self._texto_custos.insert(tk.END, f"  {modelo}\n")
            self._texto_custos.insert(tk.END, f"    US$ {custo:,.2f}\n")

        self._texto_custos.tag_configure("destaque", font=("Consolas", 12, "bold"), foreground="#1a5276")
        self._texto_custos.tag_configure("subtitulo", font=("Consolas", 10, "bold"))
        self._texto_custos.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------ #
    #  Exportação PDF                                                     #
    # ------------------------------------------------------------------ #

    def _exportar_pdf(self):
        from pathlib import Path
        from tkinter.filedialog import asksaveasfilename

        caminho = asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"relatorio_{self._ano_atual or 'todo'}_{self._mes_atual or 0}.pdf",
        )
        if not caminho:
            return

        self._definir_status("A gerar PDF...")
        try:
            nomes_meses = [
                "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
            ]
            png_path = self._salvar_grafico_temporario()

            if self._mes_atual:
                # Visão mensal — secção única
                ranking = self.db.consultar_ranking(ano=self._ano_atual, mes=self._mes_atual)
                custo_total = self.db.consultar_total_custo_mes(self._ano_atual, self._mes_atual)
                titulo = f"{nomes_meses[self._mes_atual]}/{self._ano_atual}"
                seccoes = [(titulo, ranking, custo_total)]
                periodo = f"{self._mes_atual:02d}/{self._ano_atual}"
            else:
                # Visão anual — uma secção por mês disponível
                periodos = self.db.periodos_disponiveis()
                meses_do_ano = [m for a, m in periodos if a == self._ano_atual]
                seccoes = []
                for mes in meses_do_ano:
                    ranking = self.db.consultar_ranking(ano=self._ano_atual, mes=mes)
                    custo_total = self.db.consultar_total_custo_mes(self._ano_atual, mes)
                    titulo = f"{nomes_meses[mes]}/{self._ano_atual}"
                    seccoes.append((titulo, ranking, custo_total))
                periodo = f"{self._ano_atual} (anual)"

            gerar_pdf(caminho, periodo, seccoes, png_path)
            self._definir_status(f"PDF exportado: {caminho}")
            messagebox.showinfo("Sucesso", f"Relatório guardado em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF:\n{e}")
            self._definir_status("Erro na exportação.")

    def _salvar_grafico_temporario(self):
        import tempfile
        import os
        png_path = os.path.join(tempfile.gettempdir(), "dseek_grafico_tmp.png")
        if self._fig:
            self._fig.savefig(png_path, dpi=150, bbox_inches="tight")
        return png_path

    # ------------------------------------------------------------------ #
    #  Auxiliares                                                         #
    # ------------------------------------------------------------------ #

    def _definir_status(self, texto):
        self._status.configure(text=texto)
        self.root.update_idletasks()

    def iniciar(self):
        self.root.mainloop()


def iniciar_app():
    App().iniciar()
