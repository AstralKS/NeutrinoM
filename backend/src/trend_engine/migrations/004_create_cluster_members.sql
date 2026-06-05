-- Migration 004: Create cluster_members join table
CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id          UUID        NOT NULL REFERENCES topic_clusters(id) ON DELETE CASCADE,
    document_chunk_id   UUID        NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    assigned_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (cluster_id, document_chunk_id)
);
