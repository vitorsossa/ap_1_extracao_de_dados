import streamlit as st
import plotly.express as px
import re
import pandas as pd

st.set_page_config(layout="wide")
df = st.session_state.get("df")

if df is not None and not df.empty:
    st.header("⚔️ Comparativo de Volume: Master vs Sofisa")
    
    # 1. Função para ordenar as datas (Ex: 07/2025)
    def extrair_data_sort(nome):
        match = re.search(r'(\d{4})(\d{2})', str(nome))
        if match:
            ano, mes = match.groups()
            return f"{ano}{mes}", f"{mes}/{ano}"
        return "999999", str(nome)

    # 2. Criar coluna de agrupamento baseada nas flags do utils.py
    df['Banco_Alvo'] = None
    if 'IS_MASTER' in df.columns:
        df.loc[df['IS_MASTER'] == True, 'Banco_Alvo'] = 'BANCO MASTER'
    if 'IS_SOFISA' in df.columns:
        df.loc[df['IS_SOFISA'] == True, 'Banco_Alvo'] = 'BANCO SOFISA'
    
    # Filtrar apenas as linhas que pertencem a um dos dois bancos
    df_comp = df.dropna(subset=['Banco_Alvo']).copy()
    
    if not df_comp.empty:
        col_valor = [c for c in df_comp.columns if "VL_MERC" in c.upper()][0]

        # Preparar datas
        datas_info = df_comp['arquivo_origem'].apply(extrair_data_sort)
        df_comp['sort_key'] = [x[0] for x in datas_info]
        df_comp['data_referencia'] = [x[1] for x in datas_info]

        # Agrupar para o gráfico
        df_plot = df_comp.groupby(['sort_key', 'data_referencia', 'Banco_Alvo'])[col_valor].sum().reset_index()
        df_plot = df_plot.sort_values('sort_key')

        # Gerar Gráfico
        fig = px.bar(
            df_plot, 
            x='data_referencia', 
            y=col_valor, 
            color='Banco_Alvo', 
            barmode='group',
            title="Duelo de Ativos: Master vs Sofisa",
            color_discrete_map={'BANCO MASTER': '#FFD700', 'BANCO SOFISA': '#005DAA'},
            labels={col_valor: 'Volume (R$)', 'data_referencia': 'Mês/Ano'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas
        c1, c2 = st.columns(2)
        v_master = df_comp[df_comp['Banco_Alvo'] == 'BANCO MASTER'][col_valor].sum()
        v_sofisa = df_comp[df_comp['Banco_Alvo'] == 'BANCO SOFISA'][col_valor].sum()
        c1.metric("Total Master", f"R$ {v_master:,.2f}")
        c2.metric("Total Sofisa", f"R$ {v_sofisa:,.2f}")
    else:
        st.warning("Nenhum dado encontrado para Master ou Sofisa na base atual.")
else:
    st.info("Carregue os dados na página principal primeiro.")
