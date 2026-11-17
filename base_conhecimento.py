import json

from orientacao import Orientacao

ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
           "í": "i", "ó": "o", "õ": "o", "ô": "o", "ú": "u", "ç": "c"}

CAMPOS = ["id", "categoria", "titulo", "palavras_chave", "resposta",
          "documentos", "onde", "fonte", "verificado_em"]

PONTOS_PALAVRA_CHAVE = 3
PONTOS_TITULO = 1
MINIMO_LETRAS_TITULO = 4
LIMITE_ALTA = 6
LIMITE_MEDIA = 3


IGNORADAS = {"como", "para", "quero", "preciso", "qual", "quais", "onde",
             "sobre", "fazer", "posso", "quando", "tenho", "minha", "meu"}


def normalizar(texto):
    """Minúsculas, sem acentos, sem pontuação e com espaços nas pontas."""
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in "?!.,;:()":
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


class BaseConhecimento:
    """Conjunto de todas as orientações, lidas de um arquivo JSON."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []
        self.erro = ""

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao. Nunca trava o programa."""
        self.orientacoes = []
        self.erro = ""
        try:
            with open(self.caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            self.erro = f"Arquivo da base não encontrado: {self.caminho}"
            return False
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.erro = f"Arquivo da base corrompido: {self.caminho}"
            return False
        except OSError:
            self.erro = f"Não foi possível abrir a base: {self.caminho}"
            return False

        if not isinstance(dados, list):
            self.erro = "A base precisa ser uma lista de orientações."
            return False

        ignorados = 0
        for registro in dados:
            if not self._registro_valido(registro):
                ignorados += 1
                continue
            campos = {campo: registro[campo] for campo in CAMPOS}
            self.orientacoes.append(Orientacao(**campos))

        if ignorados:
            print(f"Aviso: {ignorados} registro(s) inválido(s) foram ignorados.")
        if not self.orientacoes:
            self.erro = "A base não tem nenhuma orientação válida."
            return False
        return True

    @staticmethod
    def _registro_valido(registro):
        if not isinstance(registro, dict):
            return False
        if any(campo not in registro for campo in CAMPOS):
            return False
        if not isinstance(registro["palavras_chave"], list):
            return False
        if not isinstance(registro["documentos"], list):
            return False
        return True

    def categorias(self):
        """Lista as categorias, sem repetir e na ordem em que aparecem."""
        lista = []
        for orientacao in self.orientacoes:
            if orientacao.categoria not in lista:
                lista.append(orientacao.categoria)
        return lista

    def por_categoria(self, categoria):
        return [o for o in self.orientacoes if o.categoria == categoria]

    def pontuar(self, pergunta_norm, orientacao):
        """Calcula os pontos de uma orientação para a pergunta já normalizada."""
        pontos = 0
        for palavra_chave in orientacao.palavras_chave:
            chave = normalizar(str(palavra_chave))
            if chave.strip() and chave in pergunta_norm:
                pontos += PONTOS_PALAVRA_CHAVE

        titulo = normalizar(orientacao.titulo)
        for palavra in set(pergunta_norm.split()):
            if len(palavra) < MINIMO_LETRAS_TITULO or palavra in IGNORADAS:
                continue
            if " " + palavra + " " in titulo:
                pontos += PONTOS_TITULO
        return pontos

    def buscar(self, pergunta):
        """Devolve lista de tuplas (pontos, orientacao), da maior para a menor."""
        pergunta_norm = normalizar(pergunta)
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(pergunta_norm, orientacao)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda tupla: (-tupla[0], tupla[1].id))
        return resultados

    @staticmethod
    def confianca(pontos):
        """ALTA, MÉDIA ou None (não encontrado)."""
        if pontos >= LIMITE_ALTA:
            return "ALTA"
        if pontos >= LIMITE_MEDIA:
            return "MÉDIA"
        return None
