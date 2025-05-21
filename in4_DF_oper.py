import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv('credenciais_arquivos.env')
DIRETORIO_SAIDA = Path(os.getenv("DIRETORIO_SAIDA"))

def carregar_comercial():
    caminho = DIRETORIO_SAIDA / "oper_comercial.csv"
    if not caminho.exists():
        return pd.DataFrame()
    df = pd.read_csv(caminho, sep=";", encoding_errors='ignore')
    df["STATUS"] = "COMERCIAL"
    df = df.rename(columns={
        "PREFIXO": "PREFIXO",
        "SS_NUMERO": "OS",
        "MUNICIPIO": "MUNICIPIO",
        "TIPO_SERVICO": "TIPO OS",
        "SUBTIPO_SERVICO": "SUB OS",
        "EFETIVIDADE_VISITA": "EFETIVIDADE",
        "DATA_SOLICITACAO": "DATA SOLICITACAO",
        "INICIO_DESLOCAMENTO": "DATA INICIO DESLOCAMENTO",
        "FIM_DESLOCAMENTO": "DATA FIM DESLOCAMENTO",
        "INICIO_EXECUCAO": "DATA INICIO EXECUCAO",
        "FIM_EXECUCAO": "DATA FIM EXECUCAO",
        "ID PREFIXO": "ID PREFIXO",
        "ID MUNICIPIO": "ID MUNICIPIO",
        "ID EFETIVIDADE": "ID EFETIVIDADE",
        "ID TIPO SERVICO COMERCIAL": "ID TIPO OS",
        "ID SUBTIPO SERVICO COMERCIAL": "ID SUB OS",
        "QTD OS POR PREFIXO(MES)": "QTD OS POR PREFIXO(MES)",
        "QTD OS POR PREFIXO(DIA)": "QTD OS POR PREFIXO(DIA)",
        "EFETIVIDADE POR CIDADE (MES)": "EFETIVIDADE POR CIDADE (MES)",
        "EFETIVIDADE POR CIDADE (DIA)": "EFETIVIDADE POR CIDADE (DIA)",
        "TEMPO_RESPOSTA": "TEMPO_RESPOSTA"
    })
    return df[["PREFIXO", "OS", "MUNICIPIO", "TIPO OS", "SUB OS", "EFETIVIDADE", "DATA SOLICITACAO", "DATA INICIO DESLOCAMENTO", "DATA FIM DESLOCAMENTO",
               "DATA INICIO EXECUCAO", "DATA FIM EXECUCAO", "ID PREFIXO", "ID MUNICIPIO", "ID EFETIVIDADE", "ID TIPO OS", "ID SUB OS", "QTD OS POR PREFIXO(MES)",
               "QTD OS POR PREFIXO(DIA)", "EFETIVIDADE POR CIDADE (MES)", "EFETIVIDADE POR CIDADE (DIA)", "TEMPO_RESPOSTA", "STATUS"]]

def carregar_emergencial():
    caminho = DIRETORIO_SAIDA / "oper_emergencial.csv"
    if not caminho.exists():
        return pd.DataFrame()
    df = pd.read_csv(caminho, sep=";", encoding_errors='ignore')
    df["STATUS"] = "EMERGENCIAL"
    df = df.rename(columns={
        "PREFIXO": "PREFIXO",
        "OS": "OS",
        "MUNICIPIO": "MUNICIPIO",
        "CAUSA": "TIPO OS",
        "MOTIVO_RECLAMACAO": "SUB OS",
        "EFETIVIDADE": "EFETIVIDADE",
        "DATA_ABERTURA": "DATA SOLICITACAO",
        "INICIO_DESLOCAMENTO": "DATA INICIO DESLOCAMENTO",
        "FIM_DESLOCAMENTO": "DATA FIM DESLOCAMENTO",
        "INICIO_EXECUCAO": "DATA INICIO EXECUCAO",
        "FIM_EXECUCAO": "DATA FIM EXECUCAO",
        "ID PREFIXO": "ID PREFIXO",
        "ID MUNICIPIO": "ID MUNICIPIO",
        "ID EFETIVIDADE": "ID EFETIVIDADE",
        "ID CAUSA": "ID TIPO OS",
        "ID MOTIVO RECLAMACAO EMERGENCIA": "ID SUB OS",
        "QTD OS POR PREFIXO(MES)": "QTD OS POR PREFIXO(MES)",
        "QTD OS POR PREFIXO(DIA)": "QTD OS POR PREFIXO(DIA)",
        "EFETIVIDADE POR CIDADE (MES)": "EFETIVIDADE POR CIDADE (MES)",
        "EFETIVIDADE POR CIDADE (DIA)": "EFETIVIDADE POR CIDADE (DIA)",
        "TEMPO_RESPOSTA": "TEMPO_RESPOSTA"
    })
    return df[["PREFIXO", "OS", "MUNICIPIO", "TIPO OS", "SUB OS", "EFETIVIDADE", "DATA SOLICITACAO", "DATA INICIO DESLOCAMENTO", "DATA FIM DESLOCAMENTO",
               "DATA INICIO EXECUCAO", "DATA FIM EXECUCAO", "ID PREFIXO", "ID MUNICIPIO", "ID EFETIVIDADE", "ID TIPO OS", "ID SUB OS", "QTD OS POR PREFIXO(MES)",
               "QTD OS POR PREFIXO(DIA)", "EFETIVIDADE POR CIDADE (MES)", "EFETIVIDADE POR CIDADE (DIA)", "TEMPO_RESPOSTA", "STATUS"]]

# Carrega os dois já no formato padronizado
df_comercial = carregar_comercial()
df_emergencial = carregar_emergencial()

# Junta tudo
df_unificado = pd.concat([df_emergencial, df_comercial], ignore_index=True)

# Converte colunas de data para datetime
colunas_data = ['DATA SOLICITACAO', 'DATA INICIO DESLOCAMENTO', 'DATA FIM DESLOCAMENTO', 'DATA INICIO EXECUCAO', 'DATA FIM EXECUCAO']
for col in colunas_data: df_unificado[col] = pd.to_datetime(df_unificado[col], errors='coerce')

# Adiciona coluna ID STATUS
df_unificado["ID STATUS"] = df_unificado["STATUS"].map({
    "COMERCIAL": 1001,
    "EMERGENCIAL": 1002
})

# print(df_unificado.dtypes)

# Salva o resultado
def salvar_unificado(df):
    caminho = DIRETORIO_SAIDA / "dataframe_OPER.csv"
    df.to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")
    print("Arquivo dataframe_OPER.csv salvo com sucesso!")

salvar_unificado(df_unificado)