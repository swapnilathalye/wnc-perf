import shutil
import zipfile
import io
from pathlib import Path
from fastapi.responses import StreamingResponse
from app.utils.paths import UPLOAD_DIR, OUTPUT_DIR, LOG_DIR, DB_DIR
from app.utils.logging import logger


def ensure_directories():
    """
    Ensure all required directories exist.
    """
    for d in [UPLOAD_DIR, OUTPUT_DIR, LOG_DIR, DB_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("📂 Verified directories exist: uploads, output_csv, logs, db")


def save_uploaded_file(upload_file, dest_path: Path):
    """
    Save an uploaded file to the given destination path.
    """
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    logger.info("📥 Saved uploaded file %s", dest_path.name)
    return str(dest_path.resolve())


def zip_output_folder(folder_name: str):
    """
    Create a zip archive of all CSVs in the given output folder.
    Returns a StreamingResponse for FastAPI.
    """
    output_folder = OUTPUT_DIR / folder_name
    if not output_folder.exists():
        logger.error("❌ Output folder %s not found", folder_name)
        return {"error": "Folder not found"}

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for csv_file in output_folder.glob("*.csv"):
            zipf.write(csv_file, arcname=csv_file.name)
    zip_buffer.seek(0)

    logger.info("📦 Created zip archive for folder %s", folder_name)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={folder_name}.zip"}
    )


def clear_directory(path: Path):
    """
    Delete all contents of a directory and recreate it.
    """
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    logger.info("🗑️ Cleared directory %s", path)


def list_files_in_folder(folder: Path):
    """
    List all files in a folder.
    """
    if not folder.exists():
        logger.warning("⚠️ Folder %s does not exist", folder)
        return []
    files = [str(f.resolve()) for f in folder.iterdir() if f.is_file()]
    logger.info("📄 Listed %d files in folder %s", len(files), folder)
    return files
