import pandas as pd
from datasets import Dataset, IterableDataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import os
from dotenv import load_dotenv
import logging # Para logging
import time # Para adicionar delays

# Configura logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente (ex: OPENAI_API_KEY) do arquivo .env
load_dotenv()

# Nome do arquivo CSV de entrada e saída
RAGAS_DATASET_CSV = "ragas_evaluation_dataset.csv"
RAGAS_RESULTS_CSV = "ragas_evaluation_results_batched.csv" # Novo nome para resultados em batch

# Parâmetros para batching
EVALUATION_BATCH_SIZE = 5  # Número de itens por batch de avaliação
DELAY_BETWEEN_BATCHES = 10 # Segundos de espera entre batches

def run_ragas_evaluation():
    logger.info(f"Iniciando a avaliação Ragas.")
    logger.info(f"Carregando dataset de entrada: {RAGAS_DATASET_CSV}")

    if not os.path.exists(RAGAS_DATASET_CSV):
        logger.error(f"Arquivo do dataset '{RAGAS_DATASET_CSV}' não encontrado. "
                     "Certifique-se de que o script 'gerar_dataset_ragas.py' foi executado com sucesso.")
        return

    try:
        df_full = pd.read_csv(RAGAS_DATASET_CSV, sep=';')
    except Exception as e:
        logger.error(f"Erro ao carregar o arquivo CSV '{RAGAS_DATASET_CSV}': {e}")
        return

    logger.info(f"Dataset completo carregado com {len(df_full)} linhas.")

    # Converte a coluna 'contexts' de string para lista de strings
    try:
        import ast
        if 'contexts' not in df_full.columns:
            logger.error("A coluna 'contexts' não foi encontrada no CSV. Verifique o script gerar_dataset_ragas.py.")
            return
        df_full['contexts'] = df_full['contexts'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        logger.info("Coluna 'contexts' no dataset completo convertida de string para lista.")
    except Exception as e:
        logger.error(f"Erro ao converter a coluna 'contexts' no dataset completo: {e}. "
                     "Certifique-se de que a coluna 'contexts' está formatada como uma lista de strings no CSV.")
        return

    # Verifica se a API key da OpenAI está carregada
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("Atenção: OPENAI_API_KEY não encontrada nas variáveis de ambiente. "
                     "A avaliação não pode prosseguir sem a chave da API.")
        return
    logger.info("OPENAI_API_KEY encontrada.")

    # Define o LLM e os Embeddings para a avaliação
    # Aumentar max_retries e definir um timeout pode ajudar com erros 429 esporádicos.
    llm_for_evaluation = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0,
        api_key=openai_api_key,
        max_retries=10,  # Aumentado o número de tentativas
        request_timeout=120  # Aumentado o timeout da requisição para 2 minutos
    )
    embeddings_for_evaluation = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=openai_api_key,
        max_retries=10,
        request_timeout=120
    )
    logger.info(f"LLM para avaliação: {llm_for_evaluation.model_name} com max_retries={llm_for_evaluation.max_retries}")
    logger.info(f"Embeddings para avaliação: {embeddings_for_evaluation.model} com max_retries={embeddings_for_evaluation.max_retries}")

    metrics_to_evaluate = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]
    logger.info(f"Métricas a serem avaliadas: {[m.name for m in metrics_to_evaluate]}")

    all_results_dfs = [] # Lista para armazenar DataFrames de resultados de cada batch

    num_batches = (len(df_full) + EVALUATION_BATCH_SIZE - 1) // EVALUATION_BATCH_SIZE
    logger.info(f"Processando o dataset em {num_batches} batches de até {EVALUATION_BATCH_SIZE} itens cada.")

    for i in range(num_batches):
        start_index = i * EVALUATION_BATCH_SIZE
        end_index = start_index + EVALUATION_BATCH_SIZE
        df_batch = df_full[start_index:end_index]

        logger.info(f"\n--- Processando Batch {i+1}/{num_batches} ({len(df_batch)} itens) ---")

        if df_batch.empty:
            logger.info(f"Batch {i+1} está vazio, pulando.")
            continue

        try:
            # Ragas espera um objeto Dataset do Hugging Face
            # Se for um dataset muito grande, considere usar IterableDataset para streaming
            if len(df_batch) > 10000 and False: # Exemplo de condição para usar IterableDataset (ajuste conforme necessário)
                 ragas_dataset_batch = IterableDataset.from_pandas(df_batch)
            else:
                 ragas_dataset_batch = Dataset.from_pandas(df_batch)
            logger.info(f"Batch {i+1} convertido para o formato Hugging Face Datasets.")
        except Exception as e:
            logger.error(f"Erro ao converter DataFrame do batch {i+1} para Dataset: {e}")
            continue # Pula para o próximo batch

        logger.info(f"Iniciando avaliação Ragas para o batch {i+1}. Isso pode levar algum tempo...")
        try:
            # Nota: O parâmetro batch_size dentro de evaluate refere-se a como Ragas agrupa
            # internamente as linhas do dataset fornecido para as métricas, não ao controle de taxa de API.
            # O nosso batching manual externo é para controlar a taxa de API.
            result_batch = evaluate(
                dataset=ragas_dataset_batch, # Passa apenas o batch atual
                metrics=metrics_to_evaluate,
                llm=llm_for_evaluation,
                embeddings=embeddings_for_evaluation,
                raise_exceptions=False # Continuar mesmo se um item do batch falhar
            )
            logger.info(f"Avaliação Ragas para o batch {i+1} concluída.")

            if result_batch:
                # O resultado de evaluate() quando raise_exceptions=False
                # pode ser um Dataset do Hugging Face com as colunas das métricas.
                if hasattr(result_batch, 'to_pandas'):
                    result_df_batch = result_batch.to_pandas()
                     # Adicionar as colunas originais ao lado das métricas para contexto
                    original_cols_to_merge = ['question', 'answer', 'contexts', 'ground_truth']
                    # Garante que as colunas originais do batch atual (df_batch) sejam unidas aos resultados.
                    # Precisamos resetar o índice de df_batch para garantir uma junção correta
                    # se result_df_batch não mantiver os índices originais.
                    # No entanto, to_pandas() de um Dataset HF geralmente cria um índice de range.
                    # É mais seguro assumir que a ordem é mantida e concatenar as colunas.
                    # Se result_df_batch já inclui as colunas originais, não precisa mesclar.

                    # Verifica se as colunas originais já estão no resultado do Ragas
                    # (algumas versões do Ragas podem incluí-las)
                    if not all(col in result_df_batch.columns for col in original_cols_to_merge):
                        # Se não, mescla-as. Resetar o índice é crucial para a junção correta.
                        df_batch_reset = df_batch[original_cols_to_merge].reset_index(drop=True)
                        result_df_batch_reset = result_df_batch.reset_index(drop=True)
                        merged_df = pd.concat([df_batch_reset, result_df_batch_reset], axis=1)
                        # Remove colunas duplicadas que podem surgir se Ragas já incluiu algumas originais
                        merged_df = merged_df.loc[:,~merged_df.columns.duplicated()]
                        all_results_dfs.append(merged_df)

                    else:
                        all_results_dfs.append(result_df_batch)

                    logger.info(f"Resultados do batch {i+1} adicionados.")
                else:
                    logger.warning(f"Resultado do batch {i+1} não é um objeto Dataset/DataFrame esperado. Resultado: {result_batch}")
            else:
                logger.warning(f"Avaliação Ragas para o batch {i+1} não retornou resultados.")

        except Exception as e:
            logger.error(f"Erro durante a execução da função evaluate do Ragas para o batch {i+1}: {e}", exc_info=True)

        if i < num_batches - 1: # Não esperar após o último batch
            logger.info(f"Esperando {DELAY_BETWEEN_BATCHES} segundos antes do próximo batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)

    if all_results_dfs:
        final_results_df = pd.concat(all_results_dfs, ignore_index=True)
        logger.info(f"\n--- Avaliação Completa Concluída ---")
        logger.info(f"Total de {len(final_results_df)} itens processados.")

        # Calcula e exibe as médias gerais
        logger.info("\n--- Resumo dos Resultados Ragas (Médias Gerais) ---")
        for metric in metrics_to_evaluate:
            metric_name = metric.name
            if metric_name in final_results_df.columns:
                average_score = final_results_df[metric_name].mean()
                logger.info(f"{metric_name}: {average_score:.4f}")
            else:
                logger.warning(f"Coluna da métrica '{metric_name}' não encontrada nos resultados finais.")


        logger.info(f"\nPrimeiras 5 linhas dos resultados detalhados combinados:\n{final_results_df.head().to_string()}")
        try:
            final_results_df.to_csv(RAGAS_RESULTS_CSV, index=False, sep=';')
            logger.info(f"Resultados detalhados da avaliação salvos em: {RAGAS_RESULTS_CSV}")
        except Exception as e:
            logger.error(f"Erro ao salvar os resultados detalhados combinados em CSV: {e}")
    else:
        logger.warning("Nenhum resultado foi coletado dos batches. O arquivo CSV de resultados não será gerado.")

if __name__ == '__main__':
    run_ragas_evaluation()
