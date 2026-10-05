# 💳 Análise do Sistema Financeiro e Crédito no Brasil (2015–2024)

Projeto G2 · Tema 28. Dashboard interativo e notebook de análise sobre concessão de crédito, juros, inadimplência e risco no sistema financeiro brasileiro.

> **Aviso:** a base de dados é **simulada**. Os resultados descrevem esta base e não o mercado de crédito real.

## 🔗 Links

| Entrega | Link |
|---|---|
| Dashboard (Streamlit Cloud) | |
| Página do projeto (GitHub Pages) | https://olinov1991.github.io/An-lise-do-Sistema-Financeiro-e-Cr-dito-no-Brasil/ |
| Notebook | https://colab.research.google.com/drive/1c2nnd6N4kSPRy-9HTA27JhKLnK32VdTl#scrollTo=sYZAq6zEKgi1 |

## 🎯 Objetivo

Responder, com dados, a sete perguntas:

1. Quais regiões apresentam maior volume de crédito?
2. Quais setores possuem maior inadimplência?
3. Houve crescimento do crédito ao longo do tempo?
4. Existe relação entre juros e inadimplência?
5. Quais modalidades financeiras apresentam maior risco?
6. Como o comportamento financeiro evoluiu?
7. Quais estados possuem maior concentração bancária?

## 🛠️ Tecnologias

Python · Pandas · Plotly · Streamlit · GitHub

## 📁 Estrutura

```
projeto-sistema-financeiro/
├── app.py                 # dashboard Streamlit
├── requirements.txt
├── index.html             # página do projeto (GitHub Pages)
├── README.md
├── dados/                 # simulacao_sistema_financeiro_brasil.csv
├── notebooks/             # analise_sistema_financeiro.ipynb
├── imagens/               # gráficos exportados pelo notebook
└── database/
```

## ▶️ Como executar

```bash
git clone https://github.com/olinov1991/An-lise-do-Sistema-Financeiro-e-Cr-dito-no-Brasil
cd projeto-sistema-financeiro
pip install -r requirements.txt
streamlit run app.py
```

Para rodar o notebook, instale também `jupyter` (e, opcionalmente, `kaleido` para exportar os gráficos em PNG):

```bash
pip install jupyter kaleido
jupyter notebook notebooks/analise_sistema_financeiro.ipynb
```

## 📊 A base de dados

4.440 registros mensais (jan/2015 a dez/2024) de 20 UFs, com 14 colunas: ano, mês, data, região, UF, modalidade de crédito, valor do crédito, taxa de juros, inadimplência, quantidade de clientes, renda média, prazo médio de pagamento, risco de crédito e setor econômico. Sem valores nulos nem duplicatas.

## 🖥️ O que o dashboard oferece

- **6 filtros:** ano, mês, região, estado, modalidade e risco.
- **6 KPIs:** volume total de crédito, taxa média de juros, inadimplência média, modalidade mais utilizada, região com maior crédito e prazo médio de pagamento.
- **7 abas:** evolução temporal, modalidades, regiões, heatmap mensal, juros × inadimplência, tabela dinâmica configurável e conclusão.
- **Interpretação dinâmica:** os textos de leitura se recalculam conforme os filtros.
- **Download** dos dados filtrados em CSV.

## 🔎 Principais achados

- **Crédito estagnado:** cerca de R$ 22,4 bi no período (~R$ 2,2 bi por ano), com variação de apenas +2,5% entre 2015 e 2024.
- **Juros e inadimplência não se relacionam:** correlação de Pearson de ≈ −0,01.
- **Sudeste lidera (~36% do volume),** em grande parte por ter mais registros; o crédito médio por operação é parecido entre as regiões.
- **A classificação de risco quase não separa a inadimplência:** diferença de ~0,3 p.p. entre risco Baixo e Alto.

## ⚠️ Limitações

- Base simulada, com distribuições uniformes e variáveis independentes, o que explica a ausência de padrões econômicos fortes.
- Cobertura de 20 das 27 UFs, com número desigual de registros por região, o que influencia os totais.
- Unidade do prazo médio de pagamento assumida como **dias**.

## 👤 Autor

ALUNO: leandro parreira novarino · DISCIPLINA: 2026.2 LINGUAGENS DE PROGRAMAÇÃO | SII1P0604N0001 · PROFESSOR: Alexandre Neves Louzada
