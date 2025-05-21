import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess
import time
import plotly.graph_objects as go
import json
import geopandas as gpd
from dotenv import load_dotenv
from pathlib import Path

# Layout pra full screen
st.set_page_config(layout="wide")

# CSS fundo preto
st.markdown("""
<style>
/* FUNDO PRETO PARA TODO O DASHBOARD */
.stApp {
    background-color: #000000 !important;
}

/* CORRIGE COR DE TEXTO PADRÃO */
body, .stMarkdown, .stText, .stNumberInput, .stDataFrame {
    color: white !important;
}

/* CORRIGE COR DE FUNDO DOS GRÁFICOS PLOTLY */
.plot-container.plotly {
    background: rgba(0,0,0,0) !important;
}

/* CORRIGE COR DE FUNDO DOS CONTAINERS */
.stContainer, .stPlotlyChart {
    background: rgba(0,0,0,0.7) !important;
    border-radius: 10px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

# 1. Carregar configurações do arquivo .env
load_dotenv('credenciais_arquivos.env')
DIRETORIO_SAIDA = Path(os.getenv("DIRETORIO_SAIDA"))
geojson_goias = os.getenv("GEOJSON")
gdf = gpd.read_file(geojson_goias)

# Função para carregar o arquivo "ML_dataframe_OPER.csv"
def carregar_ML_dataframe_OPER():
    arquivo = DIRETORIO_SAIDA / "ML_dataframe_OPER.csv"
    if arquivo.exists():
        df = pd.read_csv(arquivo, sep=";", encoding_errors='ignore')
        return df
    print("Arquivo não encontrado.")
    return None

# Carregar os dados
df = carregar_ML_dataframe_OPER()
if df is None:
    st.error("Arquivo ML_dataframe_OPER.csv não encontrado no diretório configurado.")
    st.stop()

# Pré-processamento de datas
df['DATA SOLICITACAO'] = pd.to_datetime(df['DATA SOLICITACAO'], errors='coerce')
df['DATA INICIO EXECUCAO'] = pd.to_datetime(df['DATA INICIO EXECUCAO'], errors='coerce')
df['DATA FIM EXECUCAO'] = pd.to_datetime(df['DATA FIM EXECUCAO'], errors='coerce')
df['DATA INICIO DESLOCAMENTO'] = pd.to_datetime(df['DATA INICIO DESLOCAMENTO'], errors='coerce')
df['DATA FIM DESLOCAMENTO'] = pd.to_datetime(df['DATA FIM DESLOCAMENTO'], errors='coerce')

# CSS Botão de Atualizar
st.markdown("""
<style>
/* BOTÃO 3D VERDE - ESTILO MODERNO */
.stButton>button {
    background: linear-gradient(145deg, #2ecc71, #27ae60) !important;
    color: black !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    transform: scale(1.2) !important;
    font-weight: 600 !important;
    box-shadow: 
        0 4px 0 #1e8449,                                        /* Sombra 3D na base */
        0 6px 12px rgba(0, 0, 0, 0.2),                          /* Sombra externa */
        inset 0 2px 3px rgba(255, 255, 255, 0.3) !important;    /* Brilho interno */
    transition: all 0.2s ease !important;
    position: relative !important;
    top: -5px !important;
    text-transform: uppercase !important;
    left: 55px !important;  
}

/* EFEITO CLIQUE */
.stButton>button:active {
    transform: translateY(0) !important;            /* Volta à posição original */
    box-shadow: 
        0 2px 0 #1e8449,                            /* Sombra 3D reduzida */
        0 3px 6px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.1s ease-out !important;       /* Resposta rápida */
}
</style>
""", unsafe_allow_html=True)

# Botão de atualizar
if st.sidebar.button("ATUALIZAR"):
    try:
        inicio = time.time()  # marca o tempo de início

        # Chama o arquivo chamada_pai.py
        subprocess.run(["python", "chamada_pai.py"], check=True)
        
        fim = time.time()  # marca o tempo de fim
        duracao = fim - inicio  # calcula a duração

        # Exibe a mensagem após a execução do script
        success_message = st.sidebar.empty()  # Cria um "container" vazio
        success_message.success(f"Dashboard Atualizado com Sucesso! Tempo: {duracao:.2f} segundos")

        # Espera 3 segundos antes de limpar a mensagem
        time.sleep(3)

        # Limpa a mensagem
        success_message.empty()

    except subprocess.CalledProcessError as e:
        # Caso ocorra algum erro na execução do script, exibe uma mensagem de erro
        st.sidebar.error(f"Erro ao atualizar o dashboard: {e}")

# CSS Barra de Filtragem
st.markdown("""
<style>
/* BARRA LATERAL - DESIGN 3D AZUL OXFORD */
section[data-testid="stSidebar"] {
    background: linear-gradient(145deg, #001a38, #002147, #003366) !important;
    box-shadow: 15px 0 30px rgba(0, 0, 0, 0.4) !important;
    padding: 2rem 1.5rem !important;
    border-radius: 0 70px 50px 0 !important;
}

/* TÍTULO "FILTROS" */
section[data-testid="stSidebar"] h1 {
    color: white !important;
    font-size: 2rem !important;
    margin-bottom: 1.5rem !important;
    border-bottom: 2px solid rgba(255, 255, 255, 0.2);
    padding-bottom: 10px;
}

/* Caixa de Seleção */
.stMultiSelect, .stSelectbox {
    background: linear-gradient(145deg, #004080, #002147) !important;   /* Gradiente azul com ângulo de 145° */
    border-radius: 20px !important;                                     /* Bordas super arredondadas */
    margin-bottom: 3.5rem !important;                                   /* Grande margem inferior */
    box-shadow:                                                         /* Sistema de sombras 3D: */
        0 4px 8px rgba(0, 0, 0, 0.25),                                  /* - Sombra externa */
        inset 0 2px 3px rgba(255, 255, 255, 0.15),                      /* - Sombra interna superior (brilho) */
        inset 0 -3px 5px rgba(0, 0, 0, 0.3) !important;                 /* - Sombra interna inferior (profundidade) */
    border: 1px solid rgba(255, 255, 255, 0.2) !important;              /* Borda branca semi-transparente */
    color: white !important;                                            /* Texto branco */
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;   /* Transições suaves */
    /* Dimensões aumentadas: */
    min-height: 120px !important;                                       /* Altura mínima grande */
    padding: 10px 10px !important;                                      /* Espaçamento interno generoso */
    padding-top: 30px !important;                                       /* Empurra o texto para baixo */
    width: calc(80% + 97px) !important;                                 /* Aumenta 30px para cada lado */
    margin-left: -30px !important;                                      /* Compensa para centralizar */
    margin-right: 30px !important;                                      /* Compensa para centralizar */
    margin-bottom: 2rem !important;
    position: relative !important;                                      /* Contexto para posicionamento */
    left: 6px !important;                                               /* Ajuste fino de posição */
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    will-change: transform;                                             /* Otimiza a animação */
}
            
/* EFEITO HOVER PARA OS FILTROS */
.stMultiSelect:hover, 
.stSelectbox:hover {
    transform: translateY(-2px) !important;  /* Movimento sutil para cima */
    box-shadow: 
        0 6px 12px rgba(0, 0, 0, 0.3),
        inset 0 2px 3px rgba(255, 255, 255, 0.2),
        inset 0 -3px 5px rgba(0, 0, 0, 0.35) !important;
}
            
/* ESTILO PARA O RÓTULO (TÍTULO ACIMA DA SELEÇÃO) */
.stMultiSelect > label, 
.stSelectbox > label {
    display: block !important;          /* Garante que fique em linha separada */
    transform: scale(1.5) !important;   /* Tamanho da letra */
    font-weight: 600 !important;        /* Negrito */
    color: white !important;            /* Cor do texto */
    margin-bottom: 1rem !important;     /* Espaço entre título e caixa */
    text-align: center !important;        /* Alinhamento no centro*/
}
</style>
""", unsafe_allow_html=True)

# Filtros laterais (MANTIDO ORIGINAL)
st.sidebar.title("Filtros")
tipo_os = st.sidebar.multiselect("Tipo de OS", df['TIPO OS'].unique())
cidade = st.sidebar.multiselect("Município", sorted(df['MUNICIPIO'].dropna().unique()))
prefixo = st.sidebar.multiselect("Prefixo", df['PREFIXO'].unique())
efetividade = st.sidebar.multiselect("Efetividade", df['EFETIVIDADE'].unique())

# Aplicar filtros laterais
df_filtrado = df.copy()

if tipo_os:
    df_filtrado = df_filtrado[df_filtrado['TIPO OS'].isin(tipo_os)]

if cidade:
    df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].isin(cidade)]

if prefixo:
    df_filtrado = df_filtrado[df_filtrado['PREFIXO'].isin(prefixo)]

if efetividade:
    df_filtrado = df_filtrado[df_filtrado['EFETIVIDADE'].isin(efetividade)]

# Cria a coluna ATRASO_PROJETADO
df_filtrado['ATRASO_PROJETADO'] = (df_filtrado['TEMPO_DESLOCAMENTO_PRED'] + df_filtrado['DURACAO_SERVICO_PRED']) - df_filtrado['TEMPO_IDEAL_PRED']

# Título
st.title("Dashboard Preditivo Referente as Ordens de Serviço")

# CSS Tabs
st.markdown("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    font-size: 15px !important;
    color: white !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "⏱️ Tempo de Resposta", 
    "🛠️ Duração do Serviço", 
    "🔥 Mapa de Calor", 
    "🏆 Ranking de Atrasos"
])

# Tab 1: Previsão Tempo de Resposta
with tab1:
    st.subheader("Previsão de Tempo de Resposta Média por Prefixo")

    tipo_os_selecionado_tab1 = st.radio(
        "Selecione o tipo de OS",
        options=['Todos', 'Comercial', 'Emergencial'],
        horizontal=True,
        key="tipo_tab1"  # <- chave única
    )

    df_filtrado['STATUS'] = df_filtrado['STATUS'].str.upper()

    if tipo_os_selecionado_tab1 != 'Todos':
        df_tipo = df_filtrado[df_filtrado['STATUS'] == tipo_os_selecionado_tab1.upper()]
    else:
        df_tipo = df_filtrado.copy()

    # Agrupando e calculando média
    df_grouped = df_tipo.groupby('PREFIXO')['TEMPO_RESPOSTA_PRED'].mean().reset_index()

    # Converter valor bruto pra unidade ajustada
    def converter_valor(minutos):
        if minutos < 60:
            return minutos  # continua em minutos
        elif minutos < 1440:
            return minutos / 60  # vira horas
        else:
            return minutos / 1440  # vira dias

    def definir_unidade(minutos):
        if minutos < 60:
            return "min"
        elif minutos < 1440:
            return "h"
        else:
            return "d"

    df_grouped['VALOR_CONVERTIDO'] = df_grouped['TEMPO_RESPOSTA_PRED'].apply(converter_valor)
    df_grouped['UNIDADE'] = df_grouped['TEMPO_RESPOSTA_PRED'].apply(definir_unidade)
    df_grouped['LABEL'] = df_grouped['VALOR_CONVERTIDO'].round(1).astype(str) + " " + df_grouped['UNIDADE']

    # Gráfico com eixo Y adaptado
    fig1 = px.line(
        df_grouped,
        x='PREFIXO',
        y='VALOR_CONVERTIDO',
        markers=True,
        title="⏱️ Tendência de Tempo de Resposta das OS por Prefixo"
    )

    fig1.update_traces(
        mode="lines+markers+text",
        text=df_grouped['LABEL'],
        textposition="top center"
    )

    fig1.update_layout(
        height=600,
        xaxis_title="Prefixo",
        yaxis_title="Tempo de Resposta (convertido)",
        hovermode="x unified"
    )

    st.plotly_chart(fig1, use_container_width=True)

# Tab 2: Previsão Duração do Serviço
with tab2:
    st.subheader("Previsão de Duração Média das Ordens de Serviço por Prefixos, Município e Efetividade")

    tipo_os_selecionado_tab2 = st.radio(
        "Selecione o tipo de OS",
        options=['Todos', 'Comercial', 'Emergencial'],
        horizontal=True,
        key="tipo_tab2"  # <- chave única
    )

    df_filtrado['STATUS'] = df_filtrado['STATUS'].str.upper()

    if tipo_os_selecionado_tab2 != 'Todos':
        df_tipo = df_filtrado[df_filtrado['STATUS'] == tipo_os_selecionado_tab2.upper()]

    # Agrupa por MUNICIPIO + EFETIVIDADE
    df_agg = df_tipo.groupby(['MUNICIPIO', 'EFETIVIDADE'], dropna=False).agg(
        QTD_PREFIXOS=('PREFIXO', 'nunique'),
        DURACAO_MEDIA=('DURACAO_SERVICO_PRED', 'mean')
    ).reset_index()

    # Combinações
    municipios_restantes = df_tipo['MUNICIPIO'].unique()
    efetividades_presentes = df_tipo['EFETIVIDADE'].unique()

    combinacoes = pd.MultiIndex.from_product(
        [municipios_restantes, efetividades_presentes],
        names=['MUNICIPIO', 'EFETIVIDADE']
    ).to_frame(index=False)

    # Junta e preenche
    df_final = combinacoes.merge(df_agg, on=['MUNICIPIO', 'EFETIVIDADE'], how='left')
    df_final['QTD_PREFIXOS'] = df_final['QTD_PREFIXOS'].fillna(0).astype(int)
    df_final['DURACAO_MEDIA'] = df_final['DURACAO_MEDIA'].fillna(0)

    # Cores desejadas
    cores = {
        'EFETIVA': '#239B56',
        'NÃO EFETIVA': '#C0392B'
    }

    limiar_barra_curta = 5

    # Gráfico
    fig2 = go.Figure()

    for efetividade in df_final['EFETIVIDADE'].unique():
        df_efet = df_final[df_final['EFETIVIDADE'] == efetividade]

        cor_texto = df_efet['QTD_PREFIXOS'].apply(lambda x: 'white' if x < limiar_barra_curta else 'black')

        fig2.add_trace(go.Bar(
            y=df_efet['MUNICIPIO'],
            x=df_efet['QTD_PREFIXOS'],
            name=efetividade,
            orientation='h',
            text=df_efet['DURACAO_MEDIA'].apply(
                lambda x: f"{round(x/1440, 1)} dias" if x >= 1440 else f"{round(x/60, 1)} horas" if x >= 60 else f"{round(x)} min"
            ),
            textposition='auto',
            marker_color=cores.get(efetividade, 'gray'),
            textfont=dict(color=cor_texto)
        ))

    fig2.update_layout(
        barmode='relative',
        xaxis_title="Quantidade de Prefixos Distintos",
        yaxis=dict(title="Município", tickfont=dict(size=14)),
        height=1700,
        legend_title="Efetividade",
        margin=dict(l=120, r=60, t=55, b=10),
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Previsão média da duração predita por TIPO OS
    df_previsao_tipo = df_tipo.groupby('TIPO OS')['DURACAO_SERVICO_PRED'].mean().reset_index()

    # Converte duração em minutos
    df_previsao_tipo['DURACAO_PREVISTA'] = df_previsao_tipo['DURACAO_SERVICO_PRED'].apply(
        lambda x: f"{round(x/1440, 1)} dias" if x >= 1440 else f"{round(x/60, 1)} horas" if x >= 60 else f"{round(x)} min"
    )

    # Agrupa prefixos por TIPO OS
    prefixos_por_tipo = df_tipo.groupby('TIPO OS')['PREFIXO'].apply(lambda x: ', '.join(sorted(x.unique()))).reset_index()

    # Junta
    df_previsao_tabela = df_previsao_tipo[['TIPO OS', 'DURACAO_PREVISTA']].merge(prefixos_por_tipo, on='TIPO OS', how='left')

    # Renomeia colunas
    df_previsao_tabela.rename(columns={
        'TIPO OS': 'Tipo de Serviço',
        'DURACAO_PREVISTA': 'Duração Prevista',
        'PREFIXO': 'Prefixos com Tendência em Executar a OS'
    }, inplace=True)

    # Mostra a tabela
    st.markdown("### Duração média prevista por Tipo de Serviço e Prefixos com tendência")
    st.dataframe(df_previsao_tabela, use_container_width=True)

# Tab 3: Mapa de calor da tendência
with tab3:
    st.subheader("Visão Geral Preditiva de Tempo e Performance nas OS por Municipio")

    tipo_os_selecionado_tab2 = st.radio(
        "Selecione o tipo de OS",
        options=['Todos', 'Comercial', 'Emergencial'],
        horizontal=True,
        key="tipo_tab3"
    )

    # Ajustando o filtro para STATUS
    df_filtrado['STATUS'] = df_filtrado['STATUS'].str.upper()
    if tipo_os_selecionado_tab2 != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['STATUS'] == tipo_os_selecionado_tab2.upper()]

    # Função de preparação dos dados para o mapa
    def prepare_data(gdf, df):
        gdf['id'] = gdf['id'].astype(int)
        df['ID MUNICIPIO'] = df['ID MUNICIPIO'].astype(int)

        medias = df.groupby(['ID MUNICIPIO', 'MUNICIPIO'])['TEMPO_RESPOSTA_PRED'].mean().reset_index()
        mapa_df = gdf.merge(medias, left_on='id', right_on='ID MUNICIPIO', how='left')

        mapa_df['TEMPO_RESPOSTA_PRED'] = mapa_df['TEMPO_RESPOSTA_PRED'].fillna(-1)
        mapa_df['TEMPO_DE_RESPOSTA'] = mapa_df['TEMPO_RESPOSTA_PRED'].apply(
            lambda x: f"{int(x//1440)}d {int((x%1440)//60)}h" if x >= 1440 else
            f"{int(x//60)}h {int(x%60)}min" if x >= 60 else
            f"{int(x)}min" if x >= 0 else "Sem dados"
        )

        return mapa_df
    
    def formatar_tempo(minutos):
        if minutos >= 1440:
            return f"{round(minutos / 1440, 1)} dia(s)"
        elif minutos >= 60:
            return f"{round(minutos / 60, 1)} hora(s)"
        else:
            return f"{int(minutos)} min"

    # Preparando dados do mapa
    mapa_df = prepare_data(gdf, df_filtrado)
    gdf_json = json.loads(gdf.to_json())

    # Definindo a escala de cores
    colorscale = [
        [0.0, '#CCCCCC'],
        [0.0001, '#440154'],
        [1.0, '#FDE725']
    ]

    fig = px.choropleth(
        mapa_df,
        geojson=gdf_json,
        locations='id',
        featureidkey="properties.id",
        color="TEMPO_RESPOSTA_PRED",
        color_continuous_scale=colorscale,
        scope="south america",
        hover_name="name",
        hover_data={"TEMPO_DE_RESPOSTA": True, "TEMPO_RESPOSTA_PRED": False, "id": False}
    )

    fig.update_traces(
        hoverinfo='location+z+text',
        locationmode='geojson-id'
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor='rgba(0,0,0,0)',
        center=dict(lat=-15.9, lon=-49.8),
        subunitcolor='rgba(0,0,0,0)',
        landcolor='lightgray'
    )

    # Configuração do layout com clickmode
    fig.update_layout(
        title="Tempo de Resposta Médio por Município",
        height=900,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        geo=dict(bgcolor='rgba(0,0,0,0)', landcolor='rgba(0,0,0,0)'),
        clickmode="event+select"
    )

    # Exibindo o gráfico com interatividade
    col_esq, col_centro, col_dir = st.columns([0.1, 11, 0.1])  # Coluna central mais larga
    with col_centro:
        click_data = st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Exibindo a tabela com todos os dados inicialmente
    st.subheader("Análise de Desvios Preditivos no Tempo de Execução")
    tabela = df_filtrado[['MUNICIPIO', 'PREFIXO', 'TIPO OS', 'SUB OS', 'TEMPO_IDEAL_PRED', 'ATRASO_PROJETADO']]
    tabela['TEMPO_IDEAL_PRED'] = tabela['TEMPO_IDEAL_PRED'].apply(formatar_tempo)
    tabela['ATRASO_PROJETADO'] = tabela['ATRASO_PROJETADO'].apply(formatar_tempo)
    st.dataframe(tabela)

    # Verificando se houve um clique no mapa
    if 'clickData' in st.session_state:
        click_data = st.session_state.clickData  # Pega os dados do clique armazenados na sessão

        if click_data and 'points' in click_data and len(click_data['points']) > 0:
            selected_municipio = click_data['points'][0].get('location', None)  # Pega o ID do município, se existir

            if selected_municipio is not None:
                municipio_selecionado_df = df_filtrado[df_filtrado['ID MUNICIPIO'] == selected_municipio].copy()

                # Aplica formatação bonitinha
                municipio_selecionado_df['TEMPO_IDEAL_PRED'] = municipio_selecionado_df['TEMPO_IDEAL_PRED'].apply(formatar_tempo)
                municipio_selecionado_df['ATRASO_PROJETADO'] = municipio_selecionado_df['ATRASO_PROJETADO'].apply(formatar_tempo)

                st.subheader(f"Tabela de dados para o município selecionado:")
                st.dataframe(municipio_selecionado_df[['ID MUNICIPIO', 'PREFIXO', 'TIPO OS', 'SUB OS', 'TEMPO_IDEAL_PRED', 'ATRASO_PROJETADO', 'MUNICIPIO']])

# Tab 4: Ranking de atrasos projetados
with tab4:
    tipo_os_selecionado_tab2 = st.radio(
        "Selecione o tipo de OS",
        options=['Todos', 'Comercial', 'Emergencial'],
        horizontal=True,
        key="tipo_tab4"
    )

    if tipo_os_selecionado_tab2 != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['TIPO OS'].str.upper() == tipo_os_selecionado_tab2.upper()]

    df_filtrado['ATRASO_PROJETADO'] = df_filtrado['ATRASO_PROJETADO'].apply(lambda x: max(x, 0))

    # Formatar
    def formatar_atraso(minutos):
        if minutos < 0:
            return "0h"
        horas = minutos / 60
        if horas < 24:
            return f"{horas:.1f}h"
        dias = horas / 24
        return f"{dias:.1f}d"

    # Ranking
    ranking_completo = df_filtrado.groupby(['MUNICIPIO', 'PREFIXO'])['ATRASO_PROJETADO'].mean().reset_index()
    ranking_pior_prefixo = ranking_completo.sort_values('ATRASO_PROJETADO', ascending=False).groupby('MUNICIPIO').first().reset_index()
    ranking_pior_prefixo = ranking_pior_prefixo.sort_values('ATRASO_PROJETADO', ascending=False)

    ranking_pior_prefixo['ATRASO_PROJETADO'] = ranking_pior_prefixo['ATRASO_PROJETADO'].apply(formatar_atraso)

    st.subheader("Top 10 Cidades e Prefixo com Tendência a Não Cumprir o Tempo Previsto")
    st.dataframe(ranking_pior_prefixo[['MUNICIPIO', 'PREFIXO', 'ATRASO_PROJETADO']].head(10), use_container_width=True)