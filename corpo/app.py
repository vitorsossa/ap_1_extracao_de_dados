import streamlit as st
import pandas as pd
import os
from utils import carregar_dados

# Configurações de persistência
DB_FILE = "base_consolidada.parquet"

st.set_page_config(page_title="Análise Banco Master vs Sofisa", layout="wide")

# Função para carregar a base salva
def carregar_base_salva():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_parquet(DB_FILE)
        except Exception:
            return None
    return None

# Inicialização do Estado (Session State)
if "df" not in st.session_state:
    st.session_state["df"] = carregar_base_salva()

st.title("📊 Pipeline de Dados: Master vs Sofisa")

# Sidebar para novos uploads
with st.sidebar:
    st.header("⚙️ Configurações")
    novos_arquivos = st.file_uploader("Adicionar novos ZIPs (CDA)", type="zip", accept_multiple_files=True)
    
    if novos_arquivos:
        with st.spinner("Processando e consolidando dados..."):
            df_novo = carregar_dados(novos_arquivos)
            
            if st.session_state["df"] is not None:
                # Concatenar e remover duplicados
                df_final = pd.concat([st.session_state["df"], df_novo], ignore_index=True).drop_duplicates()
            else:
                df_final = df_novo
            
            # SALVAMENTO FORÇADO
            df_final.to_parquet(DB_FILE, index=False)
            st.session_state["df"] = df_final
            st.success("Dados atualizados com sucesso!")
            st.rerun() # Força a atualização da página para ler as novas colunas

    if st.button("🗑️ Resetar Base de Dados"):
        if os.path.exists(DB_FILE): 
            os.remove(DB_FILE)
        st.session_state["df"] = None
        st.rerun()

# --- ÁREA DE EXIBIÇÃO (LÓGICA COMBINADA E SEGURA) ---
df = st.session_state["df"]

if df is not None and not df.empty:
    # 1. Verificação de Segurança (Garante que as colunas existem no DF)
    if 'IS_MASTER' not in df.columns:
        df['IS_MASTER'] = False
    if 'IS_SOFISA' not in df.columns:
        df['IS_SOFISA'] = False

    # 2. Filtros
    master_df = df[df['IS_MASTER'] == True]
    sofisa_df = df[df['IS_SOFISA'] == True]

    # 3. Métricas em Colunas
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("Registros Master", f"{len(master_df):,}")
    
    with c2:
        st.metric("Registros Sofisa", f"{len(sofisa_df):,}")
    
    with c3:
        # Tenta somar o volume se a coluna existir
        col_v = [c for c in df.columns if "VL_MERC" in c.upper()]
        if col_v and not master_df.empty:
            vol_master = master_df[col_v[0]].sum()
            st.metric("Volume Master", f"R$ {vol_master:,.2f}")
        else:
            st.metric("Volume Master", "R$ 0,00")

    st.divider()
    
    # 4. Preview dos Dados
    st.subheader("🔍 Visualização dos Ativos (Top 100)")
    # Mostra os dois bancos juntos para comparação rápida
    df_preview = pd.concat([master_df, sofisa_df]).head(100)
    
    if not df_preview.empty:
        st.dataframe(df_preview, use_container_width=True)
    else:
        st.warning("Nenhum dado de Master ou Sofisa encontrado nos arquivos processados.")
else:
    st.info("👋 A base de dados está vazia ou foi resetada. Por favor, suba os arquivos ZIP na barra lateral.")
