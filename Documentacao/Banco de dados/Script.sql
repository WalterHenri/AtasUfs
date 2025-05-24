CREATE TABLE Atas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    conteudo TEXT NOT NULL,
    caminho_arquivo VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    departamento VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para armazenar as conversas individuais
CREATE TABLE Conversations (
    id UUID PRIMARY KEY,
    user_id INT REFERENCES Users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de prompts/mensagens, agora ligada a uma conversa
CREATE TABLE ChatPrompts (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES Conversations(id) ON DELETE CASCADE NOT NULL,
    user_id INT REFERENCES Users(id) ON DELETE SET NULL,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    modelo_llm VARCHAR(50) DEFAULT 'llama2',
    tokens_utilizados INT,
    data_interacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- O campo 'metadata' foi removido por não estar em uso, mas pode ser adicionado se necessário
);

-- Índices para otimização
CREATE INDEX idx_conversation_id ON ChatPrompts(conversation_id);
CREATE INDEX idx_user_id_conversations ON Conversations(user_id);

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Gatilho para a tabela Conversations
CREATE TRIGGER update_conversation_modtime
BEFORE UPDATE ON Conversations
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();

-- Índices para otimização

CREATE INDEX idx_data_interacao ON ChatPrompts(data_interacao);


CREATE TRIGGER update_ata_modtime
BEFORE UPDATE ON Atas
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();


ALTER TABLE Users ADD COLUMN password VARCHAR(255);
ALTER TABLE Users ADD COLUMN active BOOLEAN;
ALTER TABLE Users ADD COLUMN fs_uniquifier VARCHAR(255) UNIQUE;

-- Create the Role table
CREATE TABLE Role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) UNIQUE NOT NULL,
    description VARCHAR(255)
);

-- Create the Roles_Users link table
CREATE TABLE Roles_Users (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Users(id),
    role_id INTEGER REFERENCES Role(id)
);