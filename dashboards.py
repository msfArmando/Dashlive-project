from dbcred import DbConnect as db
from sqlalchemy import create_engine
import urllib
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.animation import FuncAnimation
import requests
from requests.auth import HTTPBasicAuth
import os

pd.set_option("styler.render.max_elements", 999999)
st.set_page_config(layout="wide")

params = urllib.parse.quote_plus(
    f"DRIVER={db.driver};"
    f"SERVER={db.server}"
    f"DATABASE={db.database}"
    f"UID={db.UID}"
    f"PWD={db.PWD}"
)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

codAtendimento = ""

query = """
SELECT * FROM DASHBOARD_APROVACOESCAMILA
"""

dataset = pd.read_sql(query, engine)

minDate = min(dataset["ABERTURA_ATENDIMENTO"])
maxDate = max(dataset["ABERTURA_ATENDIMENTO"])

col1, col2, col3 = st.columns(3)
with col2:
    datefilter = st.date_input(
        "Escolha a data de inicio do atendimento",
        (minDate, maxDate),
        minDate,
        maxDate,
        format="DD/MM/YYYY"
    )

dataset = dataset[(dataset["ABERTURA_ATENDIMENTO"] >= pd.to_datetime(datefilter[0])) & (dataset["ABERTURA_ATENDIMENTO"] <= pd.to_datetime(datefilter[1]))]

col4, col5 = st.columns(2)

with col4:
    st.title("Tabela principal")
    st.data_editor(
        dataset,
        column_config={
            "ABERTURA_ATENDIMENTO": st.column_config.DateColumn(
                "ABERTURA_ATENDIMENTO",
                format="DD/MM/YYYY, h:mm a"
            ),
            "CODATENDIMENTO": st.column_config.NumberColumn(
                "CODATENDIMENTO",
                format="%d",
            ),
            "IDENTIFICADOR_MOV": st.column_config.NumberColumn(
                "IDENTIFICADOR_MOV",
                format="%d"
            )
        },
        hide_index=True,
    )

with col5:
    
    st.title("Tabela de itens")

    atendimentoInput = st.text_input("Digite o código de atendimento", "")

    queryItems = f"""
    SELECT 
    TPRODUTO.NOMEFANTASIA AS PRODUTO,
    TITMMOV.QUANTIDADE,
    TITMMOV.PRECOUNITARIO AS PRECO_ITEM,
    TITMMOV.CODUND AS UNIDADE

    FROM TMOV

    INNER JOIN TITMMOV (NOLOCK) ON
    TITMMOV.IDMOV = TMOV.IDMOV AND
    TITMMOV.CODCOLIGADA = TMOV.CODCOLIGADA

    INNER JOIN TMOVATEND (NOLOCK) ON
    TMOVATEND.CODCOLIGADA = TMOV.CODCOLIGADA AND
    TMOVATEND.IDMOV = TMOV.IDMOV

    INNER JOIN TPRODUTO (NOLOCK) ON
    TPRODUTO.IDPRD = TITMMOV.IDPRD AND
    TPRODUTO.CODCOLPRD = TITMMOV.CODCOLIGADA

    WHERE TMOVATEND.CODATENDIMENTO = '{atendimentoInput}'
    """

    datasetItem = pd.read_sql(queryItems, engine)

    st.data_editor(
        datasetItem
    )


col6, col7  = st.columns(2)

atend_count = dataset.groupby("CENTRO_DE_CUSTO")["CODATENDIMENTO"].nunique().reset_index(name="Atendimentos")
fig_date = px.bar(atend_count, x="Atendimentos", y="CENTRO_DE_CUSTO", title="Atendimentos por centro de custo")

status_count = dataset.groupby("ETAPA_ATUAL")["CODATENDIMENTO"].nunique().reset_index(name="Atendimentos")
fig_pie = px.pie(status_count, values="Atendimentos", names="ETAPA_ATUAL", title="Atendimentos por etapa")

col6.plotly_chart(fig_date)
col7.plotly_chart(fig_pie)

queryItemsStatic = """
SELECT
    HATENDIMENTOBASE.CODATENDIMENTO AS ATENDIMENTO,
    HATENDIMENTOBASE.ABERTURA AS ABERTURA_ATENDIMENTO,
    CASE WHEN TITMMOV.QUANTIDADE <> 0 THEN
         SUM(TITMMOV.QUANTIDADE * TITMMOV.PRECOUNITARIO)
    ELSE SUM(TITMMOV.PRECOUNITARIO) END AS PRECO_TOTAL_ITEM
FROM HATENDIMENTOBASE

INNER JOIN TMOVATEND (NOLOCK) ON
    TMOVATEND.CODCOLIGADA = HATENDIMENTOBASE.CODCOLIGADA AND
    TMOVATEND.CODATENDIMENTO = HATENDIMENTOBASE.CODATENDIMENTO

INNER JOIN TMOV (NOLOCK) ON
    TMOV.CODCOLIGADA = TMOVATEND.CODCOLIGADA AND
    TMOV.IDMOV = TMOVATEND.IDMOV

INNER JOIN TITMMOV (NOLOCK) ON
    TITMMOV.CODCOLIGADA = TMOV.CODCOLIGADA AND
    TITMMOV.IDMOV = TMOV.IDMOV

-- joins adicionais mantidos conforme necessidade da regra
INNER JOIN TPRODUTO (NOLOCK) ON
    TPRODUTO.IDPRD = TITMMOV.IDPRD AND
    TPRODUTO.CODCOLPRD = TITMMOV.CODCOLIGADA

INNER JOIN TTMV (NOLOCK) ON
    TTMV.CODTMV = TMOV.CODTMV

INNER JOIN HTAREFA ON 
    HATENDIMENTOBASE.CODCOLIGADA = HTAREFA.CODCOLIGADA AND
    HATENDIMENTOBASE.CODTIPOATENDIMENTO = HTAREFA.CODTIPOATENDIMENTO AND
    HATENDIMENTOBASE.CODTAREFA = HTAREFA.CODTAREFA

INNER JOIN TMOVHISTORICO ON
    TMOVHISTORICO.IDMOV = TMOV.IDMOV AND
    TMOVHISTORICO.CODCOLIGADA = TMOV.CODCOLIGADA

INNER JOIN GCCUSTO ON
    GCCUSTO.CODCCUSTO = TMOV.CODCCUSTO AND
    GCCUSTO.CODCOLIGADA = TMOV.CODCOLIGADA

INNER JOIN TMOVCOMPL ON
    TMOVCOMPL.IDMOV = TMOV.IDMOV AND
    TMOVCOMPL.CODCOLIGADA = TMOV.CODCOLIGADA

INNER JOIN GCONSIST GCONSISTDIRECAO ON
    GCONSISTDIRECAO.CODCLIENTE = TMOVCOMPL.CODDIRECAO AND
    GCONSISTDIRECAO.CODTABELA = 'CODDIRECAO'

INNER JOIN GFILIAL (NOLOCK) ON
    GFILIAL.CODCOLIGADA = TMOV.CODCOLIGADA AND
    GFILIAL.CODFILIAL = TMOV.CODFILIAL

WHERE 
    TMOV.CODCOLIGADA = '1' AND 
    TMOV.CODTMV IN (
        '1.1.60', '1.1.75', '1.1.85', '1.1.91', '1.1.92', '1.1.93', '1.1.94'
    ) AND 
    HATENDIMENTOBASE.CODSTATUS = 'F'

GROUP BY
    HATENDIMENTOBASE.CODATENDIMENTO,
    HATENDIMENTOBASE.ABERTURA,
    TITMMOV.QUANTIDADE
"""

datasetItemStatic = pd.read_sql(queryItemsStatic, engine)

datasetItemStatic["ABERTURA_ATENDIMENTO"] = pd.to_datetime(datasetItemStatic["ABERTURA_ATENDIMENTO"])

datasetItemStatic["PRECO_TOTAL_ITEM"] = datasetItemStatic["PRECO_TOTAL_ITEM"].apply(lambda x: format(float(x),".2f"))

datasetItemStatic = datasetItemStatic[(datasetItemStatic["ABERTURA_ATENDIMENTO"] >= pd.to_datetime(datefilter[0])) & (datasetItemStatic["ABERTURA_ATENDIMENTO"] <= pd.to_datetime(datefilter[1]))]

fig_line = px.line(datasetItemStatic, x="ABERTURA_ATENDIMENTO", y="PRECO_TOTAL_ITEM", title="VARIAÇÃO DO VALOR TOTAL DOS ITENS APROVADOS AO LONGO DO TEMPO", labels={"ABERTURA_ATENDIMENTO": "Data do Atendimento", "PRECO_TOTAL_ITEM": "Valor Total (R$)"}, markers=True, hover_data=["ATENDIMENTO"])

col8  = st.columns(1)[0]

col8.plotly_chart(fig_line)

# new_file = "dataset.csv"
# datasetItemStatic.to_csv(new_file, index=False)

# webhook_url = "https://n8n.grupounibra.com/webhook-test/7f29ba26-2f5c-4ffc-9632-86c939ceac5e"

# with open(new_file, "rb") as f:
#     files = {
#         "file": ("dataset.csv", f, "text/csv")
#     }
#     response = requests.post(
#         webhook_url,
#         files=files,
#         auth=HTTPBasicAuth("dashlive", "dashlive2025")  # suas credenciais
#     )


formatted_lines = [
    f"Atendimento: {row['ATENDIMENTO']} | Data do Atendimento: {row['ABERTURA_ATENDIMENTO'].date()} | Preço do Item: R$ {row['PRECO_TOTAL_ITEM']}"
    for _, row in datasetItemStatic.iterrows()
]

webhook_url = "https://n8n.grupounibra.com/webhook-test/7f29ba26-2f5c-4ffc-9632-86c939ceac5e"

txt_file = "dataset_formatado.txt"
with open(txt_file, "w", encoding="utf-8") as f:
    for line in formatted_lines:
        f.write(line + "\n")

with open(txt_file, "rb") as f:
    files = {
        "file": ("dataset_formatado.txt", f, "text/txt")
    }
    response = requests.post(
        webhook_url,
        files=files,
        auth=HTTPBasicAuth("dashlive", "dashlive2025")  # suas credenciais
    )

print("Status:", response.status_code)
print("Resposta:", response.text)
