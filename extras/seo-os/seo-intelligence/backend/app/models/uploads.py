"""
Database models for file uploads and normalized data
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, JSON, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Upload(Base):
    """
    Tracks all Ahrefs file uploads
    """
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Upload metadata
    source_domain = Column(String(255), nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=False, index=True)
    report_type = Column(String(50), nullable=False, index=True)

    # File info
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    file_size_bytes = Column(Integer)

    # Processing status
    processing_status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    error_message = Column(Text)

    # Data info
    row_count = Column(Integer)
    column_count = Column(Integer)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)

    # Metadata (JSONB)
    metadata = Column(JSON)  # Stores date ranges, column names, etc.

    # Relationships
    organic_keywords = relationship("OrganicKeyword", back_populates="upload", cascade="all, delete-orphan")
    backlinks = relationship("Backlink", back_populates="upload", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_upload_user_domain', 'user_id', 'source_domain'),
        Index('idx_upload_type_status', 'report_type', 'processing_status'),
    )


class OrganicKeyword(Base):
    """
    Normalized Organic Keywords data
    """
    __tablename__ = "organic_keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core keyword data
    keyword = Column(Text, nullable=False, index=True)
    country = Column(String(10))

    # Position data
    position = Column(Integer, index=True)
    previous_position = Column(Integer)
    position_change = Column(Integer)

    # Metrics
    volume = Column(Integer, index=True)
    difficulty = Column(Integer)
    cpc = Column(Float)

    # Traffic
    traffic = Column(Float)
    previous_traffic = Column(Float)
    traffic_change = Column(Float)

    # URL
    url = Column(Text)
    previous_url = Column(Text)

    # Clustering
    parent_topic = Column(Text, index=True)
    parent_topic_volume = Column(Integer)

    # Intent flags
    branded = Column(Boolean, index=True)
    local = Column(Boolean)
    navigational = Column(Boolean)
    informational = Column(Boolean, index=True)
    commercial = Column(Boolean, index=True)
    transactional = Column(Boolean, index=True)

    # Lists
    entities = Column(ARRAY(Text))
    serp_features = Column(ARRAY(Text))
    intents = Column(ARRAY(Text))
    languages = Column(ARRAY(Text))

    # Dates
    current_date = Column(DateTime)
    previous_date = Column(DateTime)

    # For semantic analysis (pgvector)
    # keyword_embedding = Column(Vector(1536))  # Will add after pgvector setup

    # Relationships
    upload = relationship("Upload", back_populates="organic_keywords")

    # Indexes
    __table_args__ = (
        Index('idx_keyword_upload', 'upload_id', 'keyword'),
        Index('idx_keyword_parent_topic', 'parent_topic'),
        Index('idx_keyword_position', 'position'),
        Index('idx_keyword_intent', 'informational', 'commercial', 'transactional'),
    )


class Backlink(Base):
    """
    Normalized Backlinks data
    """
    __tablename__ = "backlinks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)

    # URLs
    referring_page_url = Column(Text, nullable=False)
    referring_domain = Column(String(255), index=True)
    target_url = Column(Text, nullable=False, index=True)

    # Anchor
    anchor = Column(Text, index=True)
    left_context = Column(Text)
    right_context = Column(Text)

    # Metrics
    domain_rating = Column(Integer, index=True)
    url_rating = Column(Integer)
    referring_page_traffic = Column(Float)
    referring_domain_traffic = Column(Float)

    # Link attributes
    link_type = Column(String(20))  # dofollow, nofollow, ugc, sponsored
    nofollow = Column(Boolean)
    ugc = Column(Boolean)
    sponsored = Column(Boolean)

    # Status
    lost = Column(Boolean, index=True)
    lost_status = Column(String(50))

    # Dates
    first_seen = Column(DateTime, index=True)
    last_seen = Column(DateTime)
    lost_date = Column(DateTime)

    # Relationships
    upload = relationship("Upload", back_populates="backlinks")

    # Indexes
    __table_args__ = (
        Index('idx_backlink_domain', 'referring_domain'),
        Index('idx_backlink_target', 'target_url'),
        Index('idx_backlink_dr', 'domain_rating'),
        Index('idx_backlink_dates', 'first_seen', 'last_seen'),
    )


class ReferringDomain(Base):
    """
    Normalized Referring Domains data
    """
    __tablename__ = "referring_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Domain
    domain = Column(String(255), nullable=False, index=True)
    domain_rating = Column(Integer, index=True)

    # Metrics
    dofollow_ref_domains = Column(Integer)
    dofollow_linked_domains = Column(Integer)
    traffic = Column(Float)
    keywords = Column(Integer)

    # Links to target
    links_to_target = Column(Integer)
    new_links = Column(Integer)
    lost_links = Column(Integer)
    dofollow_links = Column(Integer)

    # Dates
    first_seen = Column(DateTime, index=True)
    lost_date = Column(DateTime)

    # Indexes
    __table_args__ = (
        Index('idx_referring_domain', 'domain'),
        Index('idx_referring_dr', 'domain_rating'),
    )


class SERPOverview(Base):
    """
    Normalized SERP Overview data
    """
    __tablename__ = "serp_overview"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Keyword
    keyword = Column(Text, nullable=False, index=True)
    parent_topic = Column(Text, index=True)
    parent_topic_volume = Column(Integer)

    # Result
    url = Column(Text)
    domain = Column(String(255), index=True)
    position = Column(Integer, index=True)

    # Result type
    result_type = Column(String(50), index=True)  # organic, people_also_ask, featured_snippet, etc.
    title = Column(Text)

    # Metrics
    domain_rating = Column(Integer)
    url_rating = Column(Integer)
    backlinks = Column(Integer)
    referring_domains = Column(Integer)
    traffic = Column(Float)

    # SERP features
    serp_features = Column(ARRAY(Text))

    # Indexes
    __table_args__ = (
        Index('idx_serp_keyword', 'keyword'),
        Index('idx_serp_domain', 'domain'),
        Index('idx_serp_type', 'result_type'),
    )
