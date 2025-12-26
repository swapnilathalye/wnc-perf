from fastapi import APIRouter
from pathlib import Path
from app.utils.paths import UPLOAD_DIR, OUTPUT_DIR
from app.utils.logging import logger
from app.services.files import list_files_in_folder

router = APIRouter()


@router.get("/upload/history")
def upload_history():
    """
    Return JSON list of all past uploads and their linked output_csv files.
    Includes created_at timestamp for each folder so frontend can identify latest.
    """
    history = []

    # sort folders by modification time (latest first)
    for folder in sorted(UPLOAD_DIR.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
        if folder.is_dir():
            upload_files = list_files_in_folder(folder)

            output_folder = OUTPUT_DIR / folder.name
            output_files = []
            if output_folder.exists():
                output_files = [str(f.resolve()) for f in output_folder.glob("*.csv")]

            entry = {
                "folder_name": folder.name,
                "upload_path": str(folder.resolve()),
                "upload_files": upload_files,
                "output_path": str(output_folder.resolve()) if output_folder.exists() else None,
                "output_files": output_files,
                "created_at": folder.stat().st_mtime  # ✅ add timestamp
            }
            history.append(entry)

    logger.info("📄 Upload history endpoint returned %d entries", len(history))
    return {"history": history}
