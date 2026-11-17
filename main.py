import os

from base_conhecimento import BaseConhecimento
from assistente import Assistente

PASTA = os.path.dirname(os.path.abspath(__file__))


def main():
    base = BaseConhecimento(os.path.join(PASTA, "data", "base_conhecimento.json"))
    if not base.carregar():
        print(f"Erro: {base.erro}")
        print("Verifique o arquivo data/base_conhecimento.json e tente de novo.")
        return

    assistente = Assistente("Citizen Assist AI", base)
    print("Orientação para jovens no primeiro emprego.")
    print("Este assistente NÃO é um canal oficial e nunca pede dados pessoais.")
    assistente.menu()


if __name__ == "__main__":
    main()
