import pandas as pd
import zipfile
import io
import re
import streamlit as st  # <-- Faltava esta linha!

# Identificadores de CNPJ Raiz (8 primeiros dígitos)
CNPJ_MASTER_RAIZ = "33923798"
CNPJ_SOFISA_RAIZ = "60889128"

def carregar_dados(arquivos_zip):
    lista_df = []
    
    for arquivo_zip in arquivos_zip:
        with zipfile.ZipFile(arquivo_zip, 'r') as z:
            for nome_arquivo in z.namelist():
                # Foca apenas nos arquivos CSV de dados
                if nome_arquivo.endswith('.csv'):
                    with z.open(nome_arquivo) as f:
                        try:
                            # Lógica robusta para evitar erros de "ParserError"
                            df_temp = pd.read_csv(
                                f, 
                                sep=';', 
                                encoding='latin1', 
                                dtype=str, 
                                on_bad_lines='skip', 
                                low_memory=False
                            )
                            
                            if df_temp.empty:
                                continue

                            df_temp['arquivo_origem'] = nome_arquivo
                            
                            # Identifica colunas de CNPJ para Master e Sofisa
                            cols_cnpj = [c for c in df_temp.columns if "CNPJ" in c.upper()]
                            
                            df_temp['IS_MASTER'] = False
                            df_temp['IS_SOFISA'] = False
                            
                            for col in cols_cnpj:
                                # Limpa pontuação e extrai os 8 dígitos iniciais
                                cnpj_limpo = df_temp[col].str.replace(r'\D', '', regex=True).str[:8]
                                df_temp.loc[cnpj_limpo == CNPJ_MASTER_RAIZ, 'IS_MASTER'] = True
                                df_temp.loc[cnpj_limpo == CNPJ_SOFISA_RAIZ, 'IS_SOFISA'] = True
                            
                            # Tratamento de valores financeiros (troca vírgula por ponto)
                            cols_valor = [c for c in df_temp.columns if "VL_MERC" in c.upper() or "VL_PATRIM" in c.upper()]
                            for cv in cols_valor:
                                df_temp[cv] = df_temp[cv].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                                df_temp[cv] = pd.to_numeric(df_temp[cv], errors='coerce').fillna(0)
                            
                            lista_df.append(df_temp)
                            
                        except Exception as e:
                            # Agora o 'st' vai funcionar aqui
                            st.sidebar.warning(f"Aviso: Pulando {nome_arquivo} (Erro de formatação).")
                            continue
    
    if lista_df:
        return pd.concat(lista_df, ignore_index=True)
    return pd.DataFrame()
