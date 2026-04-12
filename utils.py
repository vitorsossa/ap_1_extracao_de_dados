import pandas as pd
import zipfile
import streamlit as st
import sys
import csv

# Aumenta o limite para evitar erro de campos muito longos
csv.field_size_limit(sys.maxsize)

def carregar_dados(uploaded_files):
    dfs = []
    # Blocos que vamos ler (BLC_5 é onde o Master costuma estar)
    BLOCOS_FOCO = ['BLC_1', 'BLC_4', 'BLC_5', 'PL', 'FIE'] 
    CNPJ_MASTER_RAIZ = "33923798"

    for arquivo in uploaded_files:
        try:
            with zipfile.ZipFile(arquivo) as z:
                # Lista apenas os arquivos que batem com nossos blocos
                csvs_alvo = [n for n in z.namelist() if any(b in n.upper() for b in BLOCOS_FOCO)]
                
                for nome_csv in csvs_alvo:
                    with z.open(nome_csv) as f:
                        # Lemos o arquivo completo
                        df_temp = pd.read_csv(
                            f, sep=";", encoding="latin1", dtype=str,
                            on_bad_lines="skip", engine="python"
                        )
                        
                        if df_temp.empty:
                            continue
                        
                        # Adicionamos metadados
                        df_temp["arquivo_origem"] = nome_csv
                        
                        # Criamos a coluna IS_MASTER varrendo TODAS as colunas
                        # Isso resolve o problema de nomes de colunas diferentes (BLC_1 vs BLC_5)
                        df_temp['IS_MASTER'] = False
                        for col in df_temp.columns:
                            c_upper = col.upper()
                            # Busca por CNPJ em qualquer coluna que tenha 'CNPJ'
                            if "CNPJ" in c_upper:
                                cnpj_limpo = df_temp[col].str.replace(r'\D', '', regex=True)
                                df_temp['IS_MASTER'] |= cnpj_limpo.str.contains(CNPJ_MASTER_RAIZ, na=False)
                            
                            # Busca por Nome em colunas de emissor ou denominação
                            if any(x in c_upper for x in ["EMISSOR", "DENOM", "SOCIAL"]):
                                df_temp['IS_MASTER'] |= df_temp[col].str.upper().str.contains("MASTER", na=False)
                        
                        dfs.append(df_temp)
                        
        except Exception as e:
            st.error(f"Erro ao processar o ZIP {arquivo.name}: {e}")

    if not dfs:
        return pd.DataFrame()

    # Une todos os arquivos lidos
    df_final = pd.concat(dfs, ignore_index=True, sort=False)
    
    # Garante que a coluna Master seja booleana
    if 'IS_MASTER' in df_final.columns:
        df_final['IS_MASTER'] = df_final['IS_MASTER'].fillna(False).astype(bool)
    else:
        df_final['IS_MASTER'] = False

    return df_final