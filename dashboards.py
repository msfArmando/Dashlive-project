from dbcred import DbConnect as db
from sqlalchemy import create_engine
import urllib
import pandas as pd
import pandas as pd
import streamlit as st
import plotly.express as px

params = urllib.parse.quote_plus(
    f"DRIVER={db.driver};"
    f"SERVER={db.server}"
    f"DATABASE={db.database}"
    f"UID={db.UID}"
    f"PWD={db.PWD}"
)
#Cria um dicionário usando o método quote_plus que decodifica caracteres especiais para que sejam aceitos em urls

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

query = """
SELECT * FROM HATENDIMENTOBASE
"""
#Cria uma string com a consulta específica para o banco de dados.

dataset = pd.read_sql(query, engine) #Realiza uma leitura do banco de dados usando esta consulta e retorna os valores como um dataset