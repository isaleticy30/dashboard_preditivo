Esse projeto é um dashboard preditivo de ordens de serviço com foco na análise de dados geográficos de Goiás e machine learning pra previsão de tempo e efetividade.

O que tem no projeto
Dados de Ordens de Serviço (OS): Tabelas com detalhes como tipo de serviço (comercial ou emergencial), cidades, prefixos, datas e durações.

GeoJSON dos municípios de Goiás: Polígonos geográficos pra plotar mapas e analisar regionalmente.

Análise exploratória e pré-processamento: Limpeza, normalização, balanceamento (undersampling) e remoção de outliers.

Modelos de ML:

Classificação: Previsão se uma OS será efetiva ou não.

Regressão Linear: Previsão do tempo ideal de execução da OS.

Clusterização (KMeans): Identificação de grupos de municípios com padrões similares.

Visualizações interativas:

Mapas choropleth com os polígonos dos municípios.

Gráficos para identificar cidades com maior taxa de não efetividade.

Rankings de equipes e cidades que mais atrasam.

KPIs de tempo de resposta, duração e efetividade, filtrados por cidade, prefixo, mês e dia.

Pipeline ML integrado no dashboard: Treina e testa os modelos direto no script Python, sem depender de arquivos externos.

Ferramentas usadas:

Python com pandas, scikit-learn, XGBoost, matplotlib, seaborn, folium (ou plotly para mapas).

Power BI (algumas análises e relatórios).

Firebase Authentication para login (parte do sistema que você mencionou em outras conversas).

Objetivo final: Ajudar gestores a entender onde e quando as OS são menos efetivas, prever o tempo ideal para otimizar recursos e identificar padrões regionais.
