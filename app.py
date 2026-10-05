"""Dashboard Streamlit: Sistema Financeiro e Crédito no Brasil (2015–2024).

Rodar:  streamlit run app.py
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Crédito no Brasil 2015–2024", page_icon="💳", layout="wide")

CSV = Path(__file__).parent / "dados" / "simulacao_sistema_financeiro_brasil.csv"
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
ORDEM_RISCO = ["Baixo", "Médio", "Alto"]
COR_RISCO = {"Baixo": "#2e9e6b", "Médio": "#f0a500", "Alto": "#d64545"}
AZUL, VERMELHO = "#1f4e79", "#d64545"
px.defaults.template = "plotly_white"


# ---------- utilitários ----------
def fmt_num(v, casas=2):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_moeda(v):
    if abs(v) >= 1e9:
        return f"R$ {fmt_num(v / 1e9)} bi"
    if abs(v) >= 1e6:
        return f"R$ {fmt_num(v / 1e6)} mi"
    return f"R$ {fmt_num(v)}"


def mostrar(fig):
    fig.update_layout(margin=dict(t=60, b=20, l=10, r=10))
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # versões antigas do Streamlit
        st.plotly_chart(fig, use_container_width=True)


def tabela(d):
    try:
        st.dataframe(d, width="stretch")
    except TypeError:
        st.dataframe(d, use_container_width=True)


def resumo(d, por):
    """Resumo por grupo; taxas ponderadas pelo valor de crédito."""
    t = d.assign(_j=d["taxa_juros"] * d["valor_credito"], _i=d["inadimplencia_percentual"] * d["valor_credito"])
    out = t.groupby(por, observed=True).agg(
        operacoes=("valor_credito", "size"), volume=("valor_credito", "sum"),
        credito_medio=("valor_credito", "mean"), clientes=("quantidade_clientes", "sum"),
        _j=("_j", "sum"), _i=("_i", "sum"))
    out["juros_pond"] = out["_j"] / out["volume"]
    out["inad_pond"] = out["_i"] / out["volume"]
    return out.drop(columns=["_j", "_i"])


def correlacao(d):
    """Pearson juros x inadimplência e p-valor aproximado (normal). None se não calculável."""
    n = len(d)
    if n < 3 or d["taxa_juros"].nunique() < 2 or d["inadimplencia_percentual"].nunique() < 2:
        return None, None
    r = d["taxa_juros"].corr(d["inadimplencia_percentual"])
    if abs(r) >= 1:
        return r, 0.0
    t = r * math.sqrt((n - 2) / (1 - r ** 2))
    return r, math.erfc(abs(t) / math.sqrt(2))


def forca(r):
    a = abs(r)
    return "praticamente nula" if a < 0.1 else "fraca" if a < 0.3 else "moderada" if a < 0.6 else "forte"


@st.cache_data
def carregar():
    d = pd.read_csv(CSV, encoding="utf-8-sig")
    d["data"] = pd.to_datetime(d["data"])
    d["risco_credito"] = pd.Categorical(d["risco_credito"], categories=ORDEM_RISCO, ordered=True)
    d["faixa_juros"] = pd.cut(d["taxa_juros"], bins=[0, 20, 40, 60, 80, 100],
                              labels=["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"], include_lowest=True)
    return d


# ---------- dados e filtros ----------
df_all = carregar()
sb = st.sidebar
sb.header("🎛️ Filtros")
anos = sb.multiselect("Ano", sorted(df_all["ano"].unique()), default=sorted(df_all["ano"].unique()))
meses = sb.multiselect("Mês", list(range(1, 13)), default=list(range(1, 13)), format_func=lambda m: MESES[m - 1])
regioes = sb.multiselect("Região", sorted(df_all["regiao"].unique()), default=sorted(df_all["regiao"].unique()))
ufs_disp = sorted(df_all[df_all["regiao"].isin(regioes)]["uf"].unique())
ufs = sb.multiselect("Estado (UF)", ufs_disp, default=ufs_disp)
mods = sb.multiselect("Modalidade", sorted(df_all["modalidade_credito"].unique()),
                      default=sorted(df_all["modalidade_credito"].unique()))
riscos = sb.multiselect("Risco de crédito", ORDEM_RISCO, default=ORDEM_RISCO)

df = df_all[df_all["ano"].isin(anos) & df_all["mes"].isin(meses) & df_all["regiao"].isin(regioes)
            & df_all["uf"].isin(ufs) & df_all["modalidade_credito"].isin(mods)
            & df_all["risco_credito"].isin(riscos)]

st.title("💳 Sistema Financeiro e Crédito no Brasil (2015–2024)")
st.caption("Projeto G2 · Tema 28 · Base **simulada**: os resultados descrevem esta base, não o mercado real.")

if df.empty:
    st.warning("Nenhum registro para a combinação de filtros escolhida. Ajuste os filtros na barra lateral.")
    st.stop()

sb.divider()
sb.caption(f"{len(df):,} de {len(df_all):,} registros selecionados".replace(",", "."))
sb.download_button("⬇️ Baixar dados filtrados (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                   "dados_filtrados.csv", "text/csv")

# ---------- KPIs ----------
vol = df["valor_credito"].sum()
juros_s, juros_p = df["taxa_juros"].mean(), np.average(df["taxa_juros"], weights=df["valor_credito"])
inad_s, inad_p = df["inadimplencia_percentual"].mean(), np.average(df["inadimplencia_percentual"], weights=df["valor_credito"])
mod_g = df.groupby("modalidade_credito", observed=True)["valor_credito"].sum()
reg_g = df.groupby("regiao", observed=True)["valor_credito"].sum()

k = st.columns(3)
k[0].metric("Volume total de crédito", fmt_moeda(vol))
k[1].metric("Taxa média de juros", f"{fmt_num(juros_s)}%", help=f"Média ponderada pelo valor: {fmt_num(juros_p)}%")
k[2].metric("Inadimplência média", f"{fmt_num(inad_s)}%", help=f"Média ponderada pelo valor: {fmt_num(inad_p)}%")
k = st.columns(3)
k[0].metric("Modalidade mais utilizada", mod_g.idxmax(), help="Critério: maior volume de crédito")
k[1].metric("Região com maior crédito", reg_g.idxmax(), help=f"{reg_g.max() / vol:.1%} do volume filtrado")
k[2].metric("Prazo médio de pagamento", f"{fmt_num(df['prazo_medio_pagamento'].mean(), 1)} dias")

tabs = st.tabs(["📈 Evolução", "💳 Modalidades", "🗺️ Regiões", "🔥 Heatmap",
                "🎯 Juros × Inadimplência", "📋 Tabela dinâmica", "📝 Conclusão"])

# ---------- 1. Evolução ----------
with tabs[0]:
    mensal = df.groupby("data", as_index=False).agg(volume=("valor_credito", "sum"))
    mensal["volume_mi"] = mensal["volume"] / 1e6
    fig = go.Figure(go.Scatter(x=mensal["data"], y=mensal["volume_mi"], mode="lines", name="Volume mensal",
                               line=dict(width=1.5, color="#9bb7d4")))
    if len(mensal) >= 12:
        fig.add_trace(go.Scatter(x=mensal["data"], y=mensal["volume_mi"].rolling(12).mean(), mode="lines",
                                 name="Média móvel (12 pontos)", line=dict(width=3, color=AZUL)))
    fig.update_layout(title="Volume mensal de crédito", yaxis_title="R$ milhões", hovermode="x unified")
    mostrar(fig)

    anual = df.groupby("ano", as_index=False).agg(volume=("valor_credito", "sum"))
    anual["variacao"] = anual["volume"].pct_change() * 100
    fig = px.bar(anual, x="ano", y=anual["volume"] / 1e9, labels={"y": "R$ bilhões", "ano": ""},
                 text=anual["variacao"].map(lambda v: "" if pd.isna(v) else f"{v:+.1f}%"),
                 title="Volume anual (rótulo = variação sobre o ano anterior)")
    fig.update_xaxes(type="category")
    fig.update_traces(textposition="outside", marker_color=AZUL)
    mostrar(fig)

    if len(anual) > 1:
        total = anual["volume"].iloc[-1] / anual["volume"].iloc[0] - 1
        mx, mn = anual.loc[anual["variacao"].idxmax()], anual.loc[anual["variacao"].idxmin()]
        st.info(f"**Leitura:** de {anual['ano'].iloc[0]} a {anual['ano'].iloc[-1]} o volume variou **{total:+.1%}**. "
                f"Maior alta anual: **{int(mx['ano'])} ({mx['variacao']:+.1f}%)**; maior queda: **{int(mn['ano'])} "
                f"({mn['variacao']:+.1f}%)**. Com meses ou UFs filtrados, compare os anos com cautela.")
    else:
        st.info("**Leitura:** selecione mais de um ano para ver a variação.")

# ---------- 2. Modalidades ----------
with tabs[1]:
    mod = resumo(df, "modalidade_credito").sort_values("volume")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(mod, x=mod["volume"] / 1e9, y=mod.index, orientation="h", text=(mod["volume"] / 1e9).round(2),
                     labels={"x": "R$ bilhões", "y": ""}, title="Volume por modalidade")
        fig.update_traces(marker_color=AZUL, textposition="outside")
        mostrar(fig)
    with c2:
        r = mod[["inad_pond", "juros_pond"]].reset_index().melt(id_vars="modalidade_credito")
        r["variable"] = r["variable"].map({"inad_pond": "Inadimplência pond. (%)", "juros_pond": "Juros pond. (%)"})
        fig = px.bar(r, x="modalidade_credito", y="value", color="variable", barmode="group",
                     labels={"value": "%", "modalidade_credito": "", "variable": ""}, title="Risco e juros por modalidade")
        mostrar(fig)
    top, risc = mod["volume"].idxmax(), mod["inad_pond"].idxmax()
    st.info(f"**Leitura:** **{top}** lidera em volume ({fmt_moeda(mod['volume'].max())}) e **{risc}** tem a maior "
            f"inadimplência ponderada (**{fmt_num(mod['inad_pond'].max())}%**). A diferença entre a maior e a menor "
            f"é de **{fmt_num(mod['inad_pond'].max() - mod['inad_pond'].min())} p.p.**"
            + ("; diferenças pequenas não indicam, por si só, modalidades mais arriscadas." if mod['inad_pond'].max() - mod['inad_pond'].min() < 1
               else ". Com poucos registros filtrados, evite generalizar."))

# ---------- 3. Regiões ----------
with tabs[2]:
    reg = resumo(df, "regiao").sort_values("volume", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(reg, x=reg.index, y=reg["volume"] / 1e9, text=(reg["volume"] / 1e9).round(2),
                     labels={"y": "R$ bilhões", "x": ""}, title="Volume total por região")
        fig.update_traces(marker_color=AZUL, textposition="outside")
        mostrar(fig)
    with c2:
        fig = px.bar(reg, x=reg.index, y=reg["credito_medio"] / 1e6, text=(reg["credito_medio"] / 1e6).round(2),
                     labels={"y": "R$ milhões", "x": ""}, title="Crédito médio por operação")
        fig.update_traces(marker_color="#2e9e6b", textposition="outside")
        mostrar(fig)
    por_uf = resumo(df, "uf").sort_values("volume", ascending=False)
    fig = px.bar(por_uf, x=por_uf.index, y=por_uf["volume"] / por_uf["volume"].sum() * 100,
                 labels={"y": "% do volume filtrado", "x": "UF"}, title="Concentração do crédito por UF")
    fig.update_traces(marker_color=AZUL)
    mostrar(fig)
    st.info(f"**Leitura:** **{reg['volume'].idxmax()}** lidera com {reg['volume'].max() / reg['volume'].sum():.1%} do volume "
            f"e **{por_uf['volume'].idxmax()}** é a UF de maior participação. Atenção: o volume total depende do **número de "
            f"registros** de cada região (de {int(reg['operacoes'].min())} a {int(reg['operacoes'].max())} operações). "
            f"O crédito médio por operação ({fmt_moeda(reg['credito_medio'].min())} a {fmt_moeda(reg['credito_medio'].max())}) "
            f"é uma comparação mais justa.")

# ---------- 4. Heatmap ----------
with tabs[3]:
    ind = st.radio("Indicador", ["Volume de crédito (R$ mi)", "Inadimplência média (%)", "Taxa de juros média (%)"], horizontal=True)
    col, agg, esc, fmt = {"V": ("valor_credito", "sum", "Blues", ".0f"), "I": ("inadimplencia_percentual", "mean", "Reds", ".1f"),
                          "T": ("taxa_juros", "mean", "Purples", ".1f")}[ind[0]]
    pv = df.pivot_table(index="ano", columns="mes", values=col, aggfunc=agg)
    if col == "valor_credito":
        pv = pv / 1e6
    fig = px.imshow(pv, x=[MESES[m - 1] for m in pv.columns], y=[str(a) for a in pv.index], aspect="auto",
                    color_continuous_scale=esc, text_auto=fmt, labels=dict(x="Mês", y="Ano", color=ind),
                    title=f"Heatmap por ano e mês: {ind}")
    mostrar(fig)
    tot = df.groupby("mes")["valor_credito"].sum()
    st.info(f"**Leitura:** no volume acumulado, **{MESES[tot.idxmax() - 1]}** é o mês mais forte e **{MESES[tot.idxmin() - 1]}** "
            f"o mais fraco. Só é sazonalidade se o padrão se repetir ano após ano: confira se as células mais escuras "
            f"mudam de posição entre as linhas.")

# ---------- 5. Juros x inadimplência ----------
with tabs[4]:
    r, p = correlacao(df)
    fig = px.scatter(df, x="taxa_juros", y="inadimplencia_percentual", color="risco_credito", opacity=0.4,
                     color_discrete_map=COR_RISCO, category_orders={"risco_credito": ORDEM_RISCO},
                     labels={"taxa_juros": "Taxa de juros (%)", "inadimplencia_percentual": "Inadimplência (%)", "risco_credito": "Risco"},
                     title="Juros × inadimplência")
    if r is not None:
        a, b = np.polyfit(df["taxa_juros"], df["inadimplencia_percentual"], 1)
        xs = np.linspace(df["taxa_juros"].min(), df["taxa_juros"].max(), 50)
        fig.add_trace(go.Scatter(x=xs, y=a * xs + b, mode="lines", name="Tendência linear", line=dict(color="black", width=3)))
    mostrar(fig)
    c1, c2 = st.columns(2)
    with c1:
        faixa = df.groupby("faixa_juros", observed=True)["inadimplencia_percentual"].mean().reset_index()
        fig = px.bar(faixa, x="faixa_juros", y="inadimplencia_percentual", text=faixa["inadimplencia_percentual"].round(2),
                     labels={"inadimplencia_percentual": "Inadimplência média (%)", "faixa_juros": "Faixa de juros"},
                     title="Inadimplência média por faixa de juros")
        fig.update_traces(marker_color=VERMELHO, textposition="outside")
        mostrar(fig)
    with c2:
        rk = df.groupby("risco_credito", observed=True)["inadimplencia_percentual"].mean().reset_index()
        fig = px.bar(rk, x="risco_credito", y="inadimplencia_percentual", color="risco_credito", color_discrete_map=COR_RISCO,
                     text=rk["inadimplencia_percentual"].round(2), title="Inadimplência média por classe de risco",
                     labels={"inadimplencia_percentual": "Inadimplência média (%)", "risco_credito": "Risco"})
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        mostrar(fig)
    if r is None:
        st.info("**Leitura:** poucos dados para calcular a correlação com os filtros atuais.")
    else:
        st.info(f"**Leitura:** correlação de Pearson **r = {r:.3f}** (p ≈ {p:.2f}), relação **{forca(r)}**. "
                f"{'Os dados não sustentam a ideia de que juros maiores levam a mais inadimplência.' if abs(r) < 0.1 else 'Há alguma associação, mas correlação não prova causalidade.'} "
                f"Se a inadimplência for parecida entre as classes de risco, a classificação discrimina pouco o risco observado.")

# ---------- 6. Tabela dinâmica ----------
with tabs[5]:
    DIM = {"Região": "regiao", "UF": "uf", "Modalidade": "modalidade_credito", "Setor": "setor_economico",
           "Risco": "risco_credito", "Ano": "ano", "Faixa de juros": "faixa_juros"}
    MET = {"Valor do crédito (R$)": "valor_credito", "Taxa de juros (%)": "taxa_juros",
           "Inadimplência (%)": "inadimplencia_percentual", "Clientes": "quantidade_clientes",
           "Prazo médio (dias)": "prazo_medio_pagamento"}
    AGG = {"Soma": "sum", "Média": "mean", "Contagem": "count"}
    c = st.columns(4)
    li = c[0].selectbox("Linhas", list(DIM), index=0)
    co = c[1].selectbox("Colunas", list(DIM), index=2)
    me = c[2].selectbox("Valor", list(MET), index=0)
    ag = c[3].selectbox("Agregação", list(AGG), index=0)
    if li == co:
        st.warning("Escolha dimensões diferentes para linhas e colunas.")
    else:
        pt = df.pivot_table(index=DIM[li], columns=DIM[co], values=MET[me], aggfunc=AGG[ag],
                            observed=True, margins=True, margins_name="Total")
        tabela(pt.round(2))
        st.caption(f"{ag} de {me}, por {li.lower()} × {co.lower()}, nos dados filtrados.")

# ---------- 7. Conclusão ----------
with tabs[6]:
    reg = resumo(df, "regiao")
    setor = resumo(df, "setor_economico")
    st.subheader("Conclusão executiva (dados filtrados)")
    linhas = [
        f"**Escala:** {fmt_moeda(vol)} em {fmt_num(len(df), 0)} operações, com juros médios de {fmt_num(juros_s)}% e inadimplência média de {fmt_num(inad_s)}%.",
        f"**Geografia:** {reg['volume'].idxmax()} concentra {reg['volume'].max() / reg['volume'].sum():.1%} do volume; "
        f"o crédito médio por operação varia pouco entre regiões.",
        f"**Setores:** {setor['inad_pond'].idxmax()} tem a maior inadimplência ({fmt_num(setor['inad_pond'].max())}%) e "
        f"{setor['inad_pond'].idxmin()} a menor ({fmt_num(setor['inad_pond'].min())}%).",
    ]
    r, p = correlacao(df)
    if r is not None:
        linhas.append(f"**Risco:** a correlação entre juros e inadimplência é {forca(r)} (r = {r:.3f}).")
    st.markdown("\n".join(f"- {l}" for l in linhas))
    st.markdown("""
**Considerações gerais (base completa)**

- O crédito está **estável** ao longo de 2015–2024 (~R$ 2,2 bi por ano), sem tendência clara nem sazonalidade evidente.
- **Juros e inadimplência não se relacionam** (r ≈ −0,01), e a classificação de risco quase não distingue a inadimplência observada.
- O **Sudeste** lidera em volume, em grande parte por ter mais registros.

**Limitações:** base simulada, com variáveis independentes e distribuição uniforme; cobertura de 20 das 27 UFs; prazo assumido em dias.
""")
