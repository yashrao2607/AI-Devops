import logging
import re
import sys
from typing import Any

# Patterns to mask sensitive information
SECRET_PATTERNS = [
    re.compile(r"(AIza[0-9A-Za-z-_]{35})"),           # Google API Key
    re.compile(r"(gsk_[0-9A-Za-z]{48,})"),            # Groq API Key
    re.compile(r"(ghp_[0-9A-Za-z]{36,})"),            # GitHub Token
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
    re.compile(r"(key|token|secret|password)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{8,})['\"]?", re.IGNORECASE)
]

class SensitiveDataRedactor(logging.Formatter):
    """Custom logging formatter that automatically masks secret tokens and keys."""
    
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub(r"***REDACTED_SECRET***", redacted)
        return redacted

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("deploysafe")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        formatter = SensitiveDataRedactor(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(module)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()
