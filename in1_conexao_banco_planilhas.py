import os
import pandas as pd
import io
import warnings
from dotenv import load_dotenv
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext
warnings.filterwarnings('ignore')

# 1. Configurações do OneDrive e Sharepoint a partir do .env
load_dotenv('credenciais_arquivos.env')
ONEDRIVE_SITE = os.getenv("SITE_ONEDRIVE_PAI")
USUARIO = os.getenv("SHAREPOINT_USUARIO")
SENHA = os.getenv("SHAREPOINT_SENHA")

ARQUIVOS_ONEDRIVE = {
    "oper_comercial": {
        "onedrive_url": os.getenv("URL_ONEDRIVE_OPERCOMERCIAL"),
        "server_relative_url_OD": os.getenv("CAMINHO_ARQUIVO_COMERCIAL"),
        "colunas_comercial": ['PREFIXO', 'SS_NUMERO', 'MUNICIPIO', 'TIPO_SERVICO', 'SUBTIPO_SERVICO', 'EFETIVIDADE_VISITA', 'DATA_SOLICITACAO',
                              'INICIO_DESLOCAMENTO', 'FIM_DESLOCAMENTO', 'INICIO_EXECUCAO', 'FIM_EXECUCAO']
    },
    "oper_emergencial": {
        "onedrive_url": os.getenv("URL_ONEDRIVE_OPEREMERGENCIAL"),
        "server_relative_url_OD": os.getenv("CAMINHO_ARQUIVO_EMERGENCIAL"),
        "colunas_emergencial": ['PREFIXO', 'OCORRENCIA', 'MUNICIPIO', 'CAUSA', 'MOTIVO_RECLAMACAO', 'EFETIVIDADE', 'DATA_ABERTURA', 'INICIO_DESLOCAMENTO',
                                'FIM_DESLOCAMENTO', 'INICIO_EXECUCAO', 'FIM_EXECUCAO']
    },
    "IDs": {
        "onedrive_url": os.getenv("URL_ONEDRIVE_IDs"),
        "server_relative_url_OD": os.getenv("CAMINHO_ARQUIVO_IDs"),
        "colunas_IDs": ['ID PREFIXO', 'PREFIXO', 'ID MUNICIPIO', 'MUNICIPIO', 'ID EFETIVIDADE', 'EFETIVIDADE', 'ID TIPO SERVICO COMERCIAL', 'TIPO SERVICO COMERCIAL',
                        'ID SUBTIPO SERVICO COMERCIAL', 'SUBTIPO SERVICO COMERCIAL', 'ID MOTIVO RECLAMACAO EMERGENCIA', 'MOTIVO RECLAMACAO EMERGENCIA', 'ID CAUSA', 'CAUSA',
                        'ID PLACA', 'PLACA', 'ID TIPO EQUIPE', 'TIPO EQUIPE', 'ID PERFIL', 'PERFIL', 'ID TIPO', 'TIPO']                   
    }
}

# 2. Configuração do site do OneDrive e Sharepoint
ONEDRIVE_SITE = os.getenv("SITE_ONEDRIVE_PAI")
# SHAREPOINT_SITE = os.getenv("SITE_SHAREPOINT_PAI")

def conectar_onedrive():
    try:
        credenciais = UserCredential(USUARIO, SENHA)
        ctxOD = ClientContext(ONEDRIVE_SITE).with_credentials(credenciais)
        ctxOD.load(ctxOD.web)  # Carrega informações do site
        ctxOD.execute_query()  # Executa a consulta
        print("Conexão estabelecida com o OneDrive")
        return ctxOD
    except Exception as e:
        print(f"Erro ao baixar arquivo do OneDrive: {e}")
        return None

def baixar_arquivo_onedrive(ctxOD, server_relative_url_OD, nome_arquivo):
    try:
        arquivoOD = ctxOD.web.get_file_by_server_relative_path(server_relative_url_OD)
        responseOD = arquivoOD.open_binary(ctxOD, server_relative_url_OD)

        try:
            df = pd.read_excel(io.BytesIO(responseOD.content), engine='openpyxl')
            print("Arquivo lido com sucesso!")
        except Exception as e:
            print("Erro ao ler o arquivo Excel:", e)
            return None

        # Escolher as colunas dependendo do arquivo
        if nome_arquivo == "oper_comercial":
            colunas = ARQUIVOS_ONEDRIVE[nome_arquivo].get("colunas_comercial", [])
        elif nome_arquivo == "oper_emergencial":
            colunas = ARQUIVOS_ONEDRIVE[nome_arquivo].get("colunas_emergencial", [])
        elif nome_arquivo == "IDs":
            colunas = ARQUIVOS_ONEDRIVE[nome_arquivo].get("colunas_IDs", [])
        else:
            colunas = []

        # Seleciona as colunas do DataFrame
        df = df[colunas]

        # Adicionar "- GO" SOMENTE para cidades específicas na coluna MUNICIPIO
        if nome_arquivo == "oper_comercial" and "MUNICIPIO" in df.columns:
            cidades_para_modificar = ["CALDAS NOVAS", "CATALAO", "ITUMBIARA", "MORRINHOS", "RIO VERDE", "PIRES DO RIO"]
            df["MUNICIPIO"] = df["MUNICIPIO"].apply(lambda x: x + " - GO" if x in cidades_para_modificar else x)

        if nome_arquivo == "oper_emergencial" and "MUNICIPIO" in df.columns:
            cidades_para_modificar = ["CALDAS NOVAS", "CATALAO", "ITUMBIARA", "MORRINHOS", "RIO VERDE", "PIRES DO RIO"]
            df["MUNICIPIO"] = df["MUNICIPIO"].apply(lambda x: x + " - GO" if x in cidades_para_modificar else x)

        # Transformar as colunas para o tipo inteiro
        colunas_inteiros = ['ID PREFIXO', 'ID MUNICIPIO', 'ID EFETIVIDADE', 'ID TIPO SERVICO COMERCIAL', 
                            'ID SUBTIPO SERVICO COMERCIAL', 'ID MOTIVO RECLAMACAO EMERGENCIA', 'ID CAUSA',
                            'ID PLACA', 'ID TIPO EQUIPE', 'ID PERFIL', 'ID TIPO']

        for coluna in colunas_inteiros:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce').fillna(0).astype(int)

        return df
    except Exception as e:
        print("Erro ao baixar arquivo do OneDrive:", e)
        return None

def main():
    print("Iniciando Conexão com o OneDrive...")
    # Conectar ao OneDrive
    ctxOD = conectar_onedrive()
    if not ctxOD:
        return
    
    resultados = {}
    
    for nomeOD, configOD in ARQUIVOS_ONEDRIVE.items():
        
        dfOD = baixar_arquivo_onedrive(ctxOD, configOD["server_relative_url_OD"], nomeOD)
        
        if dfOD is not None:
            resultados[nomeOD] = dfOD
            
            # Salvar localmente como backup
            dfOD.to_csv(f"{nomeOD}.csv", index=False, encoding='utf-8-sig', sep=';')
        else:
            print("Falha ao processar")
    
    if resultados:
        print("Processamento concluído com sucesso!")

if __name__ == "__main__":
    main()