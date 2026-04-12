import streamlit as st
import plotly.express as px
import pandas as pd

# Configuração da página
st.set_page_config(layout="wide")
st.title("📈 Evolução de Vencimentos: Abr/2025 a Mar/2026")

if "df" in st.session_state and st.session_state["df"] is not None:
    df = st.session_state["df"].copy()
    
    # 1. Identificação Segura de Colunas (Evita o erro de IndexError: list index out of range)
    cols_v_merc = [c for c in df.columns if "VL_MERC" in c.upper()]
    cols_venc = [c for c in df.columns if "DT_VENC" in c.upper() or "DATA_VENC" in c.upper()]
    
    if not cols_v_merc or not cols_venc:
        st.error("❌ Não foi possível encontrar as colunas de 'Valor de Mercado' ou 'Data de Vencimento' nos arquivos.")
    else:
        col_valor = cols_v_merc[0]
        col_data = cols_venc[0]

        # 2. Lógica de Classificação (Reutilizando a inteligência do utils.py)
        def classificar_restrito(row):
            if row.get('IS_MASTER') == True:
                return 'BANCO MASTER'
            
            # Busca Santander em colunas prováveis
            for c in ['EMISSOR', 'DENOM_SOCIAL', 'NM_FUNDO_CLASSE_SUBCLASSE_COTA']:
                if c in row.index and pd.notna(row[c]):
                    if 'SANTANDER' in str(row[c]).upper():
                        return 'SANTANDER'
            return None

        df['Grupo_Alvo'] = df.apply(classificar_restrito, axis=1)
        df_filtrado = df.dropna(subset=['Grupo_Alvo']).copy()

        # 3. Tratamento de Datas e Janela Temporal
        # Convertendo para datetime (importante para o gráfico de linha)
        df_filtrado[col_data] = pd.to_datetime(df_filtrado[col_data], errors='coerce')
        df_filtrado = df_filtrado.dropna(subset=[col_data]) # Remove datas inválidas

        data_inicio = pd.Timestamp('2025-04-01')
        data_fim = pd.Timestamp('2026-03-31')
        
        df_janela = df_filtrado[
            (df_filtrado[col_data] >= data_inicio) & 
            (df_filtrado[col_data] <= data_fim)
        ].copy()

        if not df_janela.empty:
            # 4. Agrupamento mensal para suavizar a linha
            # O freq='MS' agrupa pelo primeiro dia do mês
            df_linha = df_janela.groupby(['Grupo_Alvo', pd.Grouper(key=col_data, freq='MS')]).agg({
                col_valor: 'sum'
            }).reset_index()

            # 5. Geração do Gráfico de Evolução (Linha)
            fig = px.line(
                df_linha, 
                x=col_data, 
                y=col_valor, 
                color='Grupo_Alvo',
                markers=True,
                title="Projeção de Fluxo de Caixa (Vencimentos de CDBs/LFs)",
                labels={col_valor: 'Volume (R$)', col_data: 'Mês/Ano de Vencimento'},
                color_discrete_map={'BANCO MASTER': '#FFD700', 'SANTANDER': '#EC0000'}
            )

            fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
            fig.update_layout(hovermode="x unified", legend_title_text='Instituição')
            
            st.plotly_chart(fig, use_container_width=True)

            # 6. Painel de Métricas
            st.divider()
            c1, c2 = st.columns(2)
            
            val_master = df_janela[df_janela['Grupo_Alvo'] == 'BANCO MASTER'][col_valor].sum()
            val_santander = df_janela[df_janela['Grupo_Alvo'] == 'SANTANDER'][col_valor].sum()
            
            with c1:
                st.markdown("<h3 style='color:#FFD700'>Total Master no Período</h3>", unsafe_allow_html=True)
                st.metric("Volume Vencendo", f"R$ {val_master:,.2f}")
            
            with c2:
                st.markdown("<h3 style='color:#EC0000'>Total Santander no Período</h3>", unsafe_allow_html=True)
                st.metric("Volume Vencendo", f"R$ {val_santander:,.2f}")
                
        else:
            st.warning("⚠️ Nenhum vencimento do Master ou Santander encontrado entre Abr/25 e Mar/26.")

else:
    st.info("👋 Por favor, carregue os arquivos ZIP na página inicial para visualizar a evolução de vencimentos.")