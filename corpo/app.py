import streamlit as st
import pandas as pd
import os
from utils import carregar_dados

# Configurações de persistência
DB_FILE = "base_consolidada.parquet"

st.set_page_config(page_title="Análise Banco Master vs Sofisa", layout="wide")

# 1. Função de carregamento com cache para garantir que os dados não sumam no reload
@st.cache_data
def ler_arquivo_disco():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_parquet(DB_FILE)
        except Exception as e:
            st.error(f"Erro ao ler arquivo do disco: {e}")
            return None
    return None

# 2. Inicialização do Estado: Se o state estiver vazio, tenta recuperar do disco
if "df" not in st.session_state or st.session_state["df"] is None:
    st.session_state["df"] = ler_arquivo_disco()

st.title("📊 Pipeline de Dados: Master vs Sofisa")

# Sidebar para novos uploads
with st.sidebar:
    st.header("⚙️ Configurações")
    novos_arquivos = st.file_uploader("Adicionar novos ZIPs (CDA)", type="zip", accept_multiple_files=True)
    
    if novos_arquivos:
        # Gerar um ID único baseado nos arquivos selecionados para evitar loops
        id_atual = "".join([f"{f.name}{f.size}" for f in novos_arquivos])
        
        if st.session_state.get("ultimo_id_processado") != id_atual:
            with st.spinner("Processando e consolidando dados..."):
                df_novo = carregar_dados(novos_arquivos)
                
                if not df_novo.empty:
                    # Recupera o que já temos (no disco ou na memória)
                    df_atual = st.session_state["df"] if st.session_state["df"] is not None else ler_arquivo_disco()
                    
                    if df_atual is not None:
                        df_final = pd.concat([df_atual, df_novo], ignore_index=True).drop_duplicates()
                    else:
                        df_final = df_novo
                    
                    # SALVAMENTO FÍSICO NO DISCO
                    df_final.to_parquet(DB_FILE, index=False)
                    
                    # Atualiza a memória e limpa o cache para o próximo ciclo
                    st.session_state["df"] = df_final
                    st.session_state["ultimo_id_processado"] = id_atual
                    st.cache_data.clear() 
                    
                    st.success("Dados processados e salvos com sucesso!")
                    st.rerun()
                else:
                    st.error("Nenhum dado válido encontrado nos arquivos.")

    if st.button("🗑️ Resetar Base de Dados"):
        if os.path.exists(DB_FILE): 
            os.remove(DB_FILE)
        st.session_state["df"] = None
        st.session_state["ultimo_id_processado"] = None
        st.cache_data.clear()
        st.rerun()

# --- ÁREA DE EXIBIÇÃO ---
df = st.session_state["df"]

if df is not None and not df.empty:
    # Garante que as colunas de filtro existam para evitar KeyError
    if 'IS_MASTER' not in df.columns: df['IS_MASTER'] = False
    if 'IS_SOFISA' not in df.columns: df['IS_SOFISA'] = False

    # Filtros para métricas
    master_df = df[df['IS_MASTER'] == True]
    sofisa_df = df[df['IS_SOFISA'] == True]

    c1, c2, c3 = st.columns(3)
    c1.metric("Registros Master", f"{len(master_df):,}")
    c2.metric("Registros Sofisa", f"{len(sofisa_df):,}")
    
    # Cálculo de Volume Total (VL_MERC_POS_FINAL)
    col_v = [c for c in df.columns if "VL_MERC" in c.upper()]
    if col_v and not master_df.empty:
        vol_master = master_df[col_v[0]].sum()
        c3.metric("Volume Master", f"R$ {vol_master:,.2f}")
    else:
        c3.metric("Volume Master", "R$ 0,00")

    st.divider()
    st.subheader("🔍 Visualização dos Ativos (Master + Sofisa)")
    
    # Preview combinado dos dois bancos
    df_preview = pd.concat([master_df, sofisa_df]).head(100)
    
    if not df_preview.empty:
        st.dataframe(df_preview, use_container_width=True)
    else:
        st.warning("Nenhum registro identificado como Master ou Sofisa nos arquivos carregados.")
else:
    st.info("👋 A base de dados está vazia. Por favor, carregue os arquivos ZIP na barra lateral.")
