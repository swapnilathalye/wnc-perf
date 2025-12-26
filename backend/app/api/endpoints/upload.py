import datetime
import json
import logging
import shutil
import subprocess
import zipfile
from pathlib import Path
from app.services.database import import_csv_to_sqlite

from fastapi import APIRouter, UploadFile, File

from app.utils.paths import (
    UPLOAD_DIR,
    OUTPUT_DIR,
    JAVA_DIR,
    ACTIVE_TABLES_PATH,
    PROPERTY_DIR,
    SERVER_LOGS_DIR,
)


router = APIRouter()
logger = logging.getLogger(__name__)


def _create_upload_folder_name() -> str:
    today = datetime.datetime.now().strftime("%Y%m%d")
    existing = [f for f in UPLOAD_DIR.glob(f"{today}_upload*") if f.is_dir()]
    return f"{today}_upload{len(existing) + 1}"


def _save_upload_to_disk(file: UploadFile, dest_path: Path) -> None:
    logger.info("💾 [UPLOAD] Saving uploaded file to: %s", dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


def _extract_zip(zip_path: Path, extract_to: Path) -> None:
    logger.info("🧩 [UPLOAD] Extracting zip: %s -> %s", zip_path, extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    logger.info("✅ [UPLOAD] Zip extraction completed")


def _iter_files(root: Path):
    yield from (p for p in root.rglob("*") if p.is_file())


def _move_matching_files(extract_root: Path, folder_name: str, ext: str, target_root: Path) -> int:
    """
    Moves files with given extension directly under:
      target_root/<folder_name>/
    (Subfolders inside the zip are NOT preserved.)
    """
    moved = 0
    dest_base = target_root / folder_name
    dest_base.mkdir(parents=True, exist_ok=True)

    for f in _iter_files(extract_root):
        if f.suffix.lower() != ext.lower():
            continue

        dest = dest_base / f.name  # FLATTEN (no nested folder like "test/")

        logger.info("📁 [UPLOAD] Moving %s file: %s -> %s", ext, f, dest)
        try:
            if dest.exists():
                dest.unlink()
            shutil.move(str(f), str(dest))
            moved += 1
        except Exception as e:
            logger.error("❌ [UPLOAD] Failed moving %s file %s: %s", ext, f, e)

    logger.info("✅ [UPLOAD] Moved %d '%s' files to %s", moved, ext, dest_base)
    return moved


def _find_jmxdata_gz(extract_root: Path) -> Path | None:
    """
    Finds JMXData.gz anywhere under extract_root (case-insensitive).
    Returns first match.
    """
    logger.info("🔎 [UPLOAD] Searching for JMXData.gz under: %s", extract_root)

    matches = [f for f in _iter_files(extract_root) if f.name.lower() == "jmxdata.gz"]
    if not matches:
        logger.warning("⚠️ [UPLOAD] No JMXData.gz found in extracted zip")
        return None

    if len(matches) > 1:
        logger.warning("⚠️ [UPLOAD] Multiple JMXData.gz found (%d). Using first: %s", len(matches), matches[0])

    logger.info("✅ [UPLOAD] Found JMXData.gz at: %s", matches[0])
    return matches[0]


def _run_java_converter(input_path: Path, output_folder: Path) -> None:
    """
    Compiles and runs the Java converter (same behavior as your original code).
    """
    logger.info("🛠️ [UPLOAD] Compiling Java converter...")
    subprocess.run(["javac", "--release", "8", f"{JAVA_DIR}/ConvertPerfToCsv.java"], check=True)

    logger.info("⚙️ [UPLOAD] Running Java converter on file: %s", input_path)
    subprocess.run(
        ["java", "-cp", str(JAVA_DIR), "ConvertPerfToCsv", str(input_path), str(output_folder)],
        check=True
    )

    logger.info("✅ [UPLOAD] Java conversion completed successfully")


def _safe_cleanup_path(path: Path) -> None:
    """
    Removes a file or directory safely (best-effort).
    """
    try:
        if not path.exists():
            return
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        logger.info("🧹 [UPLOAD] Cleaned up: %s", path)
    except Exception as e:
        logger.warning("⚠️ [UPLOAD] Cleanup failed for %s: %s", path, e)


def _load_conversion_summary(folder_path: Path) -> list[dict]:
    """
    Fallback reader for uploads/<folder>/conversion_summary.json
    Expected format:
      [
        {"tableName": "CacheStatistics", "rows": 10665},
        ...
      ]
    """
    summary_path = folder_path / "conversion_summary.json"
    if not summary_path.exists():
        logger.warning("⚠️ [UPLOAD] conversion_summary.json not found at %s", summary_path)
        return []

    try:
        with summary_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.warning("⚠️ [UPLOAD] conversion_summary.json is not a list")
            return []

        cleaned = []
        for item in data:
            if not isinstance(item, dict):
                continue
            tn = item.get("tableName")
            rw = item.get("rows", 0)
            if tn:
                cleaned.append({"tableName": str(tn), "rows": int(rw or 0)})

        logger.info("✅ [UPLOAD] Loaded %d tables from conversion_summary.json", len(cleaned))
        return cleaned
    except Exception as e:
        logger.error("❌ [UPLOAD] Failed to read conversion_summary.json: %s", e)
        return []

def _extract_nested_zips(extract_root: Path):
    """
    Finds ANY .zip inside the extracted parent zip (except JMXData.gz),
    extracts them in-place, then deletes the nested zip.
    """
    nested_zips = [f for f in _iter_files(extract_root) if f.suffix.lower() == ".zip"]

    for z in nested_zips:
        logger.info("🧩 [UPLOAD] Found nested zip: %s", z)

        try:
            nested_target = z.parent / f"{z.stem}_unzipped"
            nested_target.mkdir(parents=True, exist_ok=True)

            logger.info("📦 [UPLOAD] Extracting nested zip: %s -> %s", z, nested_target)
            with zipfile.ZipFile(z, "r") as zf:
                zf.extractall(nested_target)

            logger.info("🧹 [UPLOAD] Removing nested zip after extraction: %s", z)
            z.unlink()

        except Exception as e:
            logger.error("❌ [UPLOAD] Failed extracting nested zip %s: %s", z, e)



@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    logger.info("📥 [UPLOAD] Starting upload process for file: %s", file.filename)

    # Cleanup toggles
    CLEANUP_EXTRACTED = True
    CLEANUP_UPLOADED_ZIP = True  # set False to keep original zip

    # ✅ Create folder name
    folder_name = _create_upload_folder_name()
    folder_path = UPLOAD_DIR / folder_name
    logger.info("📁 [UPLOAD] Creating upload folder: %s", folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)

    # ✅ Save uploaded zip
    uploaded_zip_path = folder_path / file.filename
    _save_upload_to_disk(file, uploaded_zip_path)

    # ✅ Extract uploaded zip into temp folder
    extract_root = folder_path / "_extracted"
    try:
        _extract_zip(uploaded_zip_path, extract_root)
    #extract nested zips
        _extract_nested_zips(extract_root)
    except zipfile.BadZipFile as e:
        logger.error("❌ [UPLOAD] Invalid zip file: %s", e)
        _safe_cleanup_path(extract_root)
        return {"message": "Invalid zip file", "error": str(e)}
    except Exception as e:
        logger.error("❌ [UPLOAD] Zip extraction failed: %s", e)
        _safe_cleanup_path(extract_root)
        return {"message": "Zip extraction failed", "error": str(e)}

    # ✅ Move .log and .properties files (flattened)
    try:
        logs_moved = _move_matching_files(extract_root, folder_name, ".log", SERVER_LOGS_DIR)
        props_moved = _move_matching_files(extract_root, folder_name, ".properties", PROPERTY_DIR)
        logger.info("📦 [UPLOAD] File routing done | logs=%d properties=%d", logs_moved, props_moved)
    except Exception as e:
        logger.error("❌ [UPLOAD] Error routing .log/.properties files: %s", e)

    # ✅ Locate JMXData.gz and pass to converter
    jmx_gz_path = _find_jmxdata_gz(extract_root)
    if not jmx_gz_path:
        logger.error("❌ [UPLOAD] JMXData.gz not found. Cannot run converter.")
        if CLEANUP_EXTRACTED:
            _safe_cleanup_path(extract_root)
        if CLEANUP_UPLOADED_ZIP:
            _safe_cleanup_path(uploaded_zip_path)
        return {"message": "JMXData.gz not found in uploaded zip", "error": "Missing JMXData.gz"}

    # ✅ Prepare output folder
    output_folder = OUTPUT_DIR / folder_name
    logger.info("📁 [UPLOAD] Creating output folder: %s", output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # ✅ Run Java converter
    try:
        _run_java_converter(jmx_gz_path, output_folder)
    except Exception as e:
        logger.error("❌ [UPLOAD] Java converter failed: %s", e)
        if CLEANUP_EXTRACTED:
            _safe_cleanup_path(extract_root)
        if CLEANUP_UPLOADED_ZIP:
            _safe_cleanup_path(uploaded_zip_path)
        return {"message": "Java converter failed", "error": str(e)}

    # ✅ Import CSVs into SQLite (FIXED INDENTATION)
    tables_info, tables = [], []
    logger.info("📊 [UPLOAD] Importing CSV files into SQLite...")

    csv_files = list(output_folder.glob("*.csv"))
    logger.info("📦 [UPLOAD] CSV files found in output folder: %d", len(csv_files))

    for csv_file in csv_files:
        logger.info("➡️ [UPLOAD] Importing CSV: %s", csv_file)
        try:
            table_name, row_count = import_csv_to_sqlite(csv_file, folder_name)
            logger.info("✅ [UPLOAD] Imported %s (%d rows)", table_name, row_count)
            tables_info.append({"tableName": str(table_name), "rows": int(row_count)})
            tables.append(str(table_name))
        except Exception as e:
            logger.error("❌ [UPLOAD] Failed to import CSV %s: %s", csv_file, e)

    # ✅ Fallback: if no CSVs registered, load conversion_summary.json
    if not tables_info:
        logger.warning("⚠️ [UPLOAD] CSV count is 0; loading conversion_summary.json fallback...")
        fallback_tables = _load_conversion_summary(folder_path)

        if fallback_tables:
            tables_info = fallback_tables
            tables = [t["tableName"] for t in tables_info]
            logger.info("✅ [UPLOAD] Using fallback conversion summary for response")
        else:
            logger.warning("⚠️ [UPLOAD] No fallback conversion summary available")

    # ✅ Write active_tables.json
    active_json = {"folder": folder_name, "tables": tables}
    logger.info("📝 [UPLOAD] Writing active_tables.json: %s", active_json)

    try:
        with open(ACTIVE_TABLES_PATH, "w", encoding="utf-8") as f:
            json.dump(active_json, f, indent=2)
        logger.info("✅ [UPLOAD] active_tables.json updated successfully")
    except Exception as e:
        logger.error("❌ [UPLOAD] Failed to write active_tables.json: %s", e)

    # ✅ Cleanup extracted temp files
    if CLEANUP_EXTRACTED:
        _safe_cleanup_path(extract_root)

    # ✅ Optional: cleanup uploaded zip too
    if CLEANUP_UPLOADED_ZIP:
        _safe_cleanup_path(uploaded_zip_path)

    logger.info("🎉 [UPLOAD] Upload process completed for folder: %s", folder_name)

    return {
        "message": f"File uploaded successfully under directory {folder_name}",
        "converter_success": True,
        "csv_count": len(tables_info),
        "tables": tables_info,
        "active_folder": folder_name,
        "active_tables": tables,
        "refresh_performance": True
    }
