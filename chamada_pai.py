import os
import subprocess
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

def excluir_csv_antigos(diretorio_saida):
    arquivos_csv_pkl = [ 
        "oper_comercial.csv", 
        "oper_emergencial.csv", 
        "IDs.csv",
        "dataframe_OPER.csv",
        "ML_dataframe_OPER.csv",
        "modelo_efetividade_xgb.pkl",
        "modelo_tempo_deslocamento.pkl",
        "modelo_tempo_ideal_xgb.pkl",
        "modelo_tempo_resposta.pkl",
        "modelo_tempo_servico.pkl"
    ]
    
    for arquivo in arquivos_csv_pkl:
        caminho_arquivo = os.path.join(diretorio_saida, arquivo)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            logging.info(f"Arquivo excluído: {caminho_arquivo}")
        else:
            logging.info(f"Arquivo não encontrado para exclusão: {caminho_arquivo}")

def main():
    try:
        # 1. Configuração de ambiente
        load_dotenv("credenciais_arquivos.env")
        DIRETORIO_SAIDA = Path(os.getenv("DIRETORIO_SAIDA"))
        os.chdir(DIRETORIO_SAIDA)
        
        logging.info(f"Diretório base: {DIRETORIO_SAIDA}")

        # Verifica se o diretório existe e possui arquivos para excluir antes de tentar excluir
        if os.path.exists(DIRETORIO_SAIDA):
            # Exclui arquivos CSV antigos
            excluir_csv_antigos(DIRETORIO_SAIDA)
        else:
            logging.warning(f"O diretório especificado não existe: {DIRETORIO_SAIDA}")
            return 1

        # 2. Lista de scripts
        SCRIPTS = [
            "in1_conexao_banco_planilhas.py",
            # "in2_ETL_view_turnos_pessoas.py",
            # "in3_ETL_view_turnos.py",
            # "in4_ETL_view_pessoas.py",
            # "in5_ETL_view_turnos_deslocamentos.py",
            "in2_ETL_oper_comercial.py",
            "in3_ETL_oper_emergencial.py",
            # "in8_DF_turnos.py",
            "in4_DF_oper.py",
            "ML1_TreinoTeste.py"
        ]

        # 3. Execução dos scripts
        for script in SCRIPTS:
            script_path = os.path.join(DIRETORIO_SAIDA, script)
            logging.info(f"Iniciando execução de {script}")
            
            if not os.path.exists(script_path):
                logging.error(f"Script não encontrado: {script_path}")
                return 1

            try:
                result = subprocess.run(
                    [sys.executable, script_path],
                    cwd=DIRETORIO_SAIDA,
                    env=os.environ,
                    check=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60  # Timeout de 5 minutos por script
                )
                
                logging.info(f"{script} concluído. Saída: {result.stdout[:200]}...")

            except subprocess.TimeoutExpired:
                logging.error(f"Timeout ao executar {script}")
                return 1
            except subprocess.CalledProcessError as e:
                logging.error(f"Erro em {script}:\n{e.stderr}")
                return 1

        logging.info("Todos os scripts carregados com sucesso!")
        return 0

    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())