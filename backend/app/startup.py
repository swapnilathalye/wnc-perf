from app.utils.paths import OUTPUT_DIR
from app.services.database import import_csv_to_sqlite
from app.utils.logging import logger

def ingest_latest_folder():
    """
    On app startup, ingest all CSVs from the latest output_csv folder into SQLite.
    """
    folders = [f for f in OUTPUT_DIR.iterdir() if f.is_dir()]
    if not folders:
        logger.info("No output_csv folders found to ingest.")
        return

    latest = max(folders, key=lambda f: f.stat().st_mtime)
    logger.info("Latest folder detected: %s", latest.name)

    csv_files = list(latest.glob("*.csv"))
    if not csv_files:
        logger.info("No CSV files found in latest folder %s, skipping ingestion.", latest.name)
        return

    for csv_file in csv_files:
        import_csv_to_sqlite(csv_file, latest.name)
