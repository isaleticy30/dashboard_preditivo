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

def carregar_emergencial():
    arquivo = DIRETORIO_SAIDA / "oper_emergencial.csv"
    if arquivo.exists():
        df = pd.read_csv(arquivo, sep=";", encoding_errors='ignore')

        # 1. Converter colunas para datetime
        date_cols = ['DATA_ABERTURA', 'INICIO_DESLOCAMENTO', 'FIM_DESLOCAMENTO', 'INICIO_EXECUCAO', 'FIM_EXECUCAO']
        for col in date_cols: df[date_cols] = df[date_cols].apply(pd.to_datetime, errors='coerce')

        # 2. Tratamento de datas nulas
        valid_diff = (df['INICIO_DESLOCAMENTO'] - df['DATA_ABERTURA']).dropna()
        average_diff = valid_diff.mean()
        
        df.loc[df['INICIO_DESLOCAMENTO'].isna(), 'INICIO_DESLOCAMENTO'] = df['DATA_ABERTURA'] + average_diff
        df.loc[df['FIM_DESLOCAMENTO'].isna(), 'FIM_DESLOCAMENTO'] = df['INICIO_DESLOCAMENTO'] + timedelta(hours=1)
        df.loc[df['INICIO_EXECUCAO'].isna(), 'INICIO_EXECUCAO'] = df['FIM_DESLOCAMENTO']
        df.loc[df['FIM_EXECUCAO'].isna(), 'FIM_EXECUCAO'] = df['INICIO_EXECUCAO'] + timedelta(hours=1)
        
        # 3. Garantir FIM > INICIO
        df['FIM_DESLOCAMENTO'] = df[['INICIO_DESLOCAMENTO', 'FIM_DESLOCAMENTO']].max(axis=1)
        df['FIM_EXECUCAO'] = df[['INICIO_EXECUCAO', 'FIM_EXECUCAO']].max(axis=1)

        # 4. Tratamento do PREFIXO
        if 'PREFIXO' in df.columns:
            df['PREFIXO'] = df['PREFIXO'].str.slice(0, 3).replace('PIR', 'PRI') + df['PREFIXO'].str.slice(3)
        
        # 5. Tratamento da coluna OS
        if 'OCORRENCIA' in df.columns:
            df['OS'] = pd.to_numeric(
                df['OCORRENCIA'].astype(str).str.split('-').str[0].str.strip(),
                errors='coerce'
            ).fillna(0).astype(int)
            df.drop(columns=['OCORRENCIA'], inplace=True)

        # 6. Criar colunas de agrupamento ANTES de usá-las
        df['ANO_MES'] = df['INICIO_DESLOCAMENTO'].dt.to_period('M')
        df['DATA_DIA'] = df['INICIO_DESLOCAMENTO'].dt.date

        # 7. Cálculo das quantidades de OS
        df['QTD OS POR PREFIXO(MES)'] = df.groupby(['PREFIXO', 'ANO_MES'])['OS'].transform('nunique').astype(int)
        df['QTD OS POR PREFIXO(DIA)'] = df.groupby(['PREFIXO', 'DATA_DIA'])['OS'].transform('nunique').astype(int)

        # 8. Cálculo de efetividade (AGORA com ANO_MES já criado)
        if all(col in df.columns for col in ['MUNICIPIO', 'EFETIVIDADE', 'OS']):
            df['EFETIVIDADE'] = df['EFETIVIDADE'].fillna('EFETIVA')
            
            efetividade_mes = df[df['EFETIVIDADE'] == 'NÃO EFETIVA'].groupby(['MUNICIPIO', 'ANO_MES'])['OS'].nunique()
            df['EFETIVIDADE POR CIDADE (MES)'] = df.set_index(['MUNICIPIO', 'ANO_MES']).index.map(efetividade_mes).fillna(0).astype(int)
            
            efetividade_dia = df[df['EFETIVIDADE'] == 'NÃO EFETIVA'].groupby(['MUNICIPIO', 'DATA_DIA'])['OS'].nunique()
            df['EFETIVIDADE POR CIDADE (DIA)'] = df.set_index(['MUNICIPIO', 'DATA_DIA']).index.map(efetividade_dia).fillna(0).astype(int)

        # Calcular a diferença de tempo entre 'INICIO_DESLOCAMENTO' e 'DATA_SOLICITACAO' retorna em minutos
            df['TEMPO_RESPOSTA'] = (df['INICIO_DESLOCAMENTO'] - df['DATA_ABERTURA']).dt.total_seconds() / 60
            df['TEMPO_RESPOSTA'] = pd.to_numeric(df['TEMPO_RESPOSTA'], errors='coerce').fillna(0).astype(int)
        
        # 10. Remover colunas temporárias
        df.drop(columns=['ANO_MES', 'DATA_DIA'], inplace=True, errors='ignore')
        
        return df
    return None

# Realiza a junção e salva
def realizar_juncao():
    oper_emergencial = carregar_emergencial()
    IDs = carregar_IDs()

    if oper_emergencial is not None and IDs is not None:
        # Realiza a junção e adiciona a coluna "ID PREFIXO"
        df_resultado = oper_emergencial \
            .merge(IDs[['PREFIXO', 'ID PREFIXO']], on='PREFIXO', how='inner') \
            .merge(IDs[['MUNICIPIO', 'ID MUNICIPIO']], on='MUNICIPIO', how='inner') \
            .merge(IDs[['EFETIVIDADE', 'ID EFETIVIDADE']], on='EFETIVIDADE', how='inner') \
            .merge(IDs[['CAUSA', 'ID CAUSA']], on='CAUSA', how='left') \
            .merge(IDs[['MOTIVO RECLAMACAO EMERGENCIA', 'ID MOTIVO RECLAMACAO EMERGENCIA']], left_on='MOTIVO_RECLAMACAO', right_on='MOTIVO RECLAMACAO EMERGENCIA', how='inner')

        # Selecionar apenas as colunas desejadas
        df_resultado = df_resultado[['PREFIXO', 'OS', 'MUNICIPIO', 'CAUSA', 'MOTIVO_RECLAMACAO', 'EFETIVIDADE', 'DATA_ABERTURA',
                                     'INICIO_DESLOCAMENTO', 'FIM_DESLOCAMENTO', 'INICIO_EXECUCAO', 'FIM_EXECUCAO',
                                     'ID PREFIXO', 'ID MUNICIPIO', 'ID EFETIVIDADE', 'ID CAUSA',
                                     'ID MOTIVO RECLAMACAO EMERGENCIA','QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)',
                                     'EFETIVIDADE POR CIDADE (MES)','EFETIVIDADE POR CIDADE (DIA)', 'TEMPO_RESPOSTA']]
        # print(df_resultado.dtypes)

        # Converte ID EFETIVIDADE para inteiro no df_resultado
        df_resultado['ID EFETIVIDADE'] = pd.to_numeric(df_resultado['ID EFETIVIDADE'], errors='coerce').fillna(0).astype(int)
        # Converte DATA_ABERTURA e INICIO_DESLOCAMENTO para datetime no df_resultado
        colunas_data = ['DATA_ABERTURA', 'INICIO_DESLOCAMENTO', 'FIM_DESLOCAMENTO', 'INICIO_EXECUCAO', 'FIM_EXECUCAO']
        for col in colunas_data: df_resultado[col] = pd.to_datetime(df_resultado[col], errors='coerce')

        # Salvar a versão atualizada no CSV
        arquivo_saida_csv = DIRETORIO_SAIDA / "oper_emergencial.csv"
        df_resultado.to_csv(arquivo_saida_csv, index=False, sep=";", encoding="utf-8-sig")
        print("Arquivo Salvo")
    else:
        print("Erro ao carregar os dados, junção não realizada.")

# Chamar a função para realizar a junção e salvar os arquivos
realizar_juncao()