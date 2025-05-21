# Dashboard Preditivo de Ordens de Serviço - Goiás

## Objetivo
- Fornecer um painel inteligente para gestores otimizarem recursos, preverem atrasos e melhorarem a eficiência das ordens de serviço com base em dados reais e machine learning.

## Sobre
Projeto de análise de dados e machine learning focado em ordens de serviço (OS) da área de manutenção em municípios de Goiás. A ideia é usar dados geográficos, históricos de execução e tipos de serviço pra prever:
- Se a OS será efetiva ou não
- O tempo ideal para execução da OS
- Identificar padrões regionais com clusterização
- Visualizar mapas e gráficos para facilitar a tomada de decisão

## O que tem no projeto
- Dados das OS com informações como tipo, cidade, prefixo, datas e durações
- GeoJSON com os polígonos dos municípios de Goiás pra mapas interativos
- Pré-processamento: limpeza, balanceamento, normalização e tratamento de outliers
- Modelos ML treinados direto no script: XGBoost (classificação e regressão) e KMeans (clusterização)
- Visualizações com mapas, rankings e KPIs filtrados por cidade, prefixo, mês e dia
- Pipeline de machine learning integrado no dashboard Python, sem dependência externa
- Integração com Firebase Authentication para login (parte do sistema de autenticação)

## Tecnologias usadas
- Python (pandas, scikit-learn, XGBoost, matplotlib, seaborn, folium/plotly)
- Firebase Authentication para gerenciamento de usuários

## Estrutura
- dataframe_OPER.csv — dados principais das ordens de serviço
- geojson_goias.json — mapa dos municípios de Goiás
- ML_dashboard_preditivo.py — dashboard com análise, visualização e ML
- ML_TreinoTeste.py — script para treinar modelos e salvar arquivos .pkl
- Pastas auxiliares para dados, gráficos e configs do Firebase

Obs.: Gráfico ainda em desenvolvimento, por motivos de segurança a visualização do dashboard é restrita.
