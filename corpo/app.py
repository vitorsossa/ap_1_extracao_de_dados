import streamlit as st
from utils import carregar_dados
import pandas as pd

st.set_page_config(page_title="Análise Banco Master", layout="wide")
st.title("📊 Monitoramento de Ativos: Banco Master")

# Função de cache para processar apenas quando os arquivos mudarem
@st.cache_data(show_spinner="Processando arquivos novos...")
def processar_arquivos(arquivos):
    df = carregar_dados(arquivos)
    
    if df.empty:
        return df

    # Tratamento de valores financeiros
    # Identifica colunas que começam com VL_ (Valor)
    cols_valor = [c for c in df.columns if "VL_" in c.upper()]
    for col in cols_valor:
        df[col] = (df[col].astype(str)
                   .str.replace('.', '', regex=False)
                   .str.replace(',', '.', regex=False))
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# Sidebar para Upload
uploaded_files = st.sidebar.file_uploader("Upload dos ZIPs (Arquivos CDA)", type="zip", accept_multiple_files=True)

# Lógica Automática de Processamento
if uploaded_files:
    # Se houver novos ficheiros, processa e guarda no session_state
    st.session_state["df"] = processar_arquivos(uploaded_files)
else:
    st.session_state["df"] = None

# --- Exibição dos Dados ---
df = st.session_state.get("df")

if df is not None and not df.empty:
    # Filtra as linhas identificadas como Banco Master pela lógica do utils.py
    master_df = df[df['IS_MASTER'] == True].copy()

    # Exibição de Métricas no Topo
    m1, m2, m3 = st.columns(3)
    m1.metric("Total de Linhas Lidas", f"{len(df):,}")
    m2.metric("Registros Banco Master", len(master_df))
    
    if not master_df.empty:
        # Tenta encontrar a coluna de Valor de Mercado
        col_v = [c for c in master_df.columns if "VL_MERC" in c.upper()]
        if col_v:
            total_master = master_df[col_v[0]].sum()
            m3.metric("Volume Total Master", f"R$ {total_master:,.2f}")
        
        st.success(f"Sucesso! Encontrámos ativos do Banco Master nos blocos processados.")
        
        # Seleção dinâmica de colunas para exibição (evita erro se a coluna não existir no bloco)
        colunas_desejadas = [
            'arquivo_origem', 'DT_COMPTC', 'EMISSOR', 'CNPJ_EMISSOR', 
            'DT_EMISSAO', 'DT_INI_VIGENCIA', 'DT_VENC', 'VL_MERC_POS_FINAL'
        ]
        colunas_existentes = [c for c in colunas_desejadas if c in master_df.columns]

        # Tabela com os dados do Master
        st.subheader("📋 Detalhamento de Ativos: Banco Master")
        st.dataframe(master_df[colunas_existentes], use_container_width=True)
        
        # Download dos dados filtrados
        csv = master_df.to_csv(index=False, sep=';', encoding='latin1')
        st.download_button("📥 Descarregar Tabela Master (CSV)", csv, "dados_master.csv", "text/csv")
    else:
        st.warning("⚠️ Ficheiros lidos com sucesso, mas o Banco Master (CNPJ 33.923.798) não foi encontrado nestes blocos.")
        
        # Debug para o usuário ver o que foi carregado
        with st.expander("Ver amostra dos dados carregados (Primeiras 10 linhas)"):
            st.write(df.head(10))
            st.write("Colunas detetadas:", df.columns.tolist())
else:
    st.info("👋 Bem-vindo! Por favor, faça o upload dos ficheiros ZIP na barra lateral para começar a análise.")