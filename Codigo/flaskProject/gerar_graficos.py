import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define o estilo dos gráficos
sns.set_theme(style="whitegrid")

# Carrega o arquivo CSV com os resultados
try:
    df_results = pd.read_csv('ragas_evaluation_results_batched.csv', sep=';')

    # Lista de todas as métricas Ragas disponíveis no arquivo
    ragas_metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']

    # --- 1. Gráfico de Dispersão (Scatter Plot) para Precisão vs. Revocação ---
    if 'context_precision' in df_results.columns and 'context_recall' in df_results.columns:
        plt.figure(figsize=(10, 7))
        sns.scatterplot(data=df_results, x='context_recall', y='context_precision', alpha=0.7, s=100)

        # Adiciona uma linha de referência (y=x) para visualização
        plt.plot([0, 1], [0, 1], 'r--', label='Referência (Precisão = Revocação)')

        plt.title('Relação entre Precisão e Revocação do Contexto', fontsize=16)
        plt.xlabel('Revocação do Contexto (Context Recall)', fontsize=12)
        plt.ylabel('Precisão do Contexto (Context Precision)', fontsize=12)
        plt.xlim(0, 1.05)
        plt.ylim(0, 1.05)
        plt.legend()
        plt.grid(True)

        scatter_filename = 'precision_recall_scatter_plot.png'
        plt.savefig(scatter_filename)
        plt.close()
        print(f"Gráfico de dispersão '{scatter_filename}' gerado com sucesso.")
    else:
        print("Colunas 'context_precision' ou 'context_recall' não encontradas para gerar o gráfico de dispersão.")

    # --- 2. Gráficos de Distribuição para TODAS as métricas ---
    print("\n--- Gerando gráficos de distribuição para todas as métricas ---")

    # Dicionário para títulos amigáveis
    metric_titles = {
        'faithfulness': 'Distribuição da Fidelidade (Faithfulness)',
        'answer_relevancy': 'Distribuição da Relevância da Resposta (Answer Relevancy)',
        'context_precision': 'Distribuição da Precisão do Contexto (Context Precision)',
        'context_recall': 'Distribuição da Revocação do Contexto (Context Recall)'
    }

    for metric in ragas_metrics:
        if metric in df_results.columns:
            average_score = df_results[metric].mean()

            plt.figure(figsize=(10, 6))
            sns.histplot(df_results[metric], kde=True, bins=10, label=f'Distribuição (bins=10)', color='teal')
            plt.axvline(average_score, color='darkorange', linestyle='--', linewidth=2,
                        label=f'Média: {average_score:.4f}')

            plt.title(metric_titles.get(metric, f'Distribuição de {metric}'), fontsize=16)
            plt.xlabel('Pontuação (Score)', fontsize=12)
            plt.ylabel('Frequência', fontsize=12)
            plt.legend()

            dist_filename = f'{metric}_distribution.png'
            plt.savefig(dist_filename)
            plt.close()

            print(f"Gráfico '{dist_filename}' gerado. Média: {average_score:.4f}")
        else:
            print(f"Métrica '{metric}' não encontrada no arquivo CSV.")

    # --- 3. Exibindo resumo das médias ---
    print("\n--- Resumo das Médias de Todas as Métricas ---")
    print(df_results[ragas_metrics].mean().to_string())

except FileNotFoundError:
    print("O arquivo 'ragas_evaluation_results_batched.csv' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")