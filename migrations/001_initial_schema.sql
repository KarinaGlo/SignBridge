-- migrations/001_initial_schema.sql
-- Skema Database Operasional & Telemetri PostgreSQL 16 untuk SignBridge ID-PH

CREATE TABLE IF NOT EXISTS sign_concepts (
    id SERIAL PRIMARY KEY,
    concept_code VARCHAR(16) NOT NULL UNIQUE,
    gloss VARCHAR(64) NOT NULL UNIQUE,
    bisindo_label VARCHAR(128) NOT NULL,
    fsl_label VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    description TEXT,
    phonology_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sign_concepts_category ON sign_concepts(category);

CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    model_code VARCHAR(32) NOT NULL UNIQUE,
    model_name VARCHAR(128) NOT NULL,
    modality VARCHAR(32) NOT NULL,
    version VARCHAR(32) NOT NULL,
    architecture VARCHAR(128) NOT NULL,
    model_path VARCHAR(256),
    dataset_source VARCHAR(128) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_model_versions_modality ON model_versions(modality);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id SERIAL PRIMARY KEY,
    model_version_id INTEGER NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    dataset_name VARCHAR(128) NOT NULL,
    evaluation_type VARCHAR(64) NOT NULL,
    protocol VARCHAR(64) NOT NULL,
    accuracy DOUBLE PRECISION,
    precision DOUBLE PRECISION,
    recall DOUBLE PRECISION,
    macro_f1 DOUBLE PRECISION,
    wer DOUBLE PRECISION,
    cer DOUBLE PRECISION,
    bleu DOUBLE PRECISION,
    chrf DOUBLE PRECISION,
    rtf DOUBLE PRECISION,
    latency_ms DOUBLE PRECISION,
    test_count INTEGER,
    result_path VARCHAR(256),
    details_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_eval_runs_model_type ON evaluation_runs(model_version_id, evaluation_type);

CREATE TABLE IF NOT EXISTS inference_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(64) NOT NULL,
    modality VARCHAR(32) NOT NULL,
    model_version_id INTEGER REFERENCES model_versions(id) ON DELETE SET NULL,
    room_code VARCHAR(32),
    input_summary VARCHAR(256) NOT NULL,
    output_summary VARCHAR(256) NOT NULL,
    confidence DOUBLE PRECISION,
    latency_ms DOUBLE PRECISION,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_inference_logs_endpoint ON inference_logs(endpoint);
CREATE INDEX IF NOT EXISTS ix_inference_logs_created_at ON inference_logs(created_at);

CREATE TABLE IF NOT EXISTS dataset_recordings (
    id SERIAL PRIMARY KEY,
    recording_code VARCHAR(64) NOT NULL UNIQUE,
    concept_id INTEGER REFERENCES sign_concepts(id) ON DELETE SET NULL,
    signer_id VARCHAR(32) NOT NULL,
    gloss VARCHAR(64) NOT NULL,
    repetition INTEGER NOT NULL DEFAULT 1,
    duration DOUBLE PRECISION NOT NULL DEFAULT 2.6,
    file_path VARCHAR(256),
    keypoint_path VARCHAR(256),
    consent_status VARCHAR(32) NOT NULL DEFAULT 'approved',
    validation_status VARCHAR(32) NOT NULL DEFAULT 'valid',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_dataset_recordings_signer_gloss ON dataset_recordings(signer_id, gloss);

