"""Pipeline logging — console + a rotating-free plain file under data/.

Never logs secret values (API keys are never touched by this module and
never appear in any log call in the pipeline).
"""

import logging
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "pipeline.log"


def configure_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("lead_pipeline")
    if logger.handlers:
        return logger  # already configured (e.g. re-imported in tests)

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
