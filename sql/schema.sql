CREATE TABLE tipos_host (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE hosts (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco_ip INET NOT NULL,
    descricao TEXT,
    tipo_host_id INTEGER NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hosts_tipo_host
        FOREIGN KEY (tipo_host_id)
        REFERENCES tipos_host(id)
        ON DELETE RESTRICT
);

CREATE TABLE tipos_servico (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    protocolo VARCHAR(20) NOT NULL,
    porta_padrao INTEGER,
    descricao TEXT
);

CREATE TABLE host_servicos (
    id SERIAL PRIMARY KEY,
    host_id INTEGER NOT NULL,
    tipo_servico_id INTEGER NOT NULL,
    nome VARCHAR(100),
    porta INTEGER,
    url TEXT,
    intervalo_verificacao_segundos INTEGER NOT NULL CHECK (intervalo_verificacao_segundos > 0),
    tempo_limite INTEGER NOT NULL CHECK (tempo_limite > 0),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_host_servicos_host
        FOREIGN KEY (host_id)
        REFERENCES hosts(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_host_servicos_tipo_servico
        FOREIGN KEY (tipo_servico_id)
        REFERENCES tipos_servico(id)
        ON DELETE RESTRICT
);

CREATE TABLE configuracoes_snmp (
    id SERIAL PRIMARY KEY,
    host_id INTEGER NOT NULL UNIQUE,
    versao_snmp VARCHAR(10) NOT NULL,
    comunidade VARCHAR(100) NOT NULL,
    porta_snmp INTEGER NOT NULL DEFAULT 161 CHECK (porta_snmp > 0),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_configuracoes_snmp_host
        FOREIGN KEY (host_id)
        REFERENCES hosts(id)
        ON DELETE CASCADE
);

CREATE TABLE metricas_snmp (
    id SERIAL PRIMARY KEY,
    host_id INTEGER NOT NULL,
    nome_metrica VARCHAR(100) NOT NULL,
    oid VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    data_recolha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_metricas_snmp_host
        FOREIGN KEY (host_id)
        REFERENCES hosts(id)
        ON DELETE CASCADE
);

CREATE TABLE verificacoes (
    id SERIAL PRIMARY KEY,
    host_id INTEGER,
    host_servico_id INTEGER,
    metodo_verificacao VARCHAR(30) NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('sucesso', 'falha')),
    tempo_resposta_ms INTEGER,
    mensagem_erro TEXT,
    data_verificacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_verificacoes_host
        FOREIGN KEY (host_id)
        REFERENCES hosts(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_verificacoes_host_servico
        FOREIGN KEY (host_servico_id)
        REFERENCES host_servicos(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_verificacoes_alvo
        CHECK (
            (host_id IS NOT NULL AND host_servico_id IS NULL)
            OR
            (host_id IS NULL AND host_servico_id IS NOT NULL)
        )
);

CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    host_id INTEGER,
    host_servico_id INTEGER,
    tipo_alerta VARCHAR(50) NOT NULL,
    mensagem TEXT NOT NULL,
    resolvido BOOLEAN NOT NULL DEFAULT FALSE,
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alertas_host
        FOREIGN KEY (host_id)
        REFERENCES hosts(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_alertas_host_servico
        FOREIGN KEY (host_servico_id)
        REFERENCES host_servicos(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_alertas_alvo
        CHECK (
            (host_id IS NOT NULL AND host_servico_id IS NULL)
            OR
            (host_id IS NULL AND host_servico_id IS NOT NULL)
        )
);