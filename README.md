# Sistema de Gerenciamento de ATAs com IA

Sistema para gestão de Atas de Reunião com capacidade de busca semântica e chat utilizando modelos de LLM via Ollama.

## Pré-requisitos

- Python 3.8+
- Ollama instalado e configurado
- Git (para clonar o repositório)
- 4GB+ de RAM livre (para execução dos modelos)

## Instalação

1. **Instale e configure o Ollama**
   ```bash
   # Baixe e instale o Ollama
   curl -fsSL https://ollama.com/install.sh | sh

   # Inicie o serviço Ollama
   ollama serve

   # Baixe o modelo necessário (em outro terminal)
   ollama pull deepseek-r1:1.5b 
   ```
2. **Clone o repositório**

    ```bash 
    git clone https://github.com/WalterHenri/AtasUfs.git
    cd AtasUFS
    ```
3. **Configure o ambiente virtual**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate  # Windows
    ```
4. **Instale as dependências**

    ```bash
    pip install -r requirements.txt
    ```

5. **Configure as pastas necessárias**

    ```bash
    mkdir uploads
    mkdir vector_store
    ```
   
5. **Crie o banco de dados**

    instale o postgresql na porta 5432 e rode o Script.sql para gerar o banco de dados
    preencha sua string de conexão em database.py (requer ser automatizado)

6. **Executando a aplicação**

    ```bash
    # Inicie o servidor Flask
    python app.py
    # A aplicação estará disponível em: http://localhost:5000
    ```

# Rotas Principais

## ATAs

    GET /atas/ - Lista todas as ATAs

    POST /atas/ - Cria nova ATA (com upload de arquivo)
    
    GET /atas/<id> - Mostra detalhes de uma ATA

    GET /atas/search?q=<query> - Busca semântica nas ATAs

## Chat

    POST /chat/ - Envia uma pergunta
    
    GET /chat/history/<session_id> - Recupera histórico do chat

## Exemplo de Uso

1.  Criar nova ATA:
    ```bash
    curl -X POST -F "file=@ata.pdf" -F "titulo=Reunião Mensal" \
      -F "data_reunião=2024-03-15" http://localhost:5000/atas/
    ```
2. Conversar com a ATA: 
    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"ata_id": 1, "pergunta": "Quais foram os pontos principais discutidos?"}' \
      http://localhost:5000/chat/
   ```

Requisitos do Sistema
Garanta que o Ollama está rodando em segundo plano

4GB+ de RAM disponível para processamento dos modelos

500MB+ de espaço livre para armazenamento de vetores

# Troubleshooting

## Problema: Erros de modelo não encontrado

### Verifique os modelos disponíveis
 ```bash
ollama list
 ```

### Baixe o modelo necessário

 ```bash
ollama pull deepseek-r1:1.5b
 ```


## Problema: Arquivos não sendo processados

### Verifique as permissões das pastas uploads/ e vector_store/

### Garanta que os arquivos enviados não estão corrompidos e possuem texto