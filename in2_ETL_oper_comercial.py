import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

# 1. Carregar configurações
load_dotenv('credenciais_arquivos.env')
DIRETORIO_SAIDA = Path(os.getenv("DIRETORIO_SAIDA"))

def carregar_IDs():
    arquivo = DIRETORIO_SAIDA / "IDs.csv"
    if arquivo.exists():
        df = pd.read_csv(arquivo, sep=";", encoding_errors='ignore')
        return df
    return None

def carregar_comercial():
    arquivo = DIRETORIO_SAIDA / "oper_comercial.csv"
    if arquivo.exists():
        df = pd.read_csv(arquivo, sep=";", encoding_errors='ignore')  # Definir o delimitador como ponto e vírgula

        # Converte colunas para datetime
        df['DATA_SOLICITACAO'] = pd.to_datetime(df['DATA_SOLICITACAO'], errors='coerce')
        df['INICIO_DESLOCAMENTO'] = pd.to_datetime(df['INICIO_DESLOCAMENTO'], errors='coerce')
        df['FIM_DESLOCAMENTO'] = pd.to_datetime(df['FIM_DESLOCAMENTO'], errors='coerce')
        df['INICIO_EXECUCAO'] = pd.to_datetime(df['INICIO_EXECUCAO'], errors='coerce')
        df['FIM_EXECUCAO'] = pd.to_datetime(df['FIM_EXECUCAO'], errors='coerce')
        
        # Passo 1: Calcular média INICIO_DESLOCAMENTO - DATA_SOLICITACAO
        valid_diff = (df['INICIO_DESLOCAMENTO'] - df['DATA_SOLICITACAO']).dropna()
        average_diff = valid_diff.mean()
        
        # Passo 2: Preenchimento de nulos
        mask = df['INICIO_DESLOCAMENTO'].isna()
        df.loc[mask, 'INICIO_DESLOCAMENTO'] = df.loc[mask, 'DATA_SOLICITACAO'] + average_diff
        
        mask = df['FIM_DESLOCAMENTO'].isna()
        df.loc[mask, 'FIM_DESLOCAMENTO'] = df.loc[mask, 'INICIO_DESLOCAMENTO'] + timedelta(hours=1)

        mask = df['INICIO_EXECUCAO'].isna()
        df.loc[mask, 'INICIO_EXECUCAO'] = df.loc[mask, 'FIM_DESLOCAMENTO']
        
        mask = df['FIM_EXECUCAO'].isna()
        df.loc[mask, 'FIM_EXECUCAO'] = df.loc[mask, 'INICIO_EXECUCAO'] + timedelta(hours=1)
        
        # Garantir FIM > INICIO
        df['FIM_DESLOCAMENTO'] = df[['INICIO_DESLOCAMENTO', 'FIM_DESLOCAMENTO']].max(axis=1)
        df['FIM_EXECUCAO'] = df[['INICIO_EXECUCAO', 'FIM_EXECUCAO']].max(axis=1)

        # Substitui "PIR" por "PRI" nos três primeiros caracteres da coluna "PREFIXO"
        if 'PREFIXO' in df.columns:
            df['PREFIXO'] = df['PREFIXO'].str.slice(0, 3).replace('PIR', 'PRI') + df['PREFIXO'].str.slice(3)

        # Adiciona as colunas QTD OS PREFIXO(MES) e QTD OS PREFIXO(DIA)
        if 'INICIO_DESLOCAMENTO' in df.columns and 'SS_NUMERO' in df.columns and 'PREFIXO' in df.columns:
            df['ANO_MES'] = df['INICIO_DESLOCAMENTO'].dt.to_period('M')  # Agrupamento mensal
            df['DATA'] = df['INICIO_DESLOCAMENTO'].dt.date  # Agrupamento diário

            # Contagem de SS_NUMERO distintos por equipe e por período
            df['QTD OS POR PREFIXO(MES)'] = df.groupby(['PREFIXO', 'ANO_MES'])['SS_NUMERO'].transform('nunique')
            df['QTD OS POR PREFIXO(DIA)'] = df.groupby(['PREFIXO', 'DATA'])['SS_NUMERO'].transform('nunique')

        # Adiciona as novas colunas de efetividade por cidade (mês e dia)
        if all(col in df.columns for col in ['MUNICIPIO', 'EFETIVIDADE_VISITA', 'SS_NUMERO', 'ANO_MES', 'DATA']):
            # Filtro para considerar apenas as OS não efetivas
            df['EFETIVIDADE_VISITA'] = df['EFETIVIDADE_VISITA'].fillna('EFETIVA')  # Caso tenha valores nulos

            # EFETIVIDADE POR CIDADE (MES)
            efetividade_mes = df[df['EFETIVIDADE_VISITA'] == 'NÃO EFETIVA'].groupby(['MUNICIPIO', 'ANO_MES'])['SS_NUMERO'].nunique()
            df['EFETIVIDADE POR CIDADE (MES)'] = df.set_index(['MUNICIPIO', 'ANO_MES']).index.map(efetividade_mes).fillna(0).astype(int)

            # EFETIVIDADE POR CIDADE (DIA)
            efetividade_dia = df[df['EFETIVIDADE_VISITA'] == 'NÃO EFETIVA'].groupby(['MUNICIPIO', 'DATA'])['SS_NUMERO'].nunique()
            df['EFETIVIDADE POR CIDADE (DIA)'] = df.set_index(['MUNICIPIO', 'DATA']).index.map(efetividade_dia).fillna(0).astype(int)

            # Remover as colunas temporárias
            df.drop(columns=['ANO_MES', 'DATA'], inplace=True)

            # Calcular a diferença de tempo entre 'INICIO_DESLOCAMENTO' e 'DATA_SOLICITACAO' retorna em minutos
            df['TEMPO_RESPOSTA'] = (df['INICIO_DESLOCAMENTO'] - df['DATA_SOLICITACAO']).dt.total_seconds() / 60
            df['TEMPO_RESPOSTA'] = pd.to_numeric(df['TEMPO_RESPOSTA'], errors='coerce').fillna(0).astype(int)

        return df
    return None

# Realiza a junção e salva
def realizar_juncao():
    oper_comercial = carregar_comercial()
    IDs = carregar_IDs()

    if oper_comercial is not None and IDs is not None:
        # Realiza a junção e adiciona a coluna "ID PREFIXO"
        df_resultado = oper_comercial \
    .merge(IDs[['PREFIXO', 'ID PREFIXO']], on='PREFIXO', how='inner') \
    .merge(IDs[['MUNICIPIO', 'ID MUNICIPIO']], on='MUNICIPIO', how='inner') \
    .merge(IDs[['EFETIVIDADE', 'ID EFETIVIDADE']], left_on='EFETIVIDADE_VISITA', right_on='EFETIVIDADE', how='inner') \
    .merge(IDs[['TIPO SERVICO COMERCIAL', 'ID TIPO SERVICO COMERCIAL']], left_on='TIPO_SERVICO', right_on='TIPO SERVICO COMERCIAL', how='inner') \
    .merge(IDs[['SUBTIPO SERVICO COMERCIAL', 'ID SUBTIPO SERVICO COMERCIAL']], left_on='SUBTIPO_SERVICO', right_on='SUBTIPO SERVICO COMERCIAL', how='inner')
        
        # Remover as colunas originais (não ID) que foram duplicadas
        df_resultado = df_resultado[['PREFIXO', 'SS_NUMERO', 'MUNICIPIO', 'TIPO_SERVICO', 'SUBTIPO_SERVICO', 'EFETIVIDADE_VISITA', 'DATA_SOLICITACAO', 'INICIO_DESLOCAMENTO',
                'FIM_DESLOCAMENTO', 'INICIO_EXECUCAO', 'FIM_EXECUCAO', 'ID PREFIXO', 'ID MUNICIPIO', 'ID EFETIVIDADE', 'ID TIPO SERVICO COMERCIAL', 'ID SUBTIPO SERVICO COMERCIAL',
                'QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)', 'EFETIVIDADE POR CIDADE (MES)', 'EFETIVIDADE POR CIDADE (DIA)', 'TEMPO_RESPOSTA']]
        # print(df_resultado.dtypes)

        # Salvar a versão atualizada no CSV
        arquivo_saida_csv = DIRETORIO_SAIDA / "oper_comercial.csv"
        df_resultado.to_csv(arquivo_saida_csv, index=False, sep=";", encoding="utf-8-sig")
        print("Arquivo Salvo.")
    else:
        print("Erro ao carregar os dados, junção não realizada.")

# Chamar a função para realizar a junção e salvar os arquivos
realizar_juncao()