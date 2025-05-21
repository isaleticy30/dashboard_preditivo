import pandas as pd
import os
import joblib
import numpy as np
import xgboost as xgb
from pathlib import Path
from dotenv import load_dotenv
from sklearn.model_selection import (train_test_split, GridSearchCV)
from sklearn.metrics import (classification_report, mean_squared_error, r2_score,)
from sklearn.utils import resample
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import (GradientBoostingRegressor)
from sklearn.pipeline import Pipeline
from xgboost import (XGBClassifier, XGBRegressor)
from sklearn.impute import SimpleImputer
from datetime import datetime

# Carregar .env e arquivo OPER
load_dotenv('credenciais_arquivos.env')
DIRETORIO_SAIDA = Path(os.getenv("DIRETORIO_SAIDA"))

def carregar_OPER():
    arquivo = DIRETORIO_SAIDA / "dataframe_OPER.csv"
    if arquivo.exists():
        df = pd.read_csv(arquivo, sep=";", encoding_errors='ignore')
        colunas_data = ['DATA SOLICITACAO', 'DATA INICIO DESLOCAMENTO', 
                       'DATA FIM DESLOCAMENTO', 'DATA INICIO EXECUCAO', 
                       'DATA FIM EXECUCAO']
        for col in colunas_data: 
            df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    return None

print("Carregando e preparando os dados...")
df_original = carregar_OPER()

# Criar cópia base pra modelos e análises
df = df_original.copy()

# Filtrar outliers para ID_STATUS 1002 (excluindo tempo de resposta acima de 24h) e ID_STATUS 1001 (acima de 5 dias)
print("\nAnalisando outliers com tempo de resposta por ID_STATUS...")

# Para ID_STATUS 1002 (EMERGENCIAL), excluindo tempo de resposta acima de 24h (1440 minutos)
df_1002 = df[(df['ID STATUS'] == 1002) & (df['TEMPO_RESPOSTA'] <= 1440)]

# Para ID_STATUS 1001 (COMERCIAL), excluindo tempo de resposta acima de 5 dias (7200 minutos)
df_1001 = df[(df['ID STATUS'] == 1001) & (df['TEMPO_RESPOSTA'] <= 7200)]

# Concatenando os dois dataframes de volta para obter o conjunto de dados completo, sem os outliers.
df = pd.concat([df_1002, df_1001])

print(f"\nTotal de registros após remoção dos outliers: {df.shape[0]}")

# Para verificar os filtros e os outliers
outliers_1002 = df_1002[df_1002['TEMPO_RESPOSTA'] > 1440]
outliers_1001 = df_1001[df_1001['TEMPO_RESPOSTA'] > 7200]

print(f"\nOutliers para ID_STATUS 1002 (acima de 24h): {outliers_1002.shape[0]}")
print(f"\nOutliers para ID_STATUS 1001 (acima de 5 dias): {outliers_1001.shape[0]}")

# Cria DURACAO_SERVICO, TEMPO_DESLOCAMENTO e TEMPO_EXECUCAO
df['DURACAO_SERVICO'] = (df['DATA FIM EXECUCAO'] - df['DATA INICIO DESLOCAMENTO']).dt.total_seconds() / 60
df['TEMPO_EXECUCAO'] = (df['DATA FIM EXECUCAO'] - df['DATA INICIO EXECUCAO']).dt.total_seconds() / 60
df['TEMPO_DESLOCAMENTO'] = (df['DATA FIM DESLOCAMENTO'] - df['DATA INICIO DESLOCAMENTO']).dt.total_seconds() / 60
df = df[df['TEMPO_DESLOCAMENTO'] <= 120]

df['DIA_SEMANA_FIM_DESLOCAMENTO'] = df['DATA FIM DESLOCAMENTO'].dt.dayofweek  # Dia da semana (0=segunda, 6=domingo)
df['MES_FIM_DESLOCAMENTO'] = df['DATA FIM DESLOCAMENTO'].dt.month  # Mês (1=Janeiro, 12=Dezembro)

df['DIA_SEMANA_IN_DESLOCAMENTO'] = df['DATA INICIO DESLOCAMENTO'].dt.dayofweek  # Dia da semana (0=segunda, 6=domingo)
df['MES_IN_DESLOCAMENTO'] = df['DATA INICIO DESLOCAMENTO'].dt.month  # Mês (1=Janeiro, 12=Dezembro)
df = df[df['TEMPO_DESLOCAMENTO'] <= 120]

df['DATA_PREVISTA'] = df['DATA SOLICITACAO'] + pd.DateOffset(months=3)
df['DIA_SEMANA'] = df['DATA SOLICITACAO'].dt.dayofweek  # Dia da semana (0=segunda, 6=domingo)
df['MES'] = df['DATA SOLICITACAO'].dt.month  # Mês (1=Janeiro, 12=Dezembro)
df['TRIMESTRE_SOLICITACAO'] = df['DATA SOLICITACAO'].dt.to_period('Q')
# Adiciona uma coluna com a data do próximo trimestre
df['TRIMESTRE_PREVISTO'] = df['DATA SOLICITACAO'] + pd.DateOffset(months=3)
df['TRIMESTRE_PREVISTO'] = df['TRIMESTRE_PREVISTO'].dt.to_period('Q')
trimestre_limite = (pd.Timestamp.today() + pd.DateOffset(months=3)).to_period('Q')
df_futuro = df[df['TRIMESTRE_PREVISTO'] <= trimestre_limite]
df['TRIMESTRE_PREVISTO'] = df['TRIMESTRE_PREVISTO'].astype('int64')

# Obter o mês atual
mes_atual = datetime.now().month

# Verificar o próximo mês
if mes_atual == 4:  # Abril
    proximo_mes = 5  # Maio
elif mes_atual == 5:  # Maio
    proximo_mes = 6  # Junho
elif mes_atual == 6:  # Junho
    proximo_mes = 7  # Julho
else:
    proximo_mes = None  # Caso seja após julho ou outro mês que você não quer prever

print(proximo_mes)

# ======================================================================
# 1. MODELO DE PREVISÃO DE DURAÇÃO DO SERVIÇO
# ======================================================================
print("\n=== MODELO DE DURAÇÃO DO SERVIÇO ===")
X_duracao = df[['TRIMESTRE_PREVISTO', 'ID MUNICIPIO', 'ID STATUS', 'ID TIPO OS', 'ID SUB OS',
                'QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)',
                'EFETIVIDADE POR CIDADE (MES)', 'EFETIVIDADE POR CIDADE (DIA)']]
y_duracao = df['DURACAO_SERVICO']

# Divisão dos dados
X_train_duracao, X_test_duracao, y_train_duracao, y_test_duracao = train_test_split(
    X_duracao, y_duracao, test_size=0.2, random_state=42)

# Pipeline de pré-processamento e modelo
pipeline_duracao = Pipeline([
    ('imputer', SimpleImputer(strategy='mean')),  # Imputação dos valores NaN
    ('scaler', StandardScaler()),                # Normalização dos dados
    ('regressor', GradientBoostingRegressor(random_state=42))  # Modelo de regressão
])

# Treinar o modelo
pipeline_duracao.fit(X_train_duracao, y_train_duracao)
df['DURACAO_SERVICO_PRED'] = pipeline_duracao.predict(X_duracao)

# Avaliação do modelo
y_pred_duracao = pipeline_duracao.predict(X_test_duracao)
print("\nAvaliação do modelo de DURACAO_SERVICO:")
mse = mean_squared_error(y_test_duracao, y_pred_duracao)
rmse = np.sqrt(mse)
print("RMSE:", rmse)
print("R²:", r2_score(y_test_duracao, y_pred_duracao))

# Prever para todo o dataframe
df['DURACAO_SERVICO_PRED'] = pipeline_duracao.predict(X_duracao)

# Salvar modelo
joblib.dump(pipeline_duracao, DIRETORIO_SAIDA / 'modelo_tempo_servico.pkl')

# ======================================================================
# 2. Treinando o modelo XGBoost para classificação de EFETIVIDADE
# ======================================================================
print("\n=== MODELO DE CLASSIFICAÇÃO DE EFETIVIDADE ===")

# Balanceamento dos dados
def balancear_efetividade_por_tipo(df_tipo, nome_tipo):
    print(f"\n{nome_tipo} - Distribuição antes do balanceamento: ")
    print(df_tipo['ID EFETIVIDADE'].value_counts())

    df_tipo = df_tipo.dropna(subset=['DURACAO_SERVICO', 'TEMPO_DESLOCAMENTO'])

    classe_0 = df_tipo[df_tipo['ID EFETIVIDADE'] == 0]
    classe_1 = df_tipo[df_tipo['ID EFETIVIDADE'] == 1]

    if len(classe_0) == 0 or len(classe_1) == 0:
        print(f"{nome_tipo} não pode ser balanceado (classe ausente).")
        return df_tipo

    n = min(len(classe_0), len(classe_1))
    classe_0_red = resample(classe_0, replace=False, n_samples=n, random_state=42)
    classe_1_red = resample(classe_1, replace=False, n_samples=n, random_state=42)

    return pd.concat([classe_0_red, classe_1_red])

# Trabalhar só com o df_futuro
df_comercial = df_futuro[df_futuro['ID STATUS'] == 1001]
df_emergencial = df_futuro[df_futuro['ID STATUS'] == 1002]

print("\nBalanceando Comercial e Emergencial separadamente...")
df_comercial_balanceado = balancear_efetividade_por_tipo(df_comercial, "COMERCIAL")
df_emergencial_balanceado = balancear_efetividade_por_tipo(df_emergencial, "EMERGENCIAL")

df_balanceado = pd.concat([df_comercial_balanceado, df_emergencial_balanceado])

print("\nDistribuição de classes após o balanceamento: ")
print(df_balanceado['ID EFETIVIDADE'].value_counts())

X_efetividade = df_balanceado[['ID MUNICIPIO', 'ID STATUS', 'ID TIPO OS', 'ID SUB OS',
                               'QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)',
                               'EFETIVIDADE POR CIDADE (MES)', 'EFETIVIDADE POR CIDADE (DIA)']]
y_efetividade = df_balanceado['ID EFETIVIDADE']

X_train_efetividade, X_test_efetividade, y_train_efetividade, y_test_efetividade = train_test_split(
    X_efetividade, y_efetividade, test_size=0.2, random_state=42)

modelo_xgb = XGBClassifier(random_state=42)
modelo_xgb.fit(X_train_efetividade, y_train_efetividade)

y_pred_efetividade = modelo_xgb.predict(X_test_efetividade)
print("\nAvaliação do modelo de EFETIVIDADE:")
print(classification_report(y_test_efetividade, y_pred_efetividade))

joblib.dump(modelo_xgb, DIRETORIO_SAIDA / 'modelo_efetividade_xgb.pkl')

# ======================================================================
# 3. MODELO DE PREVISÃO DE TEMPO DE RESPOSTA
# ======================================================================
print("\n=== MODELO DE TEMPO DE RESPOSTA ===")

df_modelo = df_futuro.dropna(subset=[
    'TEMPO_RESPOSTA', 'ID MUNICIPIO', 'ID STATUS', 'ID TIPO OS', 'ID SUB OS',
    'QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)',
    'EFETIVIDADE POR CIDADE (MES)', 'EFETIVIDADE POR CIDADE (DIA)'
])

X_resposta = df_modelo[[ 'ID MUNICIPIO', 'ID STATUS', 'ID TIPO OS', 'ID SUB OS',
                         'QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)',
                         'EFETIVIDADE POR CIDADE (MES)', 'EFETIVIDADE POR CIDADE (DIA)' ]]
y_resposta = df_modelo['TEMPO_RESPOSTA']

X_train_resp, X_test_resp, y_train_resp, y_test_resp = train_test_split(
    X_resposta, y_resposta, test_size=0.2, random_state=42)

pipeline_resposta = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', GradientBoostingRegressor(random_state=42))
])

pipeline_resposta.fit(X_train_resp, y_train_resp)

y_pred_resp = pipeline_resposta.predict(X_test_resp)
print("\nAvaliação do modelo de TEMPO_RESPOSTA:")
mse = mean_squared_error(y_test_resp, y_pred_resp)
rmse = np.sqrt(mse)
print("RMSE:", rmse)
print("R²:", r2_score(y_test_resp, y_pred_resp))

# Prever para TODO df, mas só os do futuro receberão resultado realista
df['TEMPO_RESPOSTA_PRED'] = pipeline_resposta.predict(df[[ 'ID MUNICIPIO', 'ID STATUS', 'ID TIPO OS', 'ID SUB OS',
                                                           'QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)',
                                                           'EFETIVIDADE POR CIDADE (MES)', 'EFETIVIDADE POR CIDADE (DIA)' ]].fillna(0))

joblib.dump(pipeline_resposta, DIRETORIO_SAIDA / 'modelo_tempo_resposta.pkl')

# ======================================================================
# 4. MODELO DE TEMPO IDEAL
# ======================================================================
print("\n=== MODELO DE TEMPO IDEAL ===")

# 2. Criando um exemplo de coluna 'CLUSTER'.
df['CLUSTER'] = df['MUNICIPIO'].astype('category').cat.codes  # Apenas um exemplo de cluster com base no 'MUNICIPIO'

# 3. Criando a variável "MÊS FUTURO" para prever o tempo ideal para os próximos 3 meses
df['MES_FUTURO'] = df['MES'] + 3  # Prevendo para os próximos 3 meses, ajustando a variável de mês para o futuro

# 4. Preparando os dados para o treinamento
X = df[['TIPO OS', 'MUNICIPIO', 'PREFIXO', 'DIA_SEMANA', 'MES', 'CLUSTER']]  # Features
y = df['DURACAO_SERVICO']  # Target (tempo ideal)

# Convertendo variáveis categóricas para numéricas (se necessário)
X = pd.get_dummies(X, drop_first=True)  # Usando dummies para variáveis categóricas

# Divisão de treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Inicializando e treinando o modelo XGBoost
modelo_xgb = xgb.XGBRegressor(objective='reg:squarederror', eval_metric='rmse')
modelo_xgb.fit(X_train, y_train)

# 6. Prevendo os resultados no conjunto de teste
y_pred = modelo_xgb.predict(X_test)

# 7. Calculando o erro quadrático médio (MSE)
mse_xgb = mean_squared_error(y_test, y_pred)
print(f"Erro quadrático médio (MSE) do modelo XGBoost: {mse_xgb}")
df['TEMPO_IDEAL'] = modelo_xgb.predict(X)

df_futuro = df.copy()
df_futuro['MES'] = df_futuro['MES'] + 3  # ou algum ajuste pra bater com a lógica de negócio

# Garantir que o modelo tá usando os dados com o MES do futuro
X_futuro = df_futuro[['TIPO OS', 'MUNICIPIO', 'PREFIXO', 'DIA_SEMANA', 'MES', 'CLUSTER']]
X_futuro = pd.get_dummies(X_futuro, drop_first=True)

# Reindex pra garantir que as colunas estão no mesmo formato
X_futuro = X_futuro.reindex(columns=X.columns, fill_value=0)

# Previsão pros meses futuros
df_futuro['TEMPO_IDEAL_PRED'] = modelo_xgb.predict(X_futuro)
df['TEMPO_IDEAL_PRED'] = df_futuro['TEMPO_IDEAL_PRED']

# 8. Salvando o modelo
joblib.dump(modelo_xgb, "modelo_tempo_ideal_xgb.pkl")

# ======================================================================
# 5. MODELO DE PREVISÃO DE TEMPO DE DESLOCAMENTO
# ======================================================================

print("\n=== MODELO DE TEMPO DE DESLOCAMENTO ===")

# Garantir tipo datetime
df['DATA SOLICITACAO'] = pd.to_datetime(df['DATA SOLICITACAO'], errors='coerce')

# Features temporais
df['DIA_SEMANA'] = df['DATA SOLICITACAO'].dt.dayofweek
df['MES_SOLICITACAO'] = df['DATA SOLICITACAO'].dt.month

# Remover outliers extremos de deslocamento
media = df['TEMPO_DESLOCAMENTO'].mean()
desvio = df['TEMPO_DESLOCAMENTO'].std()
df = df[df['TEMPO_DESLOCAMENTO'] < media + 2 * desvio]

# Variáveis explicativas
X_deslocamento = df[['DIA_SEMANA_FIM_DESLOCAMENTO','MES_FIM_DESLOCAMENTO', 'DIA_SEMANA_IN_DESLOCAMENTO', 'MES_IN_DESLOCAMENTO', 'DIA_SEMANA',
                     'MES', 'ID MUNICIPIO', 'ID STATUS', 'ID TIPO OS', 'ID SUB OS', 'QTD OS POR PREFIXO(MES)', 'QTD OS POR PREFIXO(DIA)',
                     'EFETIVIDADE POR CIDADE (MES)', 'EFETIVIDADE POR CIDADE (DIA)', 'ID PREFIXO', 'TEMPO_RESPOSTA', 'MES_SOLICITACAO']]

y_deslocamento = df['TEMPO_DESLOCAMENTO']

# Divisão dos dados
X_train_deslocamento, X_test_deslocamento, y_train_deslocamento, y_test_deslocamento = train_test_split(
    X_deslocamento, y_deslocamento, test_size=0.2, random_state=42)

# Pipeline
pipeline_deslocamento = Pipeline([
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler()),
    ('regressor', XGBRegressor(random_state=42))
])

# Treinar o modelo inicial
pipeline_deslocamento.fit(X_train_deslocamento, y_train_deslocamento)

# Avaliação inicial
y_pred_deslocamento = pipeline_deslocamento.predict(X_test_deslocamento)
print("\nAvaliação inicial do modelo:")
print("RMSE:", np.sqrt(mean_squared_error(y_test_deslocamento, y_pred_deslocamento)))
print("R²:", r2_score(y_test_deslocamento, y_pred_deslocamento))

# Grid Search para otimização
param_grid = {
    'regressor__n_estimators': [100, 300],
    'regressor__learning_rate': [0.01, 0.1],
    'regressor__max_depth': [3, 6],
    'regressor__subsample': [0.8, 1.0],
}

grid_search = GridSearchCV(
    estimator=pipeline_deslocamento,
    param_grid=param_grid,
    cv=3,
    n_jobs=-1,
    verbose=0  # sem log poluindo o terminal
)
grid_search.fit(X_train_deslocamento, y_train_deslocamento)

# Melhor modelo encontrado
best_pipeline = grid_search.best_estimator_

# Avaliação final
y_pred_best = best_pipeline.predict(X_test_deslocamento)
rmse_best = np.sqrt(mean_squared_error(y_test_deslocamento, y_pred_best))
print(f"Melhor Modelo XGBoost - RMSE: {rmse_best:.2f} | R²: {r2_score(y_test_deslocamento, y_pred_best):.2f}")

# Salvar modelo
joblib.dump(best_pipeline, 'modelo_tempo_deslocamento.pkl')

# Prever para todo o dataframe
df['TEMPO_DESLOCAMENTO_PRED'] = best_pipeline.predict(X_deslocamento)

# Preview
print("\nPrimeiras previsões:")
print(df[['PREFIXO', 'TEMPO_DESLOCAMENTO', 'TEMPO_DESLOCAMENTO_PRED']].head())

# ======================================================================
# FINALIZAÇÃO
# ======================================================================

# Previsões agregadas
df['PREVISAO_DURACAO_PREFIXO'] = df.groupby('PREFIXO')['DURACAO_SERVICO_PRED'].transform('median')
df['PREVISAO_DURACAO_CIDADE'] = df.groupby('MUNICIPIO')['DURACAO_SERVICO_PRED'].transform('median')

# Garantir tipos corretos
colunas_para_int = ['ID STATUS', 'ID EFETIVIDADE', 'PREVISAO_DURACAO_PREFIXO',
                   'PREVISAO_DURACAO_CIDADE', 'DURACAO_SERVICO', 
                   'TEMPO_DESLOCAMENTO', 'CLUSTER']

for col in colunas_para_int:
    if df[col].isnull().any():
        df[col] = df[col].fillna(-1)
    df[col] = df[col].round().astype(int)

# Remove colunas do df
df.drop(columns='TEMPO_IDEAL', inplace=True)
df.drop(columns='DIA_SEMANA', inplace=True)
df.drop(columns='TRIMESTRE_SOLICITACAO', inplace=True)
df.drop(columns='TRIMESTRE_PREVISTO', inplace=True)
df.drop(columns='DATA_PREVISTA', inplace=True)
df.drop(columns='MES', inplace=True)
df.drop(columns='CLUSTER', inplace=True)

df.to_csv(DIRETORIO_SAIDA / "ML_dataframe_OPER.csv", sep=";", 
          index=False, float_format='%.2f', encoding='utf-8-sig')

print("\nProcesso concluído com sucesso!")
print("\nResumo dos modelos treinados:")
print("- Modelo de Duração do Serviço (GradientBoostingRegressor)")
print("- Modelo de Classificação de Efetividade (XGBoost)")
print("- MODELO DE PREVISÃO DE TEMPO DE DESLOCAMENTO (GradientBoostingRegressor)")
print("- Modelo de Tempo de Resposta (GradientBoostingRegressor)")
print("- Modelo de Tempo Ideal (GradientBoostingRegressor)")