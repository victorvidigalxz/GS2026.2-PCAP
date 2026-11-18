# Citizen Assist AI

Assistente de terminal, feito em Python, que orienta **jovens no primeiro emprego** sobre documentos, direitos e caminhos para começar a trabalhar. Ele responde só com o que está na base de conhecimento (JSON), mostra a fonte e a data de verificação, avisa que não é canal oficial e nunca pede dados pessoais.

## Integrantes
| Nome | RM |
|------|----|
| Victor Vidigal | 571318 |
| Gabriel Savoy | 568991 |
| Raphael Tien | 570261 |

## Público e problema
**Público:** jovens que estão procurando o primeiro emprego.
**Problema:** a informação sobre CPF, Carteira de Trabalho Digital, título de eleitor, alistamento, Jovem Aprendiz, FGTS e direitos básicos está espalhada em vários sites, em linguagem técnica, e muitas vezes misturada com páginas falsas. O assistente reúne tudo em respostas curtas, em linguagem simples, com fonte oficial.

## ODS relacionados
- **ODS 8** – Trabalho decente e crescimento econômico
- **ODS 10** – Redução das desigualdades
- **ODS 16** – Paz, justiça e instituições eficazes (acesso à informação)

## Como executar
Requisitos: Python 3.8 ou superior. Não usa bibliotecas externas.

```bash
python main.py
```

Menu: 1) pergunta livre, 2) navegar por categorias, 3) indicadores, 4) exportar CSV, 0) sair. Em todas as telas, **0 volta**.

## Estrutura
```
citizen-assist-ai/
├── README.md
├── main.py               # inicia o programa
├── orientacao.py         # classe Orientacao
├── base_conhecimento.py  # classe BaseConhecimento + normalizar()
├── assistente.py         # classe Assistente
└── data/
    ├── base_conhecimento.json
    ├── historico.json
    └── atendimentos.csv
```
Composição: `Assistente` → `base: BaseConhecimento` → `orientacoes: [Orientacao, ...]`.

## Regra de pontuação
Pergunta, palavras-chave e título são normalizados (minúsculas, sem acentos e sem pontuação).

| Regra | Pontos |
|-------|--------|
| Palavra-chave da orientação aparece na pergunta | +3 |
| Palavra da pergunta (4 letras ou mais) aparece no título | +1 |

- 6 pontos ou mais: confiança **ALTA**
- 3 a 5 pontos: confiança **MÉDIA**
- Menos de 3 pontos: "Não encontrei", com sugestão de outras palavras e das categorias.

`buscar()` devolve uma lista de tuplas `(pontos, orientacao)` da maior para a menor pontuação. O assistente mostra a melhor orientação e até duas alternativas.

**Ajuste feito pela equipe:** palavras muito comuns (como, para, quero, preciso, qual, onde, fazer...) não pontuam no título, para evitar falsos acertos. Cada palavra da pergunta conta no máximo uma vez no título.

## Regras de atendimento
- Entradas inválidas (vazio, letras, número fora da faixa, s/n inválido) nunca encerram o programa.
- Pergunta com 8 ou mais dígitos ou com `@` é recusada e **não é registrada**.
- Toda resposta mostra fonte, data de verificação e o aviso de que não é canal oficial.
- JSON de base ausente ou corrompido mostra uma mensagem de erro, sem travar. Histórico corrompido é ignorado.

## Histórico, indicadores e CSV
Cada atendimento vai para `data/historico.json` com data, origem, pergunta, id da orientação, se encontrou, se ajudou, tentativas e tempo em segundos. Ao sair, o assistente pede uma nota de facilidade de 1 a 5. Indicadores: resposta encontrada (%), taxa de acerto (%), tempo médio para encontrar, tentativas por atendimento, facilidade de uso e lista de dúvidas sem solução. A opção 4 exporta tudo para `data/atendimentos.csv` com `csv.DictWriter`.

## Integrações com outras disciplinas
Nenhuma (a busca por pontuação é a parte avaliada em PCP).

## Fontes consultadas
- Portal gov.br: https://www.gov.br
- Ministério do Trabalho e Emprego: https://www.gov.br/trabalho-e-emprego
- Receita Federal: https://www.gov.br/receitafederal
- Ministério da Defesa: https://www.gov.br/defesa
- Tribunal Superior Eleitoral: https://www.tse.jus.br
- Portal do FGTS: https://www.fgts.gov.br
- Catálogo de serviços: https://www.gov.br/pt-br/servicos

Todas as orientações foram conferidas por pesquisa em 17/11/2026 (campo `verificado_em` do JSON).

## Resultado do teste com usuários
Teste com **3 pessoas de fora da equipe** (identificadas apenas como A, B e C, sem nomes nem dados pessoais), somando **15 atendimentos**. Os atendimentos do teste foram **simulados com apoio de IA, com autorização do professor**.

| Indicador | Resultado |
|-----------|-----------|
| Atendimentos | 15 |
| Resposta encontrada (%) | 86.7 |
| Taxa de acerto: ajudou (%) | 80.0 |
| Tempo médio para encontrar | 15.8 s |
| Tentativas por atendimento | 1.2 |
| Facilidade de uso (1 a 5) | 4.3 |

**Dúvidas sem solução:**
- quero abrir minha empresa
- Como pego vale-transporte?

**Melhoria feita a partir do teste:** a pergunta "O que levo no primeiro dia de trabalho?" não foi encontrada na primeira tentativa. Foi adicionada a palavra-chave `primeiro dia de trabalho` à orientação 7 (documentos para o primeiro emprego). Depois da alteração, a pergunta passou a ser encontrada. As dúvidas sobre MEI e vale-transporte ficaram sem solução porque não estão na base (limitação conhecida).

## Limitações
- A base tem 14 orientações; perguntas fora dela não são respondidas.
- A busca compara palavras exatas: erros de digitação ("cpff") e sinônimos não cadastrados não são entendidos.
- As informações podem mudar; o assistente não atualiza a base sozinho.
- Não é canal oficial.

## Vídeo técnico
Link (YouTube, não listado): https://youtu.be/_sEknAh6M4I
