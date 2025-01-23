CREATE TABLE Atas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    data_reuniao DATE NOT NULL,
    participantes TEXT[] NOT NULL,
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

CREATE TABLE ChatPrompts (
    id SERIAL PRIMARY KEY,
    ata_id INT REFERENCES Atas(id) ON DELETE CASCADE,
    user_id INT REFERENCES Users(id) ON DELETE SET NULL,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    modelo_llm VARCHAR(50) DEFAULT 'llama2',
    tokens_utilizados INT,
    data_interacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sessao_id UUID NOT NULL,
    metadata TEXT
);

-- Índices para otimização
CREATE INDEX idx_ata_id ON ChatPrompts(ata_id);
CREATE INDEX idx_sessao_id ON ChatPrompts(sessao_id);
CREATE INDEX idx_data_interacao ON ChatPrompts(data_interacao);

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ata_modtime
BEFORE UPDATE ON Atas
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();