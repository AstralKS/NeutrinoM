-- Migration 001: Enable pgvector and create documents table
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT        NOT NULL,
    source_name     TEXT        NOT NULL,
    source_type     TEXT        NOT NULL,
    published_at    TIMESTAMPTZ NOT NULL,
    source_weight   FLOAT       NOT NULL,
    raw_text        TEXT        NOT NULL,
    clean_text      TEXT        NOT NULL,
    content_hash    TEXT        NOT NULL UNIQUE,
    inserted_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_published_at ON documents(published_at);
