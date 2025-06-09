# Sistema de Gerenciamento de ATAs com IA

Sistema para gestão de Atas de Reunião com capacidade de busca semântica e chat utilizando modelos de LLM (Google Gemini, Ollama) e embeddings OpenAI.

## Pré-requisitos

- Python 3.8+
- Git (para clonar o repositório)
- 4GB+ de RAM livre (para execução dos modelos locais Ollama, se utilizados)
- **Chaves de API:**
    - `OPENAI_API_KEY` para embeddings (OpenAI text-embedding-3-large).
    - `GOOGLE_API_KEY` para geração de texto com Gemini Pro.
- Ollama instalado e configurado (APENAS se for utilizar modelos Ollama para geração via chat).

## Instalação

1.  **Configure as Chaves de API**
    Crie um arquivo `.env` na raiz do projeto e adicione suas chaves:
    ```env
    OPENAI_API_KEY="sk-..."
    GOOGLE_API_KEY="AIza..."
    FLASK_SECRET_KEY="uma_chave_secreta_forte_aqui"
    ```

2.  **(Opcional) Instale e configure o Ollama (se for usar modelos Ollama)**
    ```bash
    # Baixe e instale o Ollama
    curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh

    # Inicie o serviço Ollama (em background)
    ollama serve &

    # Baixe um modelo (ex: deepseek-coder) em outro terminal (se for usar)
    ollama pull deepseek-r1:1.5b
    # ollama pull llama3
    ```
3.  **Clone o repositório e navegue até a pasta correta**
    ```bash
    git clone [https://github.com/WalterHenri/AtasUfs.git](https://github.com/WalterHenri/AtasUfs.git)
    cd AtasUfs/Codigo/flaskProject
    ```
4.  **Configure o ambiente virtual**
    ```bash
    python -m venv .venv
    .venv\Scripts\Activate.ps1 # em windows em linux eu nao sei
    ```
5.  **Instale as dependências**
    ```bash
    pip install -r requirements.txt
    ```
6. **Crie o banco de dados**
    Instale o PostgreSQL na porta 5432.
    Crie um banco de dados com nome: `AtasUfs`).
    Coloque suas credenciais de conexão no arquivo `AtasUfs/Codigo/flaskProject/model/database.py` isso aqui ainda não foi mudado
    Rode o `AtasUfs/Documentacao/Banco de dados/Script.sql` para criar as tabelas.

7. **Executando a aplicação**
    ```bash
    # Certifique-se que o Ollama está rodando em segundo plano SE você planeja usar um modelo Ollama.
    # flask run # Ou use o python app.py
    python Codigo/flaskProject/app.py
    ```
    A aplicação estará disponível em: `http://localhost:5000`
    A interface de chat em `http://localhost:5000/chat/` permitirá selecionar entre Gemini e modelos Ollama configurados.

    
## Exemplo de Uso

1.  Criar nova ATA (via interface web em `http://localhost:5000/atas/new`):
    - Título: Reunião Mensal
    - Arquivo: `ata_reuniao_mensal.pdf`

2.  Conversar com as ATAs (via interface web em `http://localhost:5000/chat/`):
    - Selecione o modelo (Gemini Pro / Ollama).
    - Pergunta: "Quais foram os pontos principais discutidos na Reunião Mensal?"

## Troubleshooting

### Problema: Erros de API Key (OpenAI/Google)
- Verifique se as chaves `OPENAI_API_KEY` e `GOOGLE_API_KEY` estão corretamente configuradas no arquivo `.env` na raiz do projeto.
- Certifique-se de que as chaves são válidas e têm os serviços necessários habilitados nas respectivas plataformas de nuvem.

### Problema: Erros de modelo Ollama não encontrado
- Verifique os modelos disponíveis no seu Ollama local: `ollama list`
- Baixe o modelo necessário se estiver faltando: `ollama pull nome_do_modelo` (ex: `ollama pull deepseek-r1:1.5b`)
- Certifique-se que o serviço `ollama serve` está em execução.

### Problema: Arquivos não sendo processados ou erros de embedding
- Verifique as permissões das pastas `uploads/` e `vector_store/`.
- Garanta que os arquivos enviados não estão corrompidos, são PDF ou TXT válidos, e contêm texto extraível.
- Verifique os logs da aplicação Flask para mensagens de erro detalhadas do `AtaService`.
- Arquivos muito grandes ou com formatação complexa podem levar mais tempo para processar ou, em raros casos, falhar na extração de texto.
