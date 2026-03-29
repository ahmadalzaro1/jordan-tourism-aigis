import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import ETLLog
from app.etl.pipeline import run_etl
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    dataset_type: str = Form(...),
    db: Session = Depends(get_db),
):
    if dataset_type not in ["visitors", "occupancy", "site_visits", "hotels", "sites"]:
        raise HTTPException(400, f"Invalid dataset_type: {dataset_type}")

    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "File must be a CSV")

    os.makedirs(settings.etl_upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]
    filepath = os.path.join(settings.etl_upload_dir, f"{file_id}_{file.filename}")

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    try:
        result = run_etl(filepath, dataset_type, db)
        log = ETLLog(
            filename=file.filename,
            dataset_type=dataset_type,
            records_processed=result["processed"],
            records_inserted=result["inserted"],
            records_skipped=result["skipped"],
            records_errored=result["errored"],
            status=result["status"],
            error_details=result.get("error_details"),
            imported_at=datetime.utcnow().isoformat(),
        )
        db.add(log)
        db.commit()
        return {
            "status": result["status"],
            "processed": result["processed"],
            "inserted": result["inserted"],
            "skipped": result["skipped"],
            "errored": result["errored"],
            "errors": result.get("errors", []),
        }
    except Exception as e:
        log = ETLLog(
            filename=file.filename,
            dataset_type=dataset_type,
            status="failed",
            error_details=str(e),
            imported_at=datetime.utcnow().isoformat(),
        )
        db.add(log)
        db.commit()
        raise HTTPException(500, f"ETL failed: {str(e)}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@router.get("/logs")
def get_etl_logs(db: Session = Depends(get_db)):
    logs = db.query(ETLLog).order_by(ETLLog.id.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "filename": l.filename,
            "dataset_type": l.dataset_type,
            "records_processed": l.records_processed,
            "records_inserted": l.records_inserted,
            "records_skipped": l.records_skipped,
            "records_errored": l.records_errored,
            "status": l.status,
            "error_details": l.error_details,
            "imported_at": l.imported_at,
        }
        for l in logs
    ]
