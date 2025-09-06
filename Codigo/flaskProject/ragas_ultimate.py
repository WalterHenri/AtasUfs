import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
import logging

# Configuração básica
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

# Configurações
BATCH_SIZE = 4  # Batch um pouco maior já que usaremos GPT-4o
DELAY_BETWEEN_BATCHES = 20  # Aumentado para GPT-4o
DELAY_BETWEEN_QUESTIONS = 8  # Aumentado para todas as 20 perguntas


class RAGEvaluator:
    def __init__(self):
        """Inicializa o avaliador RAG com configurações otimizadas"""
        self.setup_openai()
        self.setup_app_context()
        self.perguntas_e_ground_truths = self.get_perguntas_dataset()

    def setup_openai(self):
        """Configura modelos OpenAI para avaliação"""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")

        # Configuração com GPT-4o e embeddings de produção
        self.llm_evaluation = ChatOpenAI(
            model_name="gpt-4o",  # Usando GPT-4o para avaliação
            temperature=0,
            api_key=openai_api_key,
            max_retries=5,
            request_timeout=120  # Timeout maior para GPT-4o
        )

        self.embeddings_evaluation = OpenAIEmbeddings(
            model="text-embedding-3-large",  # Mesmo modelo de produção
            api_key=openai_api_key,
            max_retries=5,
            request_timeout=120
        )

        logger.info("GPT-4o e text-embedding-3-large configurados para avaliação")

    def setup_app_context(self):
        """Configura o contexto da aplicação"""
        try:
            from Codigo.flaskProject.app import app
            from service.ata_service import AtaService
            from service.chat_service import ChatService

            self.app = app
            with app.app_context():
                self.ata_service = AtaService()
                self.chat_service = ChatService(self.ata_service)
                # Use o modelo que você realmente quer avaliar aqui
                self.modelo_producao = 'gemini-2.0-flash-lite'
                self.qa_chain = self.chat_service._get_qa_chain(self.modelo_producao)
                self.retriever = self.qa_chain.retriever

            logger.info(f"App context configurado com modelo: {self.modelo_producao}")
        except ImportError as e:
            logger.error(f"Erro ao importar módulos da aplicação: {e}")
            raise

    def get_perguntas_dataset(self):
        """Dataset completo com todas as 20 perguntas"""
        return [
            {
                "question": "Quando e onde será a colação de grau da turma 2024.2?",
                "ground_truth": "Será dia 20/05/2025, às 16h, no Serviço Social do Transporte e Serviço Nacional de Aprendizagem do Transporte (Sest Senat)."
            },
            {
                "question": "Como está atualmente o saldo da Itatech Jr?",
                "ground_truth": "O relatório financeiro do período de 08/04 a 13/05 foi apresentado com saldo final de R$ 3.054,24."
            },
            {
                "question": "A disciplina Estrutura de Dados II vai ser ofertada no período 2025.1?",
                "ground_truth": "Sim, o chefe do departamento informou a inclusão da disciplina SINF0007 - Estrutura de Dados II para atender uma demanda de alunos repetentes. A disciplina foi incluída no turno da tarde devido à indisponibilidade dos alunos solicitantes no horário matutino. A retificação foi aprovada por unanimidade."
            },
            {
                "question": "Qual foi o resultado final do concurso para professor substituto do DSI?",
                "ground_truth": "Resultado final: 1º colocado – José Vinícius de Carvalho – 52,80 pontos; 2º colocado – Ericles dos Santos Cunha – 50,20 pontos; 3º colocado – Marcos Vinícius Santana Polletti – 49,80 pontos."
            },
            {
                "question": "O que é o projeto +TI, ele foi aprovado?",
                "ground_truth": "É um programa profissionalizante de tecnologia da informação (TI) projetado para capacitar jovens em busca de oportunidades no mercado de trabalho. Ele foi aprovado por unanimidade."
            },
            {
                "question": "Quando a professora May Li foi para o Dcomp, teve concurso?",
                "ground_truth": "Não, o DSI já tem um professor substituto e a realocação do prof. Antônio José Alves Neto para a nova vaga de professor substituto foi aprovada por unanimidade."
            },
            {
                "question": "Qual foi a nota obtida pela UFS no recredenciamento institucional?",
                "ground_truth": "5,0 (cinco)."
            },
            {
                "question": "Quais são as disciplinas que compõem a oferta 2024.1?",
                "ground_truth": "A oferta 2024.1 foi composta pelas disciplinas obrigatórias dos 1º, 3º, 4º, 6º e 8º períodos, além de Matemática Discreta para Computação – SINF0013 (2º período), Introdução à Ciência da Computação – SINF0010 (ofertada para o curso de Física) e a optativa Tópicos Especiais em Hardware - SINF0070."
            },
            {
                "question": "Foi aprovada a solicitação de quebra de pré-requisito para cursar Linguagens Formais e Tradutores para Natan Vinícius Santos Pereira?",
                "ground_truth": "Sim, a solicitação de quebra de pré-requisito para cursar Linguagens Formais e Tradutores para o discente Natan Vinícius Santos Pereira foi aprovada por unanimidade."
            },
            {
                "question": "Como ficou a última composição do colegiado, membros titulares, presidente, representantes discentes e etc?",
                "ground_truth": "Raphael Pereira de Oliveira (membro titular - presidente); José Aélio de Oliveira Júnior (membro titular); José Carlos da Silva (membro titular); Joseval de Melo Santana (membro titular); André Luis Meneses Silva (membro titular); Alcides Xavier Benicasa (membro titular); Marcos Barbosa Dosea (membro titular); Methanias Colaco Rodrigues Junior (membro titular); Andrés Ignácio Martínez Menéndez (membro suplente); Daiane da Silva Santos (representante discente – titular); Pedro Henrique Santana Mesquita (representante discente – titular); Yasmin Passos Alves de Araújo (representante discente – suplente); David Santos Silvino (representante discente – titular)."
            },
            {
                "question": "Geilson dos Santos teve seu prazo para conclusão de curso aprovado?",
                "ground_truth": "Sim, (dois períodos)."
            },
            {
                "question": "Tiago Santiago de Menezes conseguiu o aproveitamento do estágio obrigatório?",
                "ground_truth": "Sim, por atividade profissional exercida na empresa Prisma Digital."
            },
            {
                "question": "Sempre há uma data de entrega para a prova, se o aluno faltar no dia, qual o procedimento?",
                "ground_truth": "Seguindo as normas acadêmicas, faz-se a correção da prova e a entrega do material num dia determinado. O aluno que não recolher seu material avaliativo na data definida, poderá recolher na secretaria do departamento até o final do período corrente, onde ficará disponível uma lista com os nomes dos alunos que não recolheram ainda. Nesse caso, o aluno não terá direito de solicitar revisão, a não ser que tenha entrado em contato com o professor e alegado os motivos pelos quais não pôde estar presente."
            },
            {
                "question": "O discente Tiago Vinícius Santos Franca conseguiu aproveitamento de Trabalho de Conclusão de Curso I (TCC I)?",
                "ground_truth": "Sim, (processo 23113.042644/2024-89) mesmo em estágios iniciais do curso, ele conseguiu, visando também amenizar os riscos de retenção do discente."
            },
            {
                "question": "Como ficou o calendário 2025 de reuniões do colegiado?",
                "ground_truth": "Continuou seguindo o mesmo padrão e não houve sugestões de alteração, sempre tentando agendar as reuniões para as segundas quartas-feiras de cada mês. Somente houve uma exceção na reunião do mês de janeiro, deslocada para o dia 15 por conta das férias coletivas dos docentes."
            },
            {
                "question": "Como ficou resolvida aquela situação da Bruna Keila e do Haendel sobre a disciplina de Sistemas Operacionais?",
                "ground_truth": "Foi aprovada por unanimidade a oferta da disciplina SINF0071 - Sistemas Operacionais como ensino individual no período de recesso acadêmico (verão) para os discentes Bruna Keila Oliveira Santos e Haendel Hernan de Jesus Santos. Eles haviam frequentado como ouvintes e obtiveram nota suficiente para aprovação."
            },
            {
                "question": "Estou tentando lembrar como ficaram definidos os novos horários das aulas a partir do semestre seguinte, você tem essa informação?",
                "ground_truth": "A partir do próximo semestre letivo, o primeiro horário terá início às 7h30 e o término do último horário será às 12h30, com duração de 45min para cada aula. Os 15min restantes para completar 1 hora de aula serão reservados para atividades que os alunos desenvolvem em casa."
            },
            {
                "question": "O aluno Samuel Albert conseguiu mesmo aproveitar as atividades do PET como estágio obrigatório?",
                "ground_truth": "Sim, o aproveitamento do Estágio Supervisionado de Sistemas de Informação foi aprovado por unanimidade para o discente Samuel Albert Santos Andrade. Ele desenvolveu atividades de robótica educacional com alunos da educação básica de escolas públicas sob supervisão do prof. André Luis Meneses Silva e entregou toda documentação necessária."
            },
            {
                "question": "Como ficou definida aquela alteração na Oferta 2024.2 que estava sendo discutida?",
                "ground_truth": "Foi aprovada por unanimidade uma alteração simples na Oferta 2024.2: retirada de Programação II e inclusão de Estrutura de Dados I, nos mesmos dias e horários. A alteração envolveu apenas o prof. Alcides Benicasa e foi justificada aos membros."
            },
            {
                "question": "Quando ficou definido para ser a recepção dos calouros do DSI em 2024.1?",
                "ground_truth": "A recepção do DSI aos calouros foi definida para o dia 9 de maio (quinta-feira), às 11h. Isso foi além do evento geral de acolhimento do campus que ocorreria no dia 6 de maio, primeiro dia de aula do semestre."
            }
        ]

    def gerar_dataset_respostas(self):
        """Gera dataset com respostas do sistema RAG"""
        logger.info("Iniciando geração do dataset de respostas...")
        dataset_list = []

        with self.app.app_context():
            for i, item in enumerate(self.perguntas_e_ground_truths):
                question = item["question"]
                logger.info(f"Processando pergunta {i + 1}/{len(self.perguntas_e_ground_truths)}: {question[:50]}...")

                try:
                    # Recupera contextos relevantes
                    retrieved_docs = self.retriever.invoke(question)
                    contexts = [doc.page_content for doc in retrieved_docs]

                    # Gera resposta usando o modelo de produção
                    result = self.qa_chain.invoke({"query": question})
                    answer = result.get("result", "Erro ao extrair resposta.")

                    dataset_list.append({
                        "question": question,
                        "answer": answer,
                        "contexts": contexts,
                        "ground_truth": item["ground_truth"]
                    })

                    logger.info(f"Pergunta {i + 1} processada com sucesso")

                except Exception as e:
                    logger.error(f"Erro na pergunta {i + 1}: {e}")
                    # Adiciona entrada com erro para manter consistência
                    dataset_list.append({
                        "question": question,
                        "answer": f"ERRO: {str(e)}",
                        "contexts": [""],
                        "ground_truth": item["ground_truth"]
                    })

                # Delay para evitar rate limits
                if i < len(self.perguntas_e_ground_truths) - 1:
                    time.sleep(DELAY_BETWEEN_QUESTIONS)

        return pd.DataFrame(dataset_list)

    def avaliar_com_ragas(self, df):
        """Avalia o dataset usando RAGAS com batching otimizado"""
        logger.info("Iniciando avaliação RAGAS...")

        # Métricas a serem avaliadas
        metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
        logger.info(f"Métricas: {[m.name for m in metrics]}")

        all_results = []
        num_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"Processando {len(df)} itens em {num_batches} batches")

        for i in range(num_batches):
            start_idx = i * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(df))
            batch_df = df[start_idx:end_idx].copy()

            logger.info(f"Processando batch {i + 1}/{num_batches} ({len(batch_df)} itens)")

            try:
                # Converte para formato RAGAS
                ragas_dataset = Dataset.from_pandas(batch_df)

                # Executa avaliação
                result = evaluate(
                    dataset=ragas_dataset,
                    metrics=metrics,
                    llm=self.llm_evaluation,
                    embeddings=self.embeddings_evaluation,
                    raise_exceptions=False
                )

                if result and hasattr(result, 'to_pandas'):
                    result_df = result.to_pandas()

                    # Combina com dados originais
                    for col in ['question', 'answer', 'ground_truth']:
                        if col not in result_df.columns:
                            result_df[col] = batch_df[col].values

                    all_results.append(result_df)
                    logger.info(f"Batch {i + 1} avaliado com sucesso")

            except Exception as e:
                logger.error(f"Erro no batch {i + 1}: {e}")

            # Delay entre batches
            if i < num_batches - 1:
                logger.info(f"Aguardando {DELAY_BETWEEN_BATCHES}s antes do próximo batch...")
                time.sleep(DELAY_BETWEEN_BATCHES)

        if all_results:
            final_results = pd.concat(all_results, ignore_index=True)
            return final_results
        else:
            logger.error("Nenhum resultado foi obtido da avaliação RAGAS")
            return None

    def gerar_graficos(self, results_df):
        """Gera gráficos de análise dos resultados"""
        if results_df is None or results_df.empty:
            logger.error("Não há dados para gerar gráficos")
            return

        logger.info("Gerando gráficos de análise...")

        # Configuração do estilo
        sns.set_theme(style="whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)

        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        metric_titles = {
            'faithfulness': 'Fidelidade',
            'answer_relevancy': 'Relevância da Resposta',
            'context_precision': 'Precisão do Contexto',
            'context_recall': 'Recall do Contexto'
        }

        # 1. Gráfico de barras com médias
        available_metrics = [m for m in metrics if m in results_df.columns]
        if available_metrics:
            means = results_df[available_metrics].mean()

            plt.figure(figsize=(12, 6))
            bars = plt.bar(range(len(means)), means.values,
                           color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])

            plt.title('Média das Métricas RAGAS', fontsize=16, fontweight='bold')
            plt.xlabel('Métricas', fontsize=12)
            plt.ylabel('Pontuação', fontsize=12)
            plt.xticks(range(len(means)), [metric_titles.get(m, m) for m in means.index], rotation=45)
            plt.ylim(0, 1.05)

            # Adiciona valores nas barras
            for bar, value in zip(bars, means.values):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                         f'{value:.3f}', ha='center', va='bottom', fontweight='bold')

            plt.tight_layout()
            plt.savefig('ragas_metrics_summary.png', dpi=300, bbox_inches='tight')
            plt.close()
            logger.info("Gráfico de resumo salvo: ragas_metrics_summary.png")

        # 2. Scatter plot Precisão vs Recall
        if 'context_precision' in results_df.columns and 'context_recall' in results_df.columns:
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(results_df['context_recall'], results_df['context_precision'],
                                  alpha=0.7, s=100,
                                  c=results_df['faithfulness'] if 'faithfulness' in results_df.columns else 'blue',
                                  cmap='viridis')

            plt.plot([0, 1], [0, 1], 'r--', alpha=0.5, label='Linha de Referência')
            plt.title('Precisão vs Recall do Contexto', fontsize=16, fontweight='bold')
            plt.xlabel('Context Recall', fontsize=12)
            plt.ylabel('Context Precision', fontsize=12)
            plt.xlim(-0.05, 1.05)
            plt.ylim(-0.05, 1.05)
            plt.legend()
            plt.grid(True, alpha=0.3)

            if 'faithfulness' in results_df.columns:
                plt.colorbar(scatter, label='Fidelidade')

            plt.tight_layout()
            plt.savefig('precision_recall_scatter.png', dpi=300, bbox_inches='tight')
            plt.close()
            logger.info("Scatter plot salvo: precision_recall_scatter.png")

        # 3. Distribuições das métricas
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()

        for i, metric in enumerate(available_metrics[:4]):
            if i < len(axes) and metric in results_df.columns:
                ax = axes[i]
                data = results_df[metric].dropna()

                ax.hist(data, bins=8, alpha=0.7, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'][i])
                ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2,
                           label=f'Média: {data.mean():.3f}')
                ax.set_title(f'Distribuição - {metric_titles.get(metric, metric)}', fontweight='bold')
                ax.set_xlabel('Pontuação')
                ax.set_ylabel('Frequência')
                ax.legend()
                ax.grid(True, alpha=0.3)

        # Remove axes não utilizados
        for i in range(len(available_metrics), len(axes)):
            fig.delaxes(axes[i])

        plt.tight_layout()
        plt.savefig('metrics_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Gráfico de distribuições salvo: metrics_distributions.png")

    def imprimir_resumo(self, results_df):
        """Imprime resumo detalhado dos resultados"""
        if results_df is None or results_df.empty:
            logger.error("Não há dados para mostrar resumo")
            return

        print("\n" + "=" * 60)
        print("RESUMO DA AVALIAÇÃO RAG")
        print("=" * 60)

        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        available_metrics = [m for m in metrics if m in results_df.columns]

        if available_metrics:
            print(f"\n📊 RESULTADOS DAS MÉTRICAS:")
            for metric in available_metrics:
                data = results_df[metric].dropna()
                if not data.empty:
                    print(f"  • {metric.replace('_', ' ').title()}: {data.mean():.4f} (±{data.std():.4f})")

        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"  • Total de perguntas avaliadas: {len(results_df)}")
        print(f"  • Modelo usado na geração: {self.modelo_producao}")
        print(f"  • Modelo usado na avaliação: {self.llm_evaluation.model_name}")

        # Análise de qualidade
        if 'faithfulness' in results_df.columns and 'answer_relevancy' in results_df.columns:
            good_answers = results_df[
                (results_df['faithfulness'] >= 0.8) &
                (results_df['answer_relevancy'] >= 0.8)
                ]
            print(
                f"  • Respostas de alta qualidade: {len(good_answers)}/{len(results_df)} ({len(good_answers) / len(results_df) * 100:.1f}%)")

    def executar_avaliacao_completa(self):
        """Executa todo o pipeline de avaliação"""
        try:
            logger.info("=== INICIANDO AVALIAÇÃO RAG COMPLETA ===")

            # 1. Gerar dataset de respostas
            df_respostas = self.gerar_dataset_respostas()
            logger.info(f"Dataset gerado com {len(df_respostas)} perguntas")

            # 2. Avaliar com RAGAS
            results_df = self.avaliar_com_ragas(df_respostas)

            if results_df is not None:
                # 3. Salvar resultados
                results_df.to_csv('ragas_evaluation_results.csv', index=False, sep=';')
                logger.info("Resultados salvos em: ragas_evaluation_results.csv")

                # 4. Gerar gráficos
                self.gerar_graficos(results_df)

                # 5. Mostrar resumo
                self.imprimir_resumo(results_df)

                logger.info("=== AVALIAÇÃO COMPLETA FINALIZADA ===")
                return results_df
            else:
                logger.error("Avaliação falhou - não foi possível obter resultados")
                return None

        except Exception as e:
            logger.error(f"Erro durante a avaliação: {e}")
            raise


def main():
    """Função principal"""
    try:
        # Criar diretórios necessários
        os.makedirs('./uploads', exist_ok=True)
        os.makedirs('./vector_store/atas', exist_ok=True)

        # Executar avaliação
        evaluator = RAGEvaluator()
        results = evaluator.executar_avaliacao_completa()

        if results is not None:
            print("\n✅ Avaliação concluída com sucesso!")
            print("📁 Arquivos gerados:")
            print("  • ragas_evaluation_results.csv")
            print("  • ragas_metrics_summary.png")
            print("  • precision_recall_scatter.png")
            print("  • metrics_distributions.png")
        else:
            print("\n❌ Avaliação falhou")

    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        raise


if __name__ == '__main__':
    main()