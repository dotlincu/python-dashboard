import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Função para carregar dados dos arquivos CSV
def fetch_data_from_csv():
    try:
        lancamentos_df = pd.read_csv("./data/lancamentos.csv")
        categorias_df = pd.read_csv("./data/categoria.csv")
        dre_df = pd.read_csv("./data/dre.csv")

        # Renomear as colunas para um padrão consistente
        lancamentos_df = lancamentos_df.rename(columns={'data.pagamento': 'data_pagamento', 'cod.categoria': 'cod_categoria'})
        categorias_df = categorias_df.rename(columns={'cod.categoria': 'cod_categoria', 'cod.dre': 'cod_dre'})
        dre_df = dre_df.rename(columns={'cod.dre': 'cod_dre'})

        return lancamentos_df, categorias_df, dre_df
    except FileNotFoundError as e:
        st.error(f"Erro: Arquivo CSV não encontrado. Por favor, verifique se todos os arquivos estão no diretório correto. Detalhes: {e}")
        return None, None, None

# Coletar e processar os dados dos CSVs
def process_data():
    lancamentos_df, categorias_df, dre_df = fetch_data_from_csv()
    
    if lancamentos_df is not None and categorias_df is not None and dre_df is not None:
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
    min_date = df['data_pagamento'].min().date()
    max_date = df['data_pagamento'].max().date()

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

    # Margens
    margem_bruta = (lucro_bruto / receita_liquida) * 100 if receita_liquida != 0 else 0
    margem_operacional = (resultado_operacional / receita_liquida) * 100 if receita_liquida != 0 else 0
    margem_liquida = (lucro_liquido / receita_liquida) * 100 if receita_liquida != 0 else 0

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
        "Lucro Líquido": lucro_liquido,
        "Margem Bruta (%)": margem_bruta,
        "Margem Operacional (%)": margem_operacional,
        "Margem Líquida (%)": margem_liquida,
    }

# Formatação dos valores
def format_value(value):
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:,.1f}M"
    elif value >= 1_000:
        return f"R$ {value / 1_000:,.1f}K"
    else:
        return f"R$ {value:,.2f}"

# Exibição dos indicadores no dashboard
def display_indicators(indicators):
    st.title("📊 Cálculo de DRE Completo")
    st.markdown("** Visão Geral dos Indicadores Financeiros**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Receita Bruta", format_value(indicators['Receita Bruta']))
    col2.metric("Deduções da Receita", format_value(indicators['Deduções da Receita']))
    col3.metric("Receita Líquida", format_value(indicators['Receita Líquida']))

    col1, col2, col3 = st.columns(3)
    col1.metric("Custos de Produtos", format_value(indicators['Custos de Produtos']))
    col2.metric("Lucro Bruto", format_value(indicators['Receita Líquida']))
    col3.metric("Despesas Variáveis", format_value(indicators['Despesas Variáveis']))

    col1, col2, col3 = st.columns(3)
    col1.metric("Margem de Contribuição", format_value(indicators['Margem de Contribuição']))
    col2.metric("Despesas Fixas", format_value(indicators['Despesas Fixas']))
    col3.metric("Resultado Operacional", format_value(indicators['Resultado Operacional']))

    col1, col2, col3 = st.columns(3)
    col1.metric("Impostos sobre Lucro", format_value(indicators['Impostos sobre Lucro']))
    col2.metric("Lucro Líquido", format_value(indicators['Lucro Líquido']))

    col1, col2, col3 = st.columns(3)
    col1.metric("Margem Bruta (%)", f"{indicators['Margem Bruta (%)']:,.2f}")
    col2.metric("Margem Operacional (%)", f"{indicators['Margem Operacional (%)']:,.2f}")
    col3.metric("Margem Líquida (%)", f"{indicators['Margem Líquida (%)']:,.2f}")
    
# Gráfico de Cascata (Waterfall)
def display_waterfall_chart(indicators):
    st.subheader("Evolução dos Resultados - Gráfico de Cascata")
    fig, ax, = plt.subplots(figsize=(12, 6))

    steps = [
        indicators['Receita Bruta'],
        -indicators['Deduções da Receita'],
        indicators['Receita Líquida'],
        -indicators['Custos de Produtos'],
        indicators['Lucro Bruto'],
        -indicators['Despesas Variáveis'],
        indicators['Margem de Contribuição'],
        -indicators['Despesas Fixas'],
        indicators['Resultado Operacional'],
        -indicators['Impostos sobre Lucro'],
        indicators['Lucro Líquido'],

        # "Margem Bruta (%)": margem_bruta,
        # "Margem Operacional (%)": margem_operacional,
        # "Margem Líquida (%)": margem_liquida,
    ]

    labels = [
        "Rec. Bruta",
        "Ded. Receita",
        "Rec. Líquida",
        "Custos Prod.",
        "Lucro Bruto",
        "Desp. Variáveis",        
        "Margem Cont.",        
        "Desp. Fixas",
        "Res. Operacional",        
        "Imp. Lucro",        
        "Lucro Líq.",

        # "Margem Bruta (%)",
        # "Margem Operacional (%)",
        # "Margem Líquida (%)",
    ]

    # Calcular as posições iniciais e finais de cada barra
    y_pos = [0]
    for step in steps[:-1]:
        y_pos.append(y_pos[-1] + step)
    
    # Cores para as barras: verde para positivo, vermelho para negativo
    colors = ['green' if x > 0 else 'red' for x in steps]
    colors[2] = 'lightgray'
    colors[4] = 'lightgray'
    colors[6] = 'lightgray'
    colors[8] = 'lightgray'
    colors[10] = 'dodgerblue'
    
    ax.bar(labels, steps, color=colors, bottom=[max(0, p) for p in y_pos], width=0.8)

    y_pos = [0]
    for step in steps[:-1]:
        y_pos.append(y_pos[-1] + step)
    
    for i in range(len(steps) - 1):
        ax.plot([i, i+1], [y_pos[i] + steps[i], y_pos[i] + steps[i]], color='black', linestyle='--')


    # ax.bar(range(len(steps)), steps, color=['green' if x > 0 else 'red' for x in steps])
    plt.xticks(rotation=45, ha='right')
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.ylabel('Valor (R$)')
    plt.title('Gráfico de Cascata do DRE')
    st.pyplot(fig)

# Main
def main():
    final_df = process_data()
    filtered_df = filter_data_by_date(final_df)
    indicators = calculate_indicators(filtered_df)
    display_indicators(indicators)

    # Chamando os gráficos separadamente
    display_waterfall_chart(indicators)
    # display_bar_chart(indicators)

    # Exibir DataFrame dos indicadores
    dre_df = pd.DataFrame([indicators])
    st.subheader("Tabela de Indicadores Financeiros")
    st.dataframe(dre_df)

    # # Adicionando barras de interação com o ChatGPT
    # st.subheader("Pergunte ao ChatGPT")
    # pergunta = st.text_input("Digite sua pergunta com base nos dados:", "")

    # # No trecho do main onde a pergunta é enviada
    # if st.button("Enviar pergunta"):

if __name__ == "__main__":
    main()