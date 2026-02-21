"""SQLAlchemy models for Cloud SQL (PostgreSQL + pgvector)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

from api_services.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    siren = Column(String(9), unique=True, nullable=False, index=True)
    name = Column(Text)
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    requests = relationship("Request", back_populates="company")
    analysis_versions = relationship("AnalysisVersion", back_populates="company")


class Request(Base):
    __tablename__ = "requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    request_type = Column(String(20))  # quick, standard, full
    status = Column(String(20), default="queued")  # queued, processing, completed, failed
    cache_hit = Column(Boolean, default=False)
    cost_eur = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="requests")


class AnalysisVersion(Base):
    __tablename__ = "analysis_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    analysis_type = Column(String(20))
    data_hash = Column(String(64))
    result_path = Column(Text)  # GCS path
    source_dates = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    company = relationship("Company", back_populates="analysis_versions")


class CacheEntry(Base):
    __tablename__ = "cache_entries"

    cache_key = Column(Text, primary_key=True)
    value = Column(JSONB, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    source_type = Column(String(30))
    created_at = Column(DateTime(timezone=True), default=now_utc)


if VECTOR_AVAILABLE:
    class DocumentEmbedding(Base):
        __tablename__ = "document_embeddings"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
        chunk_text = Column(Text, nullable=False)
        embedding = Column(Vector(768))   # text-embedding-004 dimension
        source = Column(String(50))
        created_at = Column(DateTime(timezone=True), default=now_utc)
