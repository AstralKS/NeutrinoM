-- Migration 003: Create topic_clusters table
CREATE TABLE IF NOT EXISTS topic_clusters (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    label                   TEXT,
    centroid_embedding      vector(1536) NOT NULL,
    cluster_size            INT         NOT NULL,
    weighted_doc_count_7    FLOAT       NOT NULL,
    weighted_doc_count_30   FLOAT       NOT NULL,
    weighted_doc_count_90   FLOAT       NOT NULL,
    growth_rate             FLOAT       NOT NULL,
    acceleration            FLOAT       NOT NULL,
    credibility_score       FLOAT       NOT NULL,
    source_diversity_score  FLOAT       NOT NULL,
    trend_score             FLOAT,
    classification          TEXT,
    architecture_snapshot   JSONB,
    market_stats            JSONB,
    last_updated            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_topic_clusters_trend_score ON topic_clusters(trend_score DESC);
CREATE INDEX IF NOT EXISTS idx_topic_clusters_classification ON topic_clusters(classification);
CREATE INDEX IF NOT EXISTS idx_topic_clusters_last_updated ON topic_clusters(last_updated DESC);
