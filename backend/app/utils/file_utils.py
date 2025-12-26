import logging
from pathlib import Path
import os, zipfile, subprocess, json, datetime

# ✅ Dynamically resolve BASE_DIR as the parent of this file's directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ✅ Logs, uploads, and output directories under backend/
LOG_DIR = BASE_DIR / "logs"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output_csv"

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "upload.log"

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def make_incremental_upload_folder() -> tuple[Path, str]:
    """Create an incremental folder name like YYYYMMDD_uploadN under uploads."""
    today = datetime.datetime.now().strftime("%Y%m%d")
    # Find existing folders for today
    existing = [d for d in UPLOAD_DIR.glob(f"{today}_upload*") if d.is_dir()]
    next_index = len(existing) + 1
    folder_name = f"{today}_upload{next_index}"
    target_dir = UPLOAD_DIR / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created upload folder: {target_dir}")
    return target_dir, folder_name

def register_csvs_to_output(extracted_dir: Path, folder_name: str) -> Path:
    """Copy converted CSVs into output_csv/<folder_name>."""
    target_dir = OUTPUT_DIR / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for csv_file in extracted_dir.glob("*.csv"):
        target = target_dir / csv_file.name
        if target.exists():
            target.unlink()
            logger.info(f"Overwriting existing CSV: {target}")
        csv_file.replace(target)
        count += 1

    logger.info(f"Registered {count} CSV files into {target_dir}")
    return target_dir


def save_and_extract_zip(file_bytes: bytes, filename: str, target_dir: Path) -> None:
    zip_path = target_dir / filename
    logger.info(f"Saving uploaded zip to: {zip_path.resolve()}")
    with open(zip_path, "wb") as f:
        f.write(file_bytes)
    logger.info(f"Saved uploaded zip: {zip_path.resolve()}")
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_dir)
        logger.info(f"Extracted zip into: {target_dir.resolve()}")
    except Exception as e:
        logger.error(f"Failed to extract {zip_path.resolve()}: {e}")


def run_java_converter(extracted_dir: Path) -> list:
    """Run Java converter on JMXData.gz and return table summaries."""
    gz_files = list(extracted_dir.glob("*.gz"))
    if not gz_files:
        logger.info("No .gz file found in extracted directory.")
        return []

    input_file = gz_files[0]
    try:
        result = subprocess.run(
            ["java", "ConvertPerfToCsv", str(input_file), str(OUTPUT_DIR)],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Java converter stdout:\n" + result.stdout)
        logger.info("Java converter stderr:\n" + result.stderr)

        summary_file = OUTPUT_DIR / "conversion_summary.json"
        if summary_file.exists():
            with open(summary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.info("Summary file not found in " + str(OUTPUT_DIR))
            return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Java converter failed: {e}")
        return []


def get_combined_history() -> list:
    """
    Return a list of all timestamped upload folders and their matching output_csv folders.
    Each entry links upload files with converted CSVs.
    """
    history = []
    if not UPLOAD_DIR.exists():
        return history

    for folder in sorted(UPLOAD_DIR.iterdir(), reverse=True):
        if folder.is_dir():
            files = [str(f.resolve()) for f in folder.iterdir()]
            output_folder = OUTPUT_DIR / folder.name
            output_files = []
            if output_folder.exists():
                output_files = [str(f.resolve()) for f in output_folder.glob("*.csv")]

            history.append({
                "folder_name": folder.name,
                "upload_path": str(folder.resolve()),
                "upload_files": files,
                "output_path": str(output_folder.resolve()) if output_folder.exists() else None,
                "output_files": output_files
            })
    logger.info(f"Collected combined history with {len(history)} entries")
    return history



