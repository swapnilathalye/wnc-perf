import subprocess
from pathlib import Path
from app.utils.paths import JAVA_DIR
from app.utils.logging import logger


def compile_converter() -> bool:
    """
    Compile the Java converter (ConvertPerfToCsv.java).
    Returns True if compilation succeeds, False otherwise.
    """
    try:
        logger.info("⚙️ Compiling Java converter...")
        result = subprocess.run(
            ["javac", "--release", "8", f"{JAVA_DIR}/ConvertPerfToCsv.java"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            logger.debug("javac stdout: %s", result.stdout)
        if result.stderr:
            logger.warning("javac stderr: %s", result.stderr)
        logger.info("✅ Java converter compiled successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Java converter compilation failed: %s", e.stderr)
        return False


def run_converter(input_file: Path, output_folder: Path) -> bool:
    """
    Run the Java converter on a given input file.
    Produces CSVs in the specified output folder.
    Returns True if execution succeeds, False otherwise.
    """
    try:
        logger.info("⚙️ Running Java converter for %s", input_file)
        result = subprocess.run(
            ["java", "-cp", str(JAVA_DIR), "ConvertPerfToCsv", str(input_file), str(output_folder)],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            logger.debug("java stdout: %s", result.stdout)
        if result.stderr:
            logger.warning("java stderr: %s", result.stderr)
        logger.info("✅ Java converter finished successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Java converter execution failed: %s", e.stderr)
        return False
