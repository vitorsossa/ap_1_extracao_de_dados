import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(layout="wide")
st.title("📈 Evolução de Vencimentos (CDBs/LFs)")

df = st.session_state.get("df")

if df is not None and not df.empty:
    # Identificar colunas de data e valor
    cols_venc = [c for c in df.columns if "DT_VENC" in c.upper() or "DATA_VENC" in c.upper()]
    cols_valor = [c for c in df.columns if "VL_MERC" in c.upper()]
    
    if not cols_venc or not cols_valor:
        st.error("Colunas de vencimento ou valor não encontradas.")
    else:
        col_data = cols_venc[0]
        col_valor = cols_valor[0]

        # Filtro Master e Sofisa
        df_venc = df.copy()
        df_venc['Grupo'] = None
        if 'IS_MASTER' in df_venc.columns:
            df_venc.loc[df_venc['IS_MASTER'] == True, 'Grupo'] = 'BANCO MASTER'
        if 'IS_SOFISA' in df_venc.columns:
            df_venc.loc[df_venc['IS_SOFISA'] == True, 'Grupo'] = 'BANCO SOFISA'
        
        df_venc = df_venc.dropna(subset=['Grupo'])

        # Tratar datas
        df_venc[col_data] = pd.to_datetime(df_venc[col_data], errors='coerce')
        df_venc = df_venc.dropna(subset=[col_data])

        # Janela Temporal (Abr/25 a Mar/26) conforme solicitado
        df_janela = df_venc[(df_venc[col_data] >= '2025-04-01') & (df_venc[col_data] <= '2026-03-31')]

        if not df_janela.empty:
            df_linha = df_janela.groupby(['Grupo', pd.Grouper(key=col_data, freq='MS')])[col_valor].sum().reset_index()

            fig = px.line(
                df_linha, x=col_data, y=col_valor, color='Grupo', markers=True,
                color_discrete_map={'BANCO MASTER': '#FFD700', 'BANCO SOFISA': '#005DAA'},
                title="Projeção de Saída de Caixa por Vencimento"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("Vencimentos Master", f"R$ {df_janela[df_janela['Grupo']=='BANCO MASTER'][col_valor].sum():,.2f}")
            c2.metric("Vencimentos Sofisa", f"R$ {df_janela[df_janela['Grupo']=='BANCO SOFISA'][col_valor].sum():,.2f}")
        else:
            st.warning("Não há vencimentos previstos para Master/Sofisa entre Abr/25 e Mar/26.")
