from __future__ import annotations

from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Mapping

from streamdeck_monitor.application.settings import LoggingSettings


class _ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = record.streamdeck_entry
        details = " ".join(f"{key}={value}" for key, value in entry["details"].items())
        suffix = f" {details}" if details else ""
        return f'{entry["timestamp"]} {entry["level"]:<7} {entry["event"]}{suffix}'


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(record.streamdeck_entry, ensure_ascii=False, separators=(",", ":"))


class CombinedLoggingSink:
    def __init__(self, settings: LoggingSettings) -> None:
        level = getattr(logging, settings.level.upper())
        self._logger = logging.getLogger("streamdeck_monitor")
        self._logger.handlers.clear()
        self._logger.propagate = False
        self._logger.setLevel(level)

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(_ConsoleFormatter())
        self._logger.addHandler(console)

        try:
            log_path = Path(settings.file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=settings.max_bytes,
                backupCount=settings.backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(_JsonFormatter())
            self._logger.addHandler(file_handler)
        except OSError as error:
            print(f"log file unavailable; console logging remains active: {error}", file=sys.stderr)

    def emit(
        self,
        level: str,
        event: str,
        timestamp: datetime,
        details: Mapping[str, object],
    ) -> None:
        entry = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "event": event,
            "details": dict(details),
        }
        self._logger.log(
            getattr(logging, level.upper()),
            event,
            extra={"streamdeck_entry": entry},
        )
