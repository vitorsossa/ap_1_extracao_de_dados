import streamlit as st
import plotly.express as px
import re
import pandas as pd

df = st.session_state.get("df")

if df is not None and not df.empty:
    # 1. Função interna para extrair a data e criar uma chave de ordenação
    def extrair_data_sort(nome):
        match = re.search(r'(\d{4})(\d{2})', str(nome))
        if match:
            ano, mes = match.groups()
            return f"{ano}{mes}", f"{mes}/{ano}"
        return "999999", nome

    # 2. Lógica de classificação robusta
    def classificar_duelo(row):
        # Primeiro checa o IS_MASTER que já criamos no utils.py
        if row.get('IS_MASTER') == True:
            return 'BANCO MASTER'
        
        # Procura Santander em qualquer coluna que possa ser o emissor
        for col in ['EMISSOR', 'DENOM_SOCIAL', 'NM_FUNDO_CLASSE_SUBCLASSE_COTA']:
            if col in row.index and pd.notna(row[col]):
                if 'SANTANDER' in str(row[col]).upper():
                    return 'SANTANDER'
        return None

    # Criamos as colunas de apoio
    df['Banco_Alvo'] = df.apply(classificar_duelo, axis=1)
    
    # Criamos a data de exibição e a chave de ordenação
    datas_processadas = df['arquivo_origem'].apply(extrair_data_sort)
    df['sort_key'] = [x[0] for x in datas_processadas]
    df['data_referencia'] = [x[1] for x in datas_processadas]
    
    # 3. Filtramos apenas os alvos e removemos nulos
    df_comp = df.dropna(subset=['Banco_Alvo']).copy()
    
    if not df_comp.empty:
        # Identifica a coluna de valor (VL_MERC_POS_FINAL ou similar)
        col_valor_lista = [c for c in df_comp.columns if "VL_MERC" in c.upper()]
        if not col_valor_lista:
            st.error("Coluna de valor (VL_MERC) não encontrada nos dados.")
        else:
            col_valor = col_valor_lista[0]

            # 4. AGRUPAMENTO: Somamos os valores por data e banco para o gráfico ficar limpo
            df_plot = df_comp.groupby(['sort_key', 'data_referencia', 'Banco_Alvo'])[col_valor].sum().reset_index()
            df_plot = df_plot.sort_values('sort_key')

            # 5. Gráfico de Barras Agrupadas
            fig = px.bar(
                df_plot, 
                x='data_referencia', 
                y=col_valor, 
                color='Banco_Alvo', 
                barmode='group',
                title="Duelo de Gigantes: Volume Master vs. Santander",
                color_discrete_map={
                    'BANCO MASTER': '#FFD700', 
                    'SANTANDER': '#EC0000'
                },
                labels={col_valor: 'Volume (R$)', 'data_referencia': 'Mês/Ano'}
            )
            
            # Garante a ordem cronológica correta no Eixo X
            fig.update_xaxes(type='category')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 6. Métricas formatadas
            total_master = df_comp[df_comp['Banco_Alvo'] == 'BANCO MASTER'][col_valor].sum()
            total_santander = df_comp[df_comp['Banco_Alvo'] == 'SANTANDER'][col_valor].sum()
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<h3 style='color:#FFD700'>BANCO MASTER</h3>", unsafe_allow_html=True)
                st.metric("Volume Total", f"R$ {total_master:,.2f}")
            with c2:
                st.markdown(f"<h3 style='color:#EC0000'>SANTANDER</h3>", unsafe_allow_html=True)
                st.metric("Volume Total", f"R$ {total_santander:,.2f}")
    else:
        st.warning("Nenhum dado do Banco Master ou Santander encontrado para gerar o gráfico.")