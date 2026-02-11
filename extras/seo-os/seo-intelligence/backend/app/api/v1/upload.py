"""
File upload API for Ahrefs exports
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel
import os
import hashlib
from pathlib import Path
import pandas as pd

from app.core.database import get_db
from app.core.ahrefs_normalizer import normalize_ahrefs_export
from app.models.uploads import Upload, OrganicKeyword, Backlink, ReferringDomain, SERPOverview
from app.workers.tasks import process_upload_task

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """Response from file upload"""
    upload_id: str
    filename: str
    report_type: str
    source_domain: str
    is_primary: bool
    status: str
    message: str


class UploadStatusResponse(BaseModel):
    """Upload processing status"""
    upload_id: str
    status: str
    progress: int
    message: str
    result: Dict[str, Any] | None


@router.post("/ahrefs", response_model=UploadResponse)
async def upload_ahrefs_file(
    file: UploadFile = File(...),
    user_id: str = "",
    is_primary: bool = False,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload Ahrefs CSV/Excel export

    Args:
        file: The Ahrefs export file (CSV or XLSX)
        user_id: User identifier
        is_primary: True if this is your site (vs competitor)

    Returns:
        Upload confirmation with report type and processing status
    """

    # Validate file size
    max_size = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_size / 1024 / 1024}MB"
        )

    # Validate file type
    allowed_extensions = os.getenv("ALLOWED_EXTENSIONS", "csv,xlsx").split(",")
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save file temporarily
    upload_dir = Path(os.getenv("UPLOAD_DIR", "/tmp/competitive-intel-uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_hash = hashlib.sha256(contents).hexdigest()
    temp_path = upload_dir / f"{file_hash}.{file_ext}"

    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        # Normalize and identify report type
        normalized_df, metadata, report_type = normalize_ahrefs_export(
            str(temp_path),
            is_primary=is_primary
        )

        # Create Upload record
        upload = Upload(
            user_id=user_id,
            source_domain=metadata.get('source_domain', 'unknown'),
            is_primary=is_primary,
            report_type=report_type,
            filename=file.filename,
            file_hash=file_hash,
            file_size_bytes=len(contents),
            processing_status="processing",
            row_count=metadata.get('row_count'),
            column_count=metadata.get('column_count'),
            metadata=metadata,
        )

        db.add(upload)
        await db.commit()
        await db.refresh(upload)

        # Queue background processing
        if background_tasks:
            background_tasks.add_task(
                process_upload_data,
                upload.id,
                normalized_df,
                report_type,
                db
            )

        return UploadResponse(
            upload_id=str(upload.id),
            filename=file.filename,
            report_type=report_type,
            source_domain=metadata.get('source_domain', 'unknown'),
            is_primary=is_primary,
            status="processing",
            message=f"Upload successful. Processing {metadata.get('row_count', 0)} rows."
        )

    except ValueError as e:
        # Normalization/validation error
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Unexpected error
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


async def process_upload_data(
    upload_id: str,
    df: pd.DataFrame,
    report_type: str,
    db: AsyncSession
):
    """
    Background task to insert normalized data into database
    """
    try:
        # Get upload record
        upload = await db.get(Upload, upload_id)

        if report_type == "organic_keywords":
            await insert_organic_keywords(df, upload_id, db)

        elif report_type == "backlinks":
            await insert_backlinks(df, upload_id, db)

        elif report_type == "referring_domains":
            await insert_referring_domains(df, upload_id, db)

        elif report_type == "serp_overview":
            await insert_serp_overview(df, upload_id, db)

        # Update status
        upload.processing_status = "completed"
        await db.commit()

    except Exception as e:
        # Mark as failed
        upload.processing_status = "failed"
        upload.error_message = str(e)
        await db.commit()


async def insert_organic_keywords(df: pd.DataFrame, upload_id: str, db: AsyncSession):
    """Insert organic keywords into database"""
    records = []

    for _, row in df.iterrows():
        record = OrganicKeyword(
            upload_id=upload_id,
            keyword=row.get('keyword'),
            country=row.get('country'),
            position=row.get('position'),
            previous_position=row.get('previous_position'),
            position_change=row.get('position_change'),
            volume=row.get('volume'),
            difficulty=row.get('difficulty'),
            cpc=row.get('cpc'),
            traffic=row.get('current_organic_traffic'),
            previous_traffic=row.get('previous_organic_traffic'),
            url=row.get('current_url'),
            previous_url=row.get('previous_url'),
            parent_topic=row.get('parent_topic'),
            parent_topic_volume=row.get('parent_topic_volume'),
            branded=row.get('branded'),
            local=row.get('local'),
            navigational=row.get('navigational'),
            informational=row.get('informational'),
            commercial=row.get('commercial'),
            transactional=row.get('transactional'),
            entities=row.get('entities'),
            serp_features=row.get('serp_features'),
            intents=row.get('intents'),
            languages=row.get('languages'),
        )
        records.append(record)

        # Batch insert every 1000 records
        if len(records) >= 1000:
            db.add_all(records)
            await db.commit()
            records = []

    # Insert remaining
    if records:
        db.add_all(records)
        await db.commit()


async def insert_backlinks(df: pd.DataFrame, upload_id: str, db: AsyncSession):
    """Insert backlinks into database"""
    records = []

    for _, row in df.iterrows():
        # Extract domain from URL
        referring_domain = None
        if row.get('referring_page_url'):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(row['referring_page_url'])
                referring_domain = parsed.netloc.replace('www.', '')
            except:
                pass

        record = Backlink(
            upload_id=upload_id,
            referring_page_url=row.get('referring_page_url'),
            referring_domain=referring_domain,
            target_url=row.get('target_url'),
            anchor=row.get('anchor'),
            left_context=row.get('left_context'),
            right_context=row.get('right_context'),
            domain_rating=row.get('domain_rating'),
            url_rating=row.get('url_rating'),
            referring_page_traffic=row.get('page_traffic'),
            referring_domain_traffic=row.get('domain_traffic'),
            link_type=row.get('type'),
            nofollow=row.get('nofollow'),
            ugc=row.get('ugc'),
            sponsored=row.get('sponsored'),
            lost=row.get('lost_status'),
            first_seen=row.get('first_seen'),
            last_seen=row.get('last_seen'),
        )
        records.append(record)

        if len(records) >= 1000:
            db.add_all(records)
            await db.commit()
            records = []

    if records:
        db.add_all(records)
        await db.commit()


async def insert_referring_domains(df: pd.DataFrame, upload_id: str, db: AsyncSession):
    """Insert referring domains into database"""
    records = []

    for _, row in df.iterrows():
        record = ReferringDomain(
            upload_id=upload_id,
            domain=row.get('domain'),
            domain_rating=row.get('domain_rating'),
            dofollow_ref_domains=row.get('dofollow_ref_domains'),
            dofollow_linked_domains=row.get('dofollow_linked_domains'),
            traffic=row.get('traffic'),
            keywords=row.get('keywords'),
            links_to_target=row.get('links_to_target'),
            new_links=row.get('new_links'),
            lost_links=row.get('lost_links'),
            dofollow_links=row.get('dofollow_links'),
            first_seen=row.get('first_seen'),
            lost_date=row.get('lost'),
        )
        records.append(record)

        if len(records) >= 1000:
            db.add_all(records)
            await db.commit()
            records = []

    if records:
        db.add_all(records)
        await db.commit()


async def insert_serp_overview(df: pd.DataFrame, upload_id: str, db: AsyncSession):
    """Insert SERP overview data into database"""
    records = []

    for _, row in df.iterrows():
        # Extract domain from URL
        domain = None
        if row.get('url'):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(row['url'])
                domain = parsed.netloc.replace('www.', '')
            except:
                pass

        record = SERPOverview(
            upload_id=upload_id,
            keyword=row.get('keyword'),
            parent_topic=row.get('parent_topic'),
            parent_topic_volume=row.get('parent_topic_volume'),
            url=row.get('url'),
            domain=domain,
            position=row.get('position'),
            result_type=row.get('type'),
            title=row.get('title'),
            domain_rating=row.get('domain_rating'),
            url_rating=row.get('url_rating'),
            backlinks=row.get('backlinks'),
            referring_domains=row.get('referring_domains'),
            traffic=row.get('traffic'),
            serp_features=row.get('serp_features'),
        )
        records.append(record)

        if len(records) >= 1000:
            db.add_all(records)
            await db.commit()
            records = []

    if records:
        db.add_all(records)
        await db.commit()


@router.get("/status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get processing status of an upload
    """
    upload = await db.get(Upload, upload_id)

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    progress = 0
    if upload.processing_status == "completed":
        progress = 100
    elif upload.processing_status == "processing":
        progress = 50
    elif upload.processing_status == "failed":
        progress = 0

    return UploadStatusResponse(
        upload_id=upload_id,
        status=upload.processing_status,
        progress=progress,
        message=upload.error_message or "Processing complete",
        result={
            "row_count": upload.row_count,
            "report_type": upload.report_type,
            "source_domain": upload.source_domain,
        } if upload.processing_status == "completed" else None
    )


@router.get("/list/{user_id}")
async def list_uploads(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    List all uploads for a user
    """
    from sqlalchemy import select

    query = (
        select(Upload)
        .where(Upload.user_id == user_id)
        .order_by(Upload.uploaded_at.desc())
    )

    result = await db.execute(query)
    uploads = result.scalars().all()

    return [
        {
            "upload_id": str(upload.id),
            "filename": upload.filename,
            "report_type": upload.report_type,
            "source_domain": upload.source_domain,
            "is_primary": upload.is_primary,
            "status": upload.processing_status,
            "row_count": upload.row_count,
            "uploaded_at": upload.uploaded_at.isoformat(),
        }
        for upload in uploads
    ]
