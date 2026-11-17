import csv
import json
import os
import time
from datetime import datetime

from base_conhecimento import BaseConhecimento, normalizar

CAMPOS_CSV = ["data", "origem", "pergunta", "id_orientacao", "encontrou",
              "ajudou", "tentativas", "tempo_segundos", "nota_facilidade"]


def ler_texto(mensagem):
    """input() que nunca derruba o programa (Ctrl+C / fim da entrada = '0')."""
    try:
        return input(mensagem).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


def ler_numero(mensagem, minimo, maximo):
    """Repete até o usuário digitar um número dentro da faixa."""
    while True:
        texto = ler_texto(mensagem)
        if texto.isdecimal() and minimo <= int(texto) <= maximo:
            return int(texto)
        print(f"Opção inválida. Digite um número de {minimo} a {maximo}.")


def ler_sim_nao(mensagem):
    """Devolve 's', 'n' ou None (se o usuário digitar 0 para voltar)."""
    while True:
        texto = ler_texto(mensagem).lower()
        if texto in ("s", "n"):
            return texto
        if texto == "0":
            return None
        print("Resposta inválida. Digite s para sim, n para não ou 0 para voltar.")


class Assistente:
    """Quem conversa com o cidadão: atende, guarda o histórico e calcula indicadores."""

    def __init__(self, nome, base):
        self.nome = nome
        self.base = base
        pasta = os.path.dirname(base.caminho) or "."
        self.caminho_historico = os.path.join(pasta, "historico.json")
        self.caminho_csv = os.path.join(pasta, "atendimentos.csv")
        self.historico = []
        self.sessao = []  # posições no histórico dos atendimentos desta execução
        self._carregar_historico()

    # ---------- histórico ----------
    def _carregar_historico(self):
        try:
            with open(self.caminho_historico, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if isinstance(dados, list):
                self.historico = [d for d in dados if isinstance(d, dict)]
            else:
                print("Aviso: histórico em formato inesperado. Começando um novo.")
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            print("Aviso: histórico corrompido. Começando um novo.")

    def _salvar_historico(self):
        try:
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=2)
        except OSError:
            print("Aviso: não foi possível salvar o histórico.")

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou,
                  tentativas, tempo):
        """Guarda um atendimento em data/historico.json."""
        atendimento = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "origem": origem,
            "pergunta": pergunta,
            "id_orientacao": id_orientacao,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_segundos": tempo,
            "nota_facilidade": None,
        }
        self.historico.append(atendimento)
        self.sessao.append(len(self.historico) - 1)
        self._salvar_historico()

    # ---------- atendimento por pergunta ----------
    @staticmethod
    def tem_dado_pessoal(texto):
        """8 ou mais dígitos ou @ indicam CPF, telefone ou e-mail."""
        digitos = sum(1 for letra in texto if letra.isdigit())
        return digitos >= 8 or "@" in texto

    def _mostrar_nao_encontrei(self):
        print("\nNão encontrei uma orientação para essa dúvida.")
        print("Tente usar outras palavras (ex.: o nome do documento ou do serviço)")
        print("ou use a opção de navegar por categorias:")
        for categoria in self.base.categorias():
            print(f"  - {categoria}")

    def perguntar(self):
        """Atendimento por texto livre. Usa base.buscar() e orientacao.exibir()."""
        print("\n--- Pergunta livre ---")
        print("Não digite CPF, telefone ou e-mail.")
        inicio = None
        tentativas = 0
        ultima_pergunta = ""
        id_orientacao = None
        encontrou = False
        ajudou = False

        while True:
            texto = ler_texto("\nDigite sua dúvida (0 para voltar): ")
            if texto == "0":
                break
            if texto == "":
                print("Você não digitou nada. Escreva sua dúvida.")
                continue
            if self.tem_dado_pessoal(texto):
                print("Atenção: não digite CPF, telefone ou e-mail. Reescreva.")
                continue

            if inicio is None:
                inicio = time.time()
            tentativas += 1
            ultima_pergunta = texto

            resultados = self.base.buscar(texto)
            if not resultados or self.base.confianca(resultados[0][0]) is None:
                encontrou = False
                id_orientacao = None
                self._mostrar_nao_encontrei()
                continue

            pontos, melhor = resultados[0]
            encontrou = True
            id_orientacao = melhor.id
            print(f"\nConfiança da resposta: {self.base.confianca(pontos)} ({pontos} pontos)")
            melhor.exibir()

            outras = [o for p, o in resultados[1:3]
                      if self.base.confianca(p) is not None]

            while True:
                resposta = ler_sim_nao("\nEssa orientação respondeu sua dúvida? (s/n): ")
                if resposta == "s":
                    ajudou = True
                    break
                if resposta is None or not outras:
                    break
                print("\nOutras orientações que podem ajudar:")
                for numero, outra in enumerate(outras, start=1):
                    print(f"  {numero}) {outra.titulo} [{outra.categoria}]")
                escolha = ler_numero("Número para ver (0 para escrever outra dúvida): ",
                                     0, len(outras))
                if escolha == 0:
                    break
                escolhida = outras.pop(escolha - 1)
                id_orientacao = escolhida.id
                escolhida.exibir()

            if ajudou or resposta is None:
                break
            print("Tudo bem. Tente escrever sua dúvida de outro jeito.")

        if inicio is not None:
            tempo = round(time.time() - inicio, 1)
            self.registrar("pergunta", ultima_pergunta, id_orientacao, encontrou,
                           ajudou, tentativas, tempo)
            if ajudou:
                print("Que bom que ajudou!")

    # ---------- navegação por categorias ----------
    def navegar(self):
        """Atendimento por categorias, com 0 para voltar em todas as telas."""
        categorias = self.base.categorias()
        while True:
            print("\n--- Categorias ---")
            for numero, categoria in enumerate(categorias, start=1):
                print(f"  {numero}) {categoria}")
            print("  0) Voltar")
            escolha = ler_numero("Escolha uma categoria: ", 0, len(categorias))
            if escolha == 0:
                return
            categoria = categorias[escolha - 1]

            while True:
                lista = self.base.por_categoria(categoria)
                print(f"\n--- {categoria} ---")
                for numero, orientacao in enumerate(lista, start=1):
                    print(f"  {numero}) {orientacao.titulo}")
                print("  0) Voltar")
                numero = ler_numero("Escolha uma orientação: ", 0, len(lista))
                if numero == 0:
                    break
                inicio = time.time()
                orientacao = lista[numero - 1]
                orientacao.exibir()
                resposta = ler_sim_nao("\nEssa orientação respondeu sua dúvida? (s/n): ")
                tempo = round(time.time() - inicio, 1)
                self.registrar("categoria", orientacao.titulo, orientacao.id,
                               True, resposta == "s", 1, tempo)

    # ---------- indicadores ----------
    def indicadores(self):
        """Calcula e mostra os indicadores. Devolve um dicionário com os valores."""
        total = len(self.historico)
        if total == 0:
            print("\nAinda não há atendimentos registrados.")
            return {}

        encontrados = [a for a in self.historico if a.get("encontrou")]
        ajudados = [a for a in self.historico if a.get("ajudou")]
        tempos = [a.get("tempo_segundos", 0) for a in encontrados]
        tentativas = [a.get("tentativas", 1) for a in self.historico]
        notas = [a["nota_facilidade"] for a in self.historico
                 if isinstance(a.get("nota_facilidade"), int)]
        sem_solucao = []
        for a in self.historico:
            if not a.get("ajudou") and a.get("origem") == "pergunta":
                if a.get("pergunta") and a["pergunta"] not in sem_solucao:
                    sem_solucao.append(a["pergunta"])

        valores = {
            "atendimentos": total,
            "resposta_encontrada_pct": round(100 * len(encontrados) / total, 1),
            "ajudou_pct": round(100 * len(ajudados) / total, 1),
            "tempo_medio_s": round(sum(tempos) / len(tempos), 1) if tempos else 0.0,
            "tentativas_media": round(sum(tentativas) / total, 1),
            "facilidade_media": round(sum(notas) / len(notas), 1) if notas else None,
            "sem_solucao": sem_solucao,
        }

        print("\n--- Indicadores ---")
        print(f"Atendimentos registrados:    {valores['atendimentos']}")
        print(f"Resposta encontrada (%):     {valores['resposta_encontrada_pct']}")
        print(f"Taxa de acerto: ajudou (%):  {valores['ajudou_pct']}")
        print(f"Tempo médio para encontrar:  {valores['tempo_medio_s']} s")
        print(f"Tentativas por atendimento:  {valores['tentativas_media']}")
        if valores["facilidade_media"] is None:
            print("Facilidade de uso (1 a 5):   sem notas ainda")
        else:
            print(f"Facilidade de uso (1 a 5):   {valores['facilidade_media']}")
        print("Dúvidas sem solução:")
        if sem_solucao:
            for duvida in sem_solucao:
                print(f"  - {duvida}")
        else:
            print("  (nenhuma)")
        return valores

    # ---------- CSV ----------
    def exportar_csv(self):
        """Exporta os atendimentos para data/atendimentos.csv com DictWriter."""
        if not self.historico:
            print("\nNão há atendimentos para exportar.")
            return
        try:
            with open(self.caminho_csv, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CSV,
                                          extrasaction="ignore")
                escritor.writeheader()
                for atendimento in self.historico:
                    escritor.writerow(atendimento)
            print(f"\n{len(self.historico)} atendimento(s) exportado(s) para {self.caminho_csv}")
        except OSError:
            print("\nNão foi possível gravar o CSV. Feche o arquivo se ele estiver aberto.")

    # ---------- saída ----------
    def pedir_nota(self):
        """Ao sair, pede a nota de facilidade (1 a 5) dos atendimentos desta execução."""
        if not self.sessao:
            return
        nota = ler_numero("\nDe 1 a 5, quão fácil foi usar o assistente? (0 para pular): ", 0, 5)
        if nota == 0:
            return
        for posicao in self.sessao:
            self.historico[posicao]["nota_facilidade"] = nota
        self._salvar_historico()

    def menu(self):
        while True:
            print(f"\n===== {self.nome} =====")
            print("1) Fazer uma pergunta")
            print("2) Navegar por categorias")
            print("3) Ver indicadores")
            print("4) Exportar atendimentos para CSV")
            print("0) Sair")
            opcao = ler_numero("Escolha uma opção: ", 0, 4)
            if opcao == 1:
                self.perguntar()
            elif opcao == 2:
                self.navegar()
            elif opcao == 3:
                self.indicadores()
            elif opcao == 4:
                self.exportar_csv()
            else:
                self.pedir_nota()
                print("\nObrigado por usar o assistente. Até logo!")
                return
