import pandas as pd
import streamlit as st
from database import create_db_and_tables, get_session
from models import DRE, Categoria, Lancamentos
from sqlmodel import select

# OPÇÃO 1 - BANCO DE DADOS POSTGRES
# Inicializar o banco de dados e tabelas
create_db_and_tables()

# Função para carregar dados do banco de dados
def fetch_data():
    with get_session() as session:
        # Consultar todos os dados de cada tabela
        lancamentos = session.exec(select(Lancamentos)).all()
        categorias = session.exec(select(Categoria)).all()
        dre = session.exec(select(DRE)).all()

        # Convertendo os resultados para DataFrames
        lancamentos_df = pd.DataFrame([l.model_dump() for l in lancamentos])
        categorias_df = pd.DataFrame([c.model_dump() for c in categorias])
        dre_df = pd.DataFrame([d.model_dump() for d in dre])

        # Retornar os DataFrames ajustados
        return lancamentos_df, categorias_df, dre_df

# Coletar e processar os dados
lancamentos_df, categorias_df, dre_df = fetch_data()

def process_data():
    # Converter o 'data_pagamento' para datetime
    lancamentos_df['data_pagamento'] = pd.to_datetime(lancamentos_df['data_pagamento'], format='%Y-%m-%d')
    
    # Realizar o join entre lançamentos e categoria
    merged_df = pd.merge(lancamentos_df, categorias_df, left_on="cod_categoria", right_on="cod_categoria", how="left")

    # Realizar o join entre o resultado anterior e dre
    final_df = pd.merge(merged_df, dre_df, left_on="cod_dre", right_on="cod_dre", how="left")

    # Converter o 'valor' para float, substituindo vírgulas por pontos 
    final_df['valor'] = final_df['valor'].str.replace(',', '.').astype(float)

    # Converter o 'tipo_financeiro' para 
    final_df['tipo_financeiro'] = final_df['cod_categoria'].apply(lambda x: 'Receita' if x.startswith('l') else 'Despesa')

    return final_df

# Função para aplicar o filtro de data
def filter_data_by_date(df):
    min_date = df['data_pagamento'].min()
    max_date = df['data_pagamento'].max()

    start_date, end_date = st.sidebar.date_input(
        "Selecione o intervalo de datas",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date,
        key="date_filter"
    )

    filtered_df = df[(df['data_pagamento'] >= pd.to_datetime(start_date)) &
                     (df['data_pagamento'] <= pd.to_datetime(end_date))]
    
    return filtered_df

# Cálculo dos indicadores financeiros
def calculate_indicators(df):
    receita_bruta = df[df['tipo_financeiro'] == 'Receita']['valor'].sum()
    deducoes_receita = df[df['cod_dre'].isin([201, 202, 203])]['valor'].sum()
    receita_liquida = receita_bruta - deducoes_receita
    
    custo_produtos = df[df['cod_dre'].isin([401, 402])]['valor'].sum()
    lucro_bruto = receita_liquida - custo_produtos
    
    despesas_variaveis = df[df['cod_dre'].isin([601, 602, 603, 604])]['valor'].sum()
    margem_contribuicao = lucro_bruto - despesas_variaveis

    despesas_fixas = df[df['cod_dre'].isin([801, 802, 803, 804, 805])]['valor'].sum()
    resultado_operacional = margem_contribuicao - despesas_fixas

    impostos_sobre_lucro = df[df['cod_dre'].isin([1001, 1002, 1003])]['valor'].sum()
    lucro_liquido = resultado_operacional - impostos_sobre_lucro

    return {
        "Receita Bruta": receita_bruta,
        "Deduções da Receita": deducoes_receita,
        "Receita Líquida": receita_liquida,
        "Custos de Produtos": custo_produtos,
        "Lucro Bruto": lucro_bruto,
        "Despesas Variáveis": despesas_variaveis,
        "Margem de Contribuição": margem_contribuicao,
        "Despesas Fixas": despesas_fixas,
        "Resultado Operacional": resultado_operacional,
        "Impostos sobre Lucro": impostos_sobre_lucro,
        "Lucro Líquido": lucro_liquido
    }







