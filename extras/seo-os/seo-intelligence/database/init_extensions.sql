-- Initialize PostgreSQL extensions for Competitive Intelligence Maximizer

-- Enable pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for common queries
-- (Tables will be created by SQLAlchemy, but we set up extensions first)

COMMENT ON EXTENSION vector IS 'Vector similarity search for semantic analysis';
COMMENT ON EXTENSION pg_trgm IS 'Trigram matching for fuzzy text search';
