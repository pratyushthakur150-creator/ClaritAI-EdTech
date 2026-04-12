-- =====================================================================
-- Teaching Assistant Module — PostgreSQL Migration
-- Run once: python run_migration.py
-- Creates course_documents table (other TA tables created via SQLAlchemy models)
-- =====================================================================

BEGIN;

-- Course documents (PDFs, videos, PPTX — indexed into ChromaDB)
CREATE TABLE IF NOT EXISTS course_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    course_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('pdf', 'video', 'youtube', 'pptx', 'text', 'markdown')),
    original_url VARCHAR(2000),
    status VARCHAR(20) NOT NULL DEFAULT 'uploading' CHECK (status IN ('uploading', 'processing', 'indexed', 'error', 'deleted')),
    file_path VARCHAR(1000),
    file_size INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    vector_count INTEGER DEFAULT 0,
    chroma_collection VARCHAR(255),
    description TEXT,
    tags JSONB DEFAULT '[]',
    doc_metadata JSONB DEFAULT '{}',
    error_message TEXT,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_course_documents_tenant
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cd_tenant_course ON course_documents(tenant_id, course_id);
CREATE INDEX IF NOT EXISTS idx_cd_status ON course_documents(status);
CREATE INDEX IF NOT EXISTS idx_cd_type ON course_documents(document_type);

COMMIT;
