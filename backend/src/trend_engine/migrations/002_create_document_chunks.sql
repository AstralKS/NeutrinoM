-- Migration 002: Create document_chunks table with HNSW index
CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID        NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text      TEXT        NOT NULL,
    embedding       vector(1536) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- HNSW index for fast approximate nearest-neighbor search
-- Tune m and ef_construction against recall/latency before production.
-- At >500k vectors, evaluate IVFFlat.
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
