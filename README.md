# AtasUfs - Arquitetura RAG para Recuperação Contextualizada de Informações em Atas de Reunião Acadêmicas

## Sumário

- [Sobre o Projeto](#sobre-o-projeto)
  - [Objetivo Geral](#objetivo-geral)
  - [Objetivos Específicos Alcançados](#objetivos-específicos-alcançados)
  - [Resultados](#resultados)
- [Como Instalar e Executar](#como-instalar-e-executar)
  - [Pré-requisitos](#pré-requisitos)
  - [Instalação](#instalação)
  - [Executando a Aplicação](#executando-a-aplicação)
- [Exemplo de Uso](#exemplo-de-uso)
- [Solução de Problemas](#solução-de-problemas)
- [Trabalhos Futuros](#trabalhos-futuros)

## Sobre o Projeto

O AtasUfs é um sistema de gerenciamento de Atas de Reunião que utiliza Inteligência Artificial para permitir a busca semântica e conversacional em documentos acadêmicos. O projeto foi desenvolvido para o Departamento de Sistemas de Informação (DSI) da Universidade Federal de Sergipe (UFS) com o objetivo de superar as limitações das buscas textuais tradicionais, que se baseiam em correspondências exatas de palavras-chave e se mostram ineficientes diante do grande volume de atas gerado ao longo do tempo.

Utilizando uma arquitetura de Geração Aumentada por Recuperação (RAG), o sistema combina modelos de linguagem de grande escala (LLMs) como o Google Gemini com embeddings da OpenAI para compreender o contexto das perguntas dos usuários e fornecer respostas precisas e contextualizadas, baseadas diretamente no conteúdo das atas.

### Objetivo Geral

O objetivo geral do projeto foi desenvolver uma arquitetura baseada em RAG para automatizar a recuperação contextualizada de informações em atas institucionais, possibilitando consultas em linguagem natural que promovam eficiência, precisão e acessibilidade no acesso ao conhecimento registrado em documentos acadêmicos.

### Objetivos Específicos Alcançados

O projeto cumpriu com sucesso os seguintes objetivos:

- [x] **Processamento automatizado de documentos:** Implementação de um fluxo para extrair e estruturar dados de atas em formato PDF e TXT de forma eficiente.
- [x] **Busca semântica com embeddings:** Os documentos são segmentados, transformados em embeddings e armazenados em um banco de dados vetorial (ChromaDB) para permitir buscas semânticas.
- [x] **Respostas em linguagem natural:** Utilização de LLMs para interpretar as perguntas e gerar respostas coesas e contextualizadas sobre o conteúdo das atas.
- [x] **Arquitetura RAG:** Desenvolvimento de uma arquitetura RAG para fornecer aos LLMs o contexto necessário, garantindo respostas mais precisas e evitando a geração de informações não contidas nos documentos.
- [x] **API e Aplicação Web:** Criação de uma API REST com Flask para integrar os componentes do sistema e uma aplicação web com uma interface amigável para interação do usuário.
- [x] **Avaliação do modelo:** Criação de uma base de dados de perguntas e respostas para avaliar o desempenho do sistema e captura de métricas de precisão e revocação de contexto para uma análise quantitativa da proposta.

### Resultados

A avaliação do sistema foi realizada por meio de uma análise quantitativa utilizando o framework RAGAS, que gerou as seguintes métricas:

![Image](/Codigo/flaskProject/ragas_metrics_summary.png)

O gráfico acima demonstra a **alta fidelidade (0.940)** do sistema, indicando que as respostas geradas são fiéis ao conteúdo dos documentos. No entanto, a **precisão (0.441)** e o **recall (0.478)** do contexto mostram que o desafio principal reside na etapa de recuperação da informação, algo que se alinha com outros trabalhos na área.

![Image](/Codigo/flaskProject/precision_recall_scatter.png)

Este gráfico de dispersão ilustra a relação entre a precisão e o recall do contexto, com a cor indicando a fidelidade da resposta. Observa-se que a maioria dos pontos se concentra nos cantos inferior esquerdo (baixa precisão e recall) ou superior direito (alta precisão e recall), sugerindo um comportamento "tudo ou nada" do sistema de recuperação.

## Como Instalar e Executar

### Pré-requisitos

- Python 3.8+
- Git
- 4GB+ de RAM livre (para execução de modelos locais com Ollama, se utilizados)
- **Chaves de API:**
  - `OPENAI_API_KEY` para embeddings (OpenAI text-embedding-3-large).
  - `GOOGLE_API_KEY` para geração de texto com Gemini.
- PostgreSQL instalado e em execução na porta 5432.
- (Opcional) Ollama instalado e configurado para utilizar modelos de linguagem locais.

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/WalterHenri/AtasUfs.git](https://github.com/WalterHenri/AtasUfs.git)
    cd AtasUfs/Codigo/flaskProject
    ```
2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\Activate.ps1
    # Linux/macOS
    source .venv/bin/activate
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` na raiz do projeto (`Codigo/flaskProject`) e adicione suas chaves de API:
    ```env
    OPENAI_API_KEY="sk-..."
    GOOGLE_API_KEY="AIza..."
    FLASK_SECRET_KEY="uma_chave_secreta_forte_aqui"
    ```
5.  **Configure o banco de dados:**
    - Crie um banco de dados no PostgreSQL com o nome `AtasUfs`.
    - Atualize as credenciais de conexão no arquivo `AtasUfs/Codigo/flaskProject/model/database.py` se necessário.
    - Execute o script `AtasUfs/Documentacao/Banco de dados/Script.sql` para criar as tabelas do banco de dados.
6.  **(Opcional) Instale e configure o Ollama:**
    Se desejar utilizar modelos de linguagem locais, siga as instruções de instalação do [Ollama](https://ollama.com/install.sh) e baixe um modelo:
    ```bash
    # Inicie o serviço Ollama (em background)
    ollama serve &

    # Baixe um modelo (ex: deepseek-coder) em outro terminal
    ollama pull deepseek-coder
    ```

### Executando a Aplicação

Com o ambiente configurado, execute o seguinte comando na pasta `AtasUfs`:
```bash
python Codigo/flaskProject/app.py
```

A aplicação estará disponível em `http://localhost:5000`. A interface de chat, em `http://localhost:5000/chat/`, permitirá selecionar entre os modelos Gemini e Ollama.

## Exemplo de Uso

1.  **Criar nova ATA:** Acesse `http://localhost:5000/atas/new` (requer login de administrador), preencha o título e envie um arquivo `.pdf` ou `.txt`.
2.  **Conversar com as ATAs:** Acesse `http://localhost:5000/chat/`, selecione o modelo de sua preferência (Gemini ou Ollama) e faça perguntas em linguagem natural, como: *"Quais foram os pontos principais discutidos na Reunião Mensal?"*

## Solução de Problemas

  - **Erros de chave de API:** Verifique se as chaves `OPENAI_API_KEY` e `GOOGLE_API_KEY` estão configuradas corretamente no arquivo `.env`.
  - **Modelo Ollama não encontrado:** Certifique-se de que o serviço `ollama serve` está em execução e que o modelo desejado foi baixado (`ollama list`).
  - **Arquivos não processados:** Verifique as permissões das pastas `uploads/` e `vector_store/`. Garanta que os arquivos enviados são PDFs ou TXTs válidos e contêm texto extraível. Consulte os logs do Flask para mensagens de erro detalhadas.

## Trabalhos Futuros

  - [ ] Adicionar um filtro às pesquisas para permitir a inclusão de datas e assuntos, o que poderia diminuir o volume de conteúdo a ser buscado.
  - [ ] Utilizar rotas semânticas e técnicas de text-to-sql com múltiplas bases de dados para responder a perguntas temporais, como "Qual foi a última vez que...".
  - [ ] Implementar o pré-processamento da consulta do usuário, dividindo perguntas complexas em múltiplas subconsultas e aplicando o roteamento semântico para otimizar a recuperação de informações.
  - [ ] Adicionar a referência da ata utilizada ao texto gerado na aplicação web, permitindo que o usuário possa consultar o documento original para sua própria interpretação.
