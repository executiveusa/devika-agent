import os
from src.config import Config
from src.logger import Logger
from src.synthia.config_validation import validate_runtime_config


def init_devika():
    logger = Logger()

    logger.info("Initializing Devika...")
    logger.info("checking configurations...")
    
    config = Config()
    validation = validate_runtime_config(strict=os.getenv("SYNTHIA_STRICT_RUNTIME", "false").lower() == "true")
    for warning in validation.warnings:
        logger.warning(f"Runtime config warning: {warning}")
    if not validation.ok:
        for error in validation.errors:
            logger.error(f"Runtime config error: {error}")
        raise RuntimeError("Runtime configuration validation failed")

    sqlite_db = config.get_sqlite_db()
    screenshots_dir = config.get_screenshots_dir()
    pdfs_dir = config.get_pdfs_dir()
    projects_dir = config.get_projects_dir()
    logs_dir = config.get_logs_dir()

    logger.info("Initializing Prerequisites Jobs...")
    os.makedirs(os.path.dirname(sqlite_db), exist_ok=True)
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(pdfs_dir, exist_ok=True)
    os.makedirs(projects_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    from src.bert.sentence import SentenceBert

    logger.info("Loading sentence-transformer BERT models...")
    prompt = "Light-weight keyword extraction exercise for BERT model loading.".strip()
    SentenceBert(prompt).extract_keywords()
    logger.info("BERT model loaded successfully.")
