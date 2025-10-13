# core/utils.py
import logging

def setup_logger(level="INFO"):
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
    )
    return logging.getLogger("MCP")
