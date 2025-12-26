from fastapi import APIRouter
from app.services.files import zip_output_folder
from app.utils.logging import logger

router = APIRouter()


@router.get("/download/{folder_name}")
def download_csvs(folder_name: str):
    """
    Download all CSVs from a given output folder as a zip archive.
    """
    logger.info("📦 Preparing download for folder %s", folder_name)
    return zip_output_folder(folder_name)
