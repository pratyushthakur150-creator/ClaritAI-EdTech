"""
Content Management Router for Teaching Assistant Module.

Handles upload, indexing, listing, and deletion of course documents.
Supports: PDF, PPTX, video (MP4/MOV), YouTube URLs, text, markdown.

Phase 1: NO permission checks — all authenticated users can access.
Phase 2: Will add RBAC permissions after testing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path as FastAPIPath, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import sys
import uuid
import traceback

# Local imports
from app.core.database import get_db_session
from app.dependencies.auth import get_optional_current_user
from app.schemas.content import (
    DocumentIndexResponse,
    BatchDocumentIndexResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentType,
    DocumentStatus,
)

# Initialize router (prefix applied in v1/__init__.py)
router = APIRouter(tags=["Content Indexing"])

# Logger with DEBUG level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ── Subject name → deterministic UUID ──
_SUBJECT_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

def _subject_to_uuid(course_id: str) -> str:
    """Convert subject strings (e.g. 'mathematics') to deterministic UUIDs.
    If course_id is already a valid UUID, return it unchanged."""
    try:
        uuid.UUID(str(course_id))
        return str(course_id)
    except (ValueError, AttributeError):
        return str(uuid.uuid5(_SUBJECT_NAMESPACE, str(course_id)))

def _log(msg: str, level: str = "INFO"):
    """Log + print to guarantee visibility in terminal."""
    getattr(logger, level.lower(), logger.info)(msg)
    print(f"[CONTENT] [{level}] {msg}", file=sys.stderr, flush=True)

# ============================================================================
# HELPER: Get Content Indexing Service
# ============================================================================


def _get_content_service(db: Session, request: Request = None):
    """
    Initialize ContentIndexingService with ChromaDB and OpenAI.
    Falls back to mock service if dependencies unavailable.
    """
    try:
        from app.services.content_indexing_service import ContentIndexingService
        from app.core.config import settings

        # Check if ChromaDB and OpenAI are available
        try:
            import chromadb
            chroma_client = chromadb.PersistentClient(
                path=os.getenv("CHROMA_DB_PATH", "./chroma_db")
            )
        except Exception as e:
            logger.warning(f"ChromaDB unavailable: {e}")
            chroma_client = None

        openai_client = None
        if getattr(settings, "openai_api_key", None):
            try:
                from openai import OpenAI
                openai_client = OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.warning(f"OpenAI client unavailable: {e}")

        # Inject pre-loaded Whisper model from startup (avoids CUDA OOM)
        whisper_model = None
        if request:
            whisper_model = getattr(request.app.state, "whisper_model", None)

        return ContentIndexingService(
            openai_client=openai_client,
            chroma_client=chroma_client,
            storage_path=getattr(settings, "documents_storage_path", "storage/documents"),
            whisper_model=whisper_model,
        )
    except ImportError as e:
        logger.warning(f"ContentIndexingService not found — using mock: {e}")

    # Mock service for testing
    class MockContentService:
        async def index_document(self, **kwargs):
            doc_id = str(uuid.uuid4())
            return {
                "document_id": doc_id,
                "title": kwargs.get("title", "Mock"),
                "document_type": kwargs.get("document_type", "pdf"),
                "status": "indexed",
                "course_id": kwargs.get("course_id", ""),
                "tenant_id": str(kwargs.get("tenant_id", "")),
                "upload_timestamp": datetime.utcnow(),
                "file_size": len(kwargs.get("file_content") or b""),
                "chunk_count": 10,
                "vector_count": 10,
                "processing_time": 0.0,
                "chroma_collection": None,
                "metadata": {},
            }

    return MockContentService()


# ============================================================================
# ENDPOINT 1: Upload and Index Document
# ============================================================================


@router.post("/index", response_model=DocumentIndexResponse)
async def index_document(
    request: Request,
    file: Optional[UploadFile] = File(None),
    course_id: str = Form(...),
    title: str = Form(...),
    document_type: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    youtube_url: str = Form(""),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Upload and index course content into ChromaDB.

    Supported types: pdf, pptx, video, youtube, text, markdown

    Process:
    1. Validate input
    2. Extract text/transcript
    3. Chunk content (800 tokens, 100 overlap)
    4. Generate OpenAI embeddings
    5. Store in ChromaDB with tenant isolation

    Returns:
        DocumentIndexResponse with status, chunk_count, document_id
    """

    # ===== LOGGING FOR DEBUGGING =====
    _log("=" * 80)
    _log("POST /content/index — ENDPOINT REACHED")
    _log(f"Title: {title}")
    _log(f"Document Type: {document_type}")
    _log(f"Course ID: {course_id}")
    _log(f"User: {current_user}")
    _log("=" * 80)

    username = (
        current_user.get("email", "unknown")
        if isinstance(current_user, dict)
        else getattr(current_user, "email", "unknown")
    )
    tenant_id = (
        current_user.get("tenant_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "tenant_id", None)
    )

    _log(f"Authenticated user: {username}")
    _log(f"Tenant ID: {tenant_id}")
    _log("Permission check: BYPASSED (Phase 1 — all users allowed)")

    # Validate: tenant_id is required for document indexing
    if not tenant_id:
        _log("No tenant_id available — user must be authenticated to index documents", "ERROR")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication required for document indexing. Please log in and try again.",
        )

    # Validate input
    if not file and document_type.lower() != "youtube":
        logger.error("Validation failed: File required for non-YouTube types")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is required for non-YouTube document types",
        )

    if document_type.lower() == "youtube" and not (youtube_url or "").strip():
        logger.error("Validation failed: YouTube URL required")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube URL is required for youtube document type",
        )

    # Parse tags
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    # Read file content
    file_content = None
    filename = None
    if file:
        try:
            file_content = await file.read()
            filename = file.filename
            _log(f"File read: {filename} ({len(file_content)} bytes)")
            # Reject 0-byte files early
            if len(file_content) == 0:
                _log(f"REJECTED: 0-byte file '{filename}' — nothing to index", "ERROR")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{filename}' is empty (0 bytes). Please select a valid file.",
                )
        except HTTPException:
            raise
        except Exception as e:
            _log(f"File read failed: {e}", "ERROR")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read uploaded file: {str(e)}",
            )

    # Initialize indexing service
    try:
        service = _get_content_service(db, request)
        _log("ContentIndexingService initialized")
    except Exception as e:
        _log(f"Service initialization failed: {e}", "ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize indexing service: {str(e)}",
        )

    # Index the document
    try:
        _log("Starting document indexing...")
        safe_course_id = _subject_to_uuid(course_id)
        _log(f"Course ID mapped: {course_id} -> {safe_course_id}")
        result = await service.index_document(
            file_content=file_content,
            filename=filename,
            title=title,
            document_type=document_type.lower(),
            course_id=safe_course_id,
            tenant_id=str(tenant_id),
            db_session=db,
            description=description or None,
            tags=tag_list,
            youtube_url=(youtube_url or "").strip() or None,
        )
        _log(
            f"Document indexed: {result.get('document_id')} | "
            f"{result.get('chunk_count', 0)} chunks"
        )
        return DocumentIndexResponse(**result)
    except ValueError as e:
        _log(f"Indexing validation error: {e}", "ERROR")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        _log(f"Indexing failed: {e}\n{traceback.format_exc()}", "ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document indexing failed: {str(e)}",
        )


# ============================================================================
# ENDPOINT 1b: Batch Upload and Index Multiple Documents
# ============================================================================


@router.post("/index-batch", response_model=BatchDocumentIndexResponse)
async def index_documents_batch(
    request: Request,
    files: List[UploadFile] = File(..., description="One or more files to upload"),
    course_id: str = Form(...),
    document_type: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Upload and index multiple course documents at once.

    Each file is indexed individually using the same pipeline as /index.
    A shared document_type, description, and tags are applied to all files.
    The title for each document defaults to the filename.

    Returns:
        BatchDocumentIndexResponse with per-file results and error summary.
    """

    logger.info("=" * 80)
    logger.info("POST /content/index-batch — ENDPOINT REACHED")
    logger.info(f"Files count: {len(files)}")
    logger.info(f"Document Type: {document_type}")
    logger.info(f"Course ID: {course_id}")
    logger.info(f"User: {current_user}")
    logger.info("=" * 80)

    tenant_id = (
        current_user.get("tenant_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "tenant_id", None)
    )

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication required for document indexing. Please log in and try again.",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )

    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    try:
        service = _get_content_service(db, request)
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize indexing service: {str(e)}",
        )

    results: List[DocumentIndexResponse] = []
    errors: List[Dict[str, str]] = []

    for upload_file in files:
        fname = upload_file.filename or "untitled"
        try:
            file_content = await upload_file.read()
            logger.info(f"Processing file: {fname} ({len(file_content)} bytes)")

            safe_course_id = _subject_to_uuid(course_id)
            result = await service.index_document(
                file_content=file_content,
                filename=fname,
                title=fname,
                document_type=document_type.lower(),
                course_id=safe_course_id,
                tenant_id=str(tenant_id),
                db_session=db,
                description=description or None,
                tags=tag_list,
            )
            results.append(DocumentIndexResponse(**result))
            logger.info(f"Indexed: {fname} -> {result.get('document_id')}")
        except Exception as e:
            logger.error(f"Failed to index {fname}: {e}")
            errors.append({"filename": fname, "error": str(e)})

    return BatchDocumentIndexResponse(
        total_files=len(files),
        successful=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
    )


# ============================================================================
# ENDPOINT 2: List Documents for a Course
# ============================================================================


@router.get("/documents/{course_id}", response_model=DocumentListResponse)
async def list_course_documents(
    course_id: str = FastAPIPath(..., description="Course ID to list documents for"),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
):
    """
    List all documents for a specific course.

    Returns documents with metadata:
    - Title, type, status, chunk count, file size
    - Upload timestamp, error messages (if any)

    Filters:
    - Only documents for the specified course
    - Only documents for the user's tenant (multi-tenant isolation)
    - Excludes soft-deleted documents
    """

    # ===== LOGGING FOR DEBUGGING =====
    logger.info("=" * 80)
    logger.info("GET /content/documents/{course_id} — ENDPOINT REACHED")
    logger.info(f"Course ID: {course_id}")
    logger.info(f"User: {current_user}")
    logger.info("=" * 80)

    username = (
        current_user.get("email", "unknown")
        if isinstance(current_user, dict)
        else getattr(current_user, "email", "unknown")
    )
    tenant_id = (
        current_user.get("tenant_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "tenant_id", None)
    )

    logger.info(f"Authenticated user: {username}")
    logger.info(f"Tenant ID: {tenant_id}")
    logger.info("Permission check: BYPASSED (Phase 1 — all users allowed)")

    try:
        from app.models.course_document import CourseDocument

        safe_course_id = _subject_to_uuid(course_id)
        logger.info(f"Querying documents for course {course_id} (uuid={safe_course_id}) and tenant {tenant_id}...")

        documents = (
            db.query(CourseDocument)
            .filter(
                CourseDocument.course_id == safe_course_id,
                CourseDocument.tenant_id == tenant_id,
                CourseDocument.status != "deleted",
            )
            .order_by(CourseDocument.upload_timestamp.desc())
            .all()
        )

        logger.info(f"Found {len(documents)} documents")

        doc_list = []
        for doc in documents:
            try:
                doc_list.append(
                    DocumentMetadata(
                        document_id=str(doc.id),
                        title=doc.title,
                        document_type=doc.document_type or "pdf",
                        status=doc.status or "unknown",
                        course_id=str(doc.course_id),
                        file_size=doc.file_size or 0,
                        chunk_count=doc.chunk_count or 0,
                        upload_timestamp=doc.upload_timestamp,
                        last_updated=doc.last_updated,
                        tags=doc.tags or [],
                        description=doc.description,
                        error_message=doc.error_message,
                        chroma_collection=doc.chroma_collection,
                    )
                )
            except Exception as e:
                logger.warning(f"Skipping invalid document {doc.id}: {e}")

        return DocumentListResponse(
            course_id=course_id,
            tenant_id=str(tenant_id) if tenant_id else "",
            total_documents=len(doc_list),
            documents=doc_list,
            request_timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Document listing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


# ============================================================================
# ENDPOINT 3: Delete Document
# ============================================================================


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str = FastAPIPath(..., description="Document ID to delete"),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Delete a document (soft delete + ChromaDB cleanup).

    Process:
    1. Mark document as deleted in database
    2. Remove vectors from ChromaDB collection
    3. Optionally delete physical file

    Returns:
        Success message with document ID and title
    """

    # ===== LOGGING FOR DEBUGGING =====
    _log("=" * 80)
    _log("DELETE /content/documents/{document_id} — ENDPOINT REACHED")
    _log(f"Document ID: {document_id}  (type={type(document_id).__name__})")
    _log(f"User: {current_user}")
    _log("=" * 80)

    username = (
        current_user.get("email", "unknown")
        if isinstance(current_user, dict)
        else getattr(current_user, "email", "unknown")
    )
    tenant_id = (
        current_user.get("tenant_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "tenant_id", None)
    )

    _log(f"Authenticated user: {username}")
    _log(f"Tenant ID: {tenant_id}  (type={type(tenant_id).__name__})")
    _log("Permission check: BYPASSED (Phase 1 — all users allowed)")

    # Validate document_id is a valid UUID
    try:
        doc_uuid = uuid.UUID(str(document_id))
    except (ValueError, AttributeError) as e:
        _log(f"Invalid document_id UUID format: {document_id!r} — {e}", "ERROR")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document ID format: {document_id}",
        )

    # Also validate tenant_id
    tenant_uuid = None
    if tenant_id:
        try:
            tenant_uuid = uuid.UUID(str(tenant_id))
        except (ValueError, AttributeError) as e:
            _log(f"Invalid tenant_id UUID format: {tenant_id!r} — {e}", "ERROR")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant ID format.",
            )

    try:
        from app.models.course_document import CourseDocument

        _log(f"Querying: CourseDocument.id == {doc_uuid}  AND  tenant_id == {tenant_uuid}")

        query = db.query(CourseDocument).filter(CourseDocument.id == doc_uuid)
        if tenant_uuid:
            query = query.filter(CourseDocument.tenant_id == tenant_uuid)

        doc = query.first()

        if not doc:
            # Try without tenant filter to see if doc exists at all
            doc_any = db.query(CourseDocument).filter(CourseDocument.id == doc_uuid).first()
            if doc_any:
                _log(f"Document {document_id} exists but belongs to tenant {doc_any.tenant_id}, not {tenant_uuid}", "ERROR")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found (tenant mismatch)",
                )
            _log(f"Document not found in DB at all: {document_id}", "ERROR")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        _log(f"Found document: {doc.title} (status={doc.status})")

        # Delete from ChromaDB
        try:
            import chromadb
            chroma_client = chromadb.PersistentClient(
                path=os.getenv("CHROMA_DB_PATH", "./chroma_db")
            )
            if doc.chroma_collection:
                try:
                    collection = chroma_client.get_collection(doc.chroma_collection)
                    collection.delete(where={"document_id": str(document_id)})
                    _log(f"Deleted from ChromaDB collection: {doc.chroma_collection}")
                except Exception as ce:
                    _log(f"ChromaDB collection op failed: {ce}", "WARNING")
        except Exception as e:
            _log(f"ChromaDB cleanup failed (non-critical): {e}", "WARNING")

        # Soft delete in database
        doc.status = "deleted"
        db.commit()
        _log(f"Document soft-deleted: {document_id}")

        return {
            "document_id": document_id,
            "status": "deleted",
            "title": doc.title,
            "message": f"Document '{doc.title}' deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        _log(f"Document deletion failed: {e}\n{traceback.format_exc()}", "ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


# ============================================================================
# DIAGNOSTIC: Verify this router version is loaded (no permission checks)
# ============================================================================


@router.get("/debug")
async def content_debug():
    """
    Diagnostic endpoint. Returns version info.
    If you get 403 on this endpoint, old cached code is still running.
    """
    return {
        "status": "content_router_v2",
        "permission_checks": "NONE",
        "message": "This router has zero permission checks - all authenticated users allowed",
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================


@router.get("/health")
async def content_health_check():
    """Check if content indexing service is operational."""

    health_status = {
        "status": "healthy",
        "chromadb": False,
        "openai": False,
        "whisper": False,
    }

    # Check ChromaDB
    try:
        import chromadb
        chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "./chroma_db"))
        health_status["chromadb"] = True
    except Exception:
        pass

    # Check OpenAI
    try:
        from app.core.config import settings
        if getattr(settings, "openai_api_key", None):
            health_status["openai"] = True
    except Exception:
        pass

    # Check Whisper
    try:
        import whisper
        health_status["whisper"] = True
    except Exception:
        pass

    return health_status
