import os
import pandas as pd
from dotenv import load_dotenv
from Codigo.flaskProject.app import app  # Importa a instância do Flask para ter o contexto da aplicação
from service.ata_service import AtaService
from service.chat_service import ChatService

# Carrega as variáveis de ambiente (API keys)
load_dotenv()

def gerar_dataset():
    """
    Função para gerar o dataset no formato necessário para o Ragas.
    """
    # Perguntas e respostas ideais baseadas nos seus documentos de teste
    perguntas_e_ground_truths = [
        {
            "question": "Quais candidatos tiveram suas inscrições homologadas para o concurso de professor efetivo em Computação, Algoritmos e Compiladores, e Programação, conforme a ata de 16/02/2006?",
            "ground_truth": "Na reunião de 16/02/2006, Ahmed Ali Abdalla Esmin e Eleazar Geraldo Madriz tiveram suas inscrições homologadas para as matérias de ensino Computação, Algoritmos e Compiladores, e Programação."
        },
        {
            "question": "Na reunião do Conselho de Núcleo de 10/03/2006, quem foi designado presidente da comissão examinadora do concurso para professor efetivo em Programação e Computação, Algoritmos e Compiladores?",
            "ground_truth": "A professora Leila Maciel do DCCE foi indicada como presidente da comissão examinadora para o concurso em Programação e Computação, Algoritmos e Compiladores, conforme homologado em 10/03/2006."
        },
        {
            "question": "Houve aprovação de novo concurso para professor efetivo na reunião do Conselho de Núcleo de 15 de abril de 2009?",
            "ground_truth": "Sim, na reunião de 15/04/2009, foi decidido abrir um novo concurso para professor efetivo para preencher a vaga referente à Portaria nº 243 de 30 de janeiro de 2009, antes ocupada pela professora Kalina Ramos Porto."
        },
        {
            "question": "Quando foi aprovada a versão final da reformulação do Projeto Pedagógico do Curso de Sistemas de Informação em 2010?",
            "ground_truth": "A versão final do Projeto Pedagógico do Curso de Sistemas de Informação foi aprovada por unanimidade na 5ª Reunião Ordinária do Conselho de Núcleo, em 02 de junho de 2010 (Ata Nucleo2010.05)."
        },
        {
            "question": "Qual professor foi indicado como representante do Núcleo de Sistemas de Informação para a Coordenação de Cursos na reunião de 06 de outubro de 2009?",
            "ground_truth": "O Prof. José Carlos da Silva foi indicado e aprovado por unanimidade como representante do Núcleo para a Coordenação de Cursos na reunião de 06/10/2009."
        },
        {
            "question": "Em que data o Conselho Departamental aprovou a criação do Colegiado do Curso de Bacharelado em Sistemas de Informação em 2011?",
            "ground_truth": "A criação do Colegiado do Curso de Bacharelado em Sistemas de Informação foi aprovada por unanimidade na 5ª Reunião Ordinária do Conselho Departamental em 08 de junho de 2011 (AtaDepartamento2011.05)."
        },
        {
            "question": "Quando foi a última discussão sobre a necessidade de um novo concurso para professor efetivo para as áreas de Sistemas Operacionais, Redes de Computadores e Sistemas Distribuídos, e Arquitetura de Computadores, antes de março de 2013?",
            "ground_truth": "Na 4ª Reunião Extraordinária do Conselho Departamental de 28/11/2012, foi aprovada a abertura de processo seletivo para professor efetivo para as áreas de Sistemas Operacionais, Redes de Computadores e Sistemas Distribuídos; Arquitetura de Computadores e Programação (AtaExtraOrdDepartamento2012.04)."
        },
        {
            "question": "Qual foi a deliberação sobre o Projeto Pedagógico do Curso (PPC) na reunião do Conselho Departamental de 13 de agosto de 2014?",
            "ground_truth": "Na reunião de 13/08/2014, foi aprovado por unanimidade manter as disciplinas de tópicos sem pré-requisito e a retirada do pré-requisito do Estágio Supervisionado, permitindo que o aluno realize o estágio a qualquer momento (AtaDepartamento2014.04)."
        },
        {
            "question": "Em qual reunião de 2017 o Núcleo Docente Estruturante (NDE) tratou da adequação do Projeto Pedagógico do Curso (PPC) às novas normas do sistema acadêmico (Resolução nº 14/2015/CONEPE)?",
            "ground_truth": "O NDE tratou da adequação do PPC à Resolução nº 14/2015/CONEPE na sua 1ª Reunião Ordinária de 08 de fevereiro de 2017 (AtaNDE2017.01)."
        },
        {
            "question": "Qual foi a principal pauta da 1ª Reunião Ordinária do NDE em 01 de dezembro de 2020?",
            "ground_truth": "A pauta principal foi o debate sobre medidas para diminuição dos índices de reprovação nas atividades de Trabalho de Conclusão de Curso (TCC) (AtaNDE2020.01)."
        },
        {
            "question": "Quando foi discutida a possibilidade de oferta de disciplinas na modalidade a distância (EaD) pelo Colegiado do Curso em 2017?",
            "ground_truth": "Na 1ª Reunião Ordinária do Colegiado de Curso de 11 de janeiro de 2017, foi apreciado um parecer do NDE sobre as disciplinas que poderiam ser ministradas a distância, mas ficou decidido que o NDE se reuniria para discussão e análise mais aprofundada (AtaColegiado2017.01)."
        },
        {
            "question": "Houve alguma discussão sobre a grade curricular do curso de Sistemas de Informação na reunião do Conselho Departamental de 17 de agosto de 2011?",
            "ground_truth": "A ata da reunião do Conselho Departamental de 17 de agosto de 2011 (AtaDepartamento2011.07) menciona a apreciação do parecer da coordenação de cursos a respeito do novo Projeto Pedagógico do curso de SI, indicando uma discussão sobre a grade."
        },
        {
            "question": "Qual professor foi eleito Chefe do Departamento de Sistemas de Informação na eleição ocorrida em 08 de maio de 2013?",
            "ground_truth": "Na eleição para Chefe do DSI realizada em 08 de maio de 2013, o professor Dr. Eugênio Rubens Cardoso Braz foi o primeiro nome da lista tríplice para Chefe, com 08 votos (AtaDepartamento2013.04)."
        },
        {
            "question": "Quando foi a última vez, antes de 2015, que se discutiu a reformulação do Projeto Pedagógico do Curso no Conselho Departamental?",
            "ground_truth": "O Projeto Pedagógico foi um tema central na 4ª Reunião Ordinária do Conselho Departamental em 13 de agosto de 2014 (AtaDepartamento2014.04), onde se discutiu alterações e a não exigência de pré-requisitos para disciplinas de tópicos."
        },
        {
            "question": "Qual foi a decisão sobre o pedido de afastamento do Prof. Marcos Barbosa Dósea para cursar doutorado na reunião de 15 de maio de 2014?",
            "ground_truth": "Na 3ª Reunião Ordinária do Conselho Departamental de 15/05/2014, o pedido de afastamento funcional do Prof. M.Sc. Marcos Barbosa Dósea para cursar doutorado foi aprovado por unanimidade, a partir do período letivo 2014.2 (AtaDepartamento2014.03)."
        },
        {
            "question": "Na reunião do Conselho de Núcleo de 21 de fevereiro de 2008, quais providências foram tomadas referente aos concursos para professor efetivo?",
            "ground_truth": "Na reunião de 21/02/2008 (AtaExtra Ord Nucleo2008.01), foram homologadas as inscrições dos candidatos dos concursos de Sistemas de Informação, constituídas as bancas examinadoras e sorteada a ordem de provas dos candidatos."
        },
        {
            "question": "Quando foi a última vez que houve concurso para professor efetivo para a área de Banco de Dados e Programação, conforme as atas até 2009?",
            "ground_truth": "Conforme a Ata Nucleo2009.01 de 12/01/2009, foi homologado o resultado do concurso para Professor Efetivo (Adjunto) nas matérias de ensino Banco de Dados e Programação, no qual Eugênio Rubens Cardozo Braz foi aprovado em primeiro lugar."
        },
        {
            "question": "Em que data de 2024 foi aprovada a criação do curso de Ciência de Dados e Inteligência Artificial pelo Conselho Departamental?",
            "ground_truth": "Na 1ª Reunião Ordinária do Conselho Departamental de 17 de janeiro de 2024 (Ata Departamento2024.01), foi aprovada a proposta de criação do curso de Ciência de Dados e Inteligência Artificial."
        },
        {
            "question": "Qual foi o resultado do concurso para professor efetivo do DSI (edital nº 15/2018) apreciado na reunião de 27 de março de 2019?",
            "ground_truth": "O candidato Raphael Pereira de Oliveira foi o 1º classificado com 90,03 pontos, e Igor Oliveira Vasconcelos foi o 2º classificado com 73,15 pontos, conforme apreciado na 2ª Reunião Ordinária do Conselho Departamental de 27/03/2019 (AtaDepartamento2019.02)."
        },
        {
            "question": "Houve alguma mudança na grade curricular referente à disciplina 'Tecnologias de Desenvolvimento para Internet' discutida em 2018?",
            "ground_truth": "Sim, na 9ª Reunião Ordinária do Colegiado de Curso de 12/12/2018 (AtaColegiado2018.09), foi apreciada e aprovada a alteração da disciplina optativa SINF0035 (Tecnologias de Desenvolvimento para Internet) para compor a estrutura curricular padrão, referente ao sexto período."
        }
    ]

    # Lista para armazenar os dados coletados
    dataset_list = []

    # Utiliza o contexto da aplicação Flask para acessar os serviços e configurações
    with app.app_context():
        # Instancia os serviços como na sua aplicação
        ata_service = AtaService()
        chat_service = ChatService(ata_service)

        # Seleciona o modelo a ser avaliado
        modelo_selecionado = 'gemini-1.5-flash'

        # Inicializa a cadeia de QA para ter acesso aos componentes
        qa_chain = chat_service._get_qa_chain(modelo_selecionado)
        retriever = qa_chain.retriever  # Pega o retriever final (com reranker)

        print("Iniciando a geração do dataset...")

        for item in perguntas_e_ground_truths:
            question = item["question"]
            print(f"Processando pergunta: {question}")

            # 1. Recuperar Contextos (contexts)
            # O retriever já é o `ContextualCompressionRetriever` que faz busca híbrida + reranking
            retrieved_docs = retriever.invoke(question)
            contexts = [doc.page_content for doc in retrieved_docs]

            # 2. Gerar Resposta do LLM (answer)
            # Invoca a cadeia completa para obter a resposta gerada
            result = qa_chain.invoke({"query": question})
            answer = result.get("result", "Erro ao gerar resposta.")

            # Adiciona os resultados à lista
            dataset_list.append({
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": item["ground_truth"]
            })

    # Converte a lista para um DataFrame do Pandas e salva em CSV
    df = pd.DataFrame(dataset_list)
    df.to_csv("ragas_evaluation_dataset.csv", index=False, sep=';')

    print("\nDataset gerado e salvo em 'ragas_evaluation_dataset.csv'")
    print(df.head())


if __name__ == '__main__':
    # Garante que as pastas necessárias existem
    os.makedirs('./uploads', exist_ok=True)
    os.makedirs('./vector_store/atas', exist_ok=True)
    gerar_dataset()