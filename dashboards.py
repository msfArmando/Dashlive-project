from dbcred import DbConnect as db
from sqlalchemy import create_engine
import datetime
import urllib
import pandas as pd
import pandas as pd
import streamlit as st
import plotly.express as px

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


col6, col7 = st.columns(2)
col8, col9 = st.columns(2)

atend_count = dataset.groupby("CENTRO_DE_CUSTO")["CODATENDIMENTO"].nunique().reset_index(name="Qtd_Atendimentos")
fig_date = px.bar(atend_count, x="Qtd_Atendimentos", y="CENTRO_DE_CUSTO", title="Atendimentos por centro de custo")
col6.plotly_chart(fig_date)