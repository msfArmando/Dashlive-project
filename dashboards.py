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
atendimentoInput = ""

query = """
SELECT * FROM DASHBOARD_APROVACOESCAMILA
"""
queryItemsStatic = """
SELECT * FROM DASHLIVE_ITEMSSTATIC
"""
queryItemsN8N = """
SELECT * FROM DASHLIVE_N8N_POSTGRES
"""

dataset = pd.read_sql(query, engine)
datasetItemStatic = pd.read_sql(queryItemsStatic, engine)
dataSetItemsN8N = pd.read_sql(queryItemsN8N, engine)

minDate = min(dataset["ABERTURA_ATENDIMENTO"])
maxDate = max(dataset["ABERTURA_ATENDIMENTO"])

if "selected_date_range" not in st.session_state:
    st.session_state.selected_date_range = (minDate, maxDate)

if "temp_date_range" not in st.session_state:
    st.session_state.temp_date_range = (minDate, maxDate)

col1, col2, col3 = st.columns(3)
with col2:
    st.session_state.temp_date_range = st.date_input(
        "Escolha a data de início e fim do atendimento",
        value=st.session_state.selected_date_range,
        min_value=minDate,
        max_value=maxDate,
        format="DD/MM/YYYY"
    )

with col3:
    if st.button("Atualizar"):
        st.session_state.selected_date_range = st.session_state.temp_date_range

        datefilterN8N = st.session_state.selected_date_range

        dataSetItemsN8N = dataSetItemsN8N[
        (dataSetItemsN8N["ABERTURA_ATENDIMENTO"] >= pd.to_datetime(datefilterN8N[0])) &
        (dataSetItemsN8N["ABERTURA_ATENDIMENTO"] <= pd.to_datetime(datefilterN8N[1]))
        ]

        formatted_lines = [
        f"Coligada: {row['COLIGADA']} | Filial: {row['FILIAL']} | Atendimento: {row['CODIGO_ATENDIMENTO']} | Data do Atendimento: {row['ABERTURA_ATENDIMENTO'].date()} | Etapa do atendimento: {row['ETAPA_ATUAL']} | Status do atendimento: {row['STATUS_DO_ATENDIMENTO']} | Diretor responsável: {row['DIRETOR']} | Identificador Ordem de Compra: {[row['IDENTIFICADOR_ORDEM_DE_COMPRA']]} | Identificador Solicitação de Compra: {row['IDENTIFICADOR_SOLICITACAO_DE_COMPRA']} | Descrição do movimento: {row['OBSERVACAO_MOVIMENTO']} | Centro de Custo: {row['CENTRO_DE_CUSTO']} | Solicitante: {row['SOLICITANTE']} | Item/produto do movimento: {row['ITEM']} | Preço do Item: R$ {row['PRECO_ITEM']}"
        for _, row in dataSetItemsN8N.iterrows()
        ]

        webhook_url = "https://n8n.grupounibra.com/webhook/7f29ba26-2f5c-4ffc-9632-86c939ceac5e"

        txt_file = "dataset_formatado.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for line in formatted_lines:
                f.write(line + "\n")

        with open(txt_file, "rb") as f:
            files = {
                "file": ("dataset_formatado.txt", f, "text/txt")
            }
            header = {
                "user_id": "11063139414"
            }
            response = requests.post(
                webhook_url,
                headers=header,
                files=files,
                auth=HTTPBasicAuth("dashlive", "dashlive2025")  # suas credenciais
            )
        
        print("Status:", response.status_code)
        print("Resposta:", response.text)



datefilter = st.session_state.selected_date_range

dataset = dataset[
    (dataset["ABERTURA_ATENDIMENTO"] >= pd.to_datetime(datefilter[0])) &
    (dataset["ABERTURA_ATENDIMENTO"] <= pd.to_datetime(datefilter[1]))
]

datasetItemStatic = datasetItemStatic[
    (datasetItemStatic["ABERTURA_ATENDIMENTO"] >= pd.to_datetime(datefilter[0])) &
    (datasetItemStatic["ABERTURA_ATENDIMENTO"] <= pd.to_datetime(datefilter[1]))
]



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
            "CODIGO_ATENDIMENTO": st.column_config.NumberColumn(
                "CODIGO_ATENDIMENTO",
                format="%d",
            ),
            "IDENTIFICADOR_ORDEM_DE_COMPRA": st.column_config.NumberColumn(
                "IDENTIFICADOR_ORDEM_DE_COMPRA",
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

atend_count = dataset.groupby("CENTRO_DE_CUSTO")["CODIGO_ATENDIMENTO"].nunique().reset_index(name="Atendimentos")
fig_date = px.bar(atend_count, x="Atendimentos", y="CENTRO_DE_CUSTO", title="Atendimentos por centro de custo")

status_count = dataset.groupby("ETAPA_ATUAL")["CODIGO_ATENDIMENTO"].nunique().reset_index(name="Atendimentos")
fig_pie = px.pie(status_count, values="Atendimentos", names="ETAPA_ATUAL", title="Atendimentos por etapa")

col6.plotly_chart(fig_date)
col7.plotly_chart(fig_pie)

datasetItemStatic["ABERTURA_ATENDIMENTO"] = pd.to_datetime(datasetItemStatic["ABERTURA_ATENDIMENTO"])

datasetItemStatic = datasetItemStatic.sort_values(by="ABERTURA_ATENDIMENTO")

fig_line = px.line(datasetItemStatic, x="ABERTURA_ATENDIMENTO", y="PRECO_ITEM", color="COLIGADA",title="VARIAÇÃO DO VALOR TOTAL DOS ITENS APROVADOS AO LONGO DO TEMPO", labels={"ABERTURA_ATENDIMENTO": "Data do Atendimento", "PRECO_ITEM": "Valor Total (R$)"}, markers=True, hover_data=["CODIGO_ATENDIMENTO"])

col8  = st.columns(1)[0]

col8.plotly_chart(fig_line)