# gerar_dataset_ragas.py (VERSÃO CORRIGIDA)

import os
import pandas as pd
from dotenv import load_dotenv
import time  # <--- 1. Importe a biblioteca 'time'

from Codigo.flaskProject.app import app
from service.ata_service import AtaService
from service.chat_service import ChatService

load_dotenv()


def gerar_dataset_corrigido():
    """
    Função corrigida para gerar o dataset com tratamento de erros e prevenção de rate limit.
    """
    perguntas_e_ground_truths = [
        # ... (sua lista de 20 perguntas continua a mesma aqui)
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
            "question": "“Sempre há uma data de entrega para a prova, se o aluno faltar no dia, qual o procedimento?”",
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
    dataset_list = []

    with app.app_context():
        ata_service = AtaService()
        chat_service = ChatService(ata_service)
        modelo_selecionado = 'gemini-2.0-flash-lite'
        qa_chain = chat_service._get_qa_chain(modelo_selecionado)
        retriever = qa_chain.retriever

        print("Iniciando a geração do dataset...")

        # --- 2. Use 'enumerate' para rastrear o número da pergunta ---
        for i, item in enumerate(perguntas_e_ground_truths):
            question = item["question"]
            # Adicionado o número da pergunta para facilitar a depuração
            print(f"--- Processando pergunta {i + 1}/{len(perguntas_e_ground_truths)}: {question} ---")

            # --- 3. Adicione o bloco try...except ---
            try:
                retrieved_docs = retriever.invoke(question)
                contexts = [doc.page_content for doc in retrieved_docs]

                result = qa_chain.invoke({"query": question})
                answer = result.get("result", "Erro ao extrair 'result' da resposta.")

                dataset_list.append({
                    "question": question,
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": item["ground_truth"]
                })
                print("Pergunta processada com sucesso.")

            except Exception as e:
                # Se qualquer erro ocorrer, ele será capturado aqui
                print(f"\n!!!!!! OCORREU UM ERRO NA PERGUNTA {i + 1} !!!!!!!")
                print(f"Erro: {e}\n")


            # --- 4. Adicione um atraso para evitar 'rate limits' ---
            # Aguarda 1 segundo antes de ir para a próxima pergunta.
            # Ajuste o valor se continuar recebendo erros de rate limit.
            time.sleep(10)

    df = pd.DataFrame(dataset_list)
    df.to_csv("ragas_evaluation_dataset.csv", index=False, sep=';')

    print("\nDataset gerado e salvo em 'ragas_evaluation_dataset.csv'")
    print(f"Total de itens no CSV: {len(df)}")  # Mostra o total de linhas geradas
    print(df.head())


if __name__ == '__main__':
    os.makedirs('./uploads', exist_ok=True)
    os.makedirs('./vector_store/atas', exist_ok=True)
    gerar_dataset_corrigido()  # Chame a função corrigida