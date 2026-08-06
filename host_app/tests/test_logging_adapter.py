from datetime import datetime, timezone
import json

from streamdeck_monitor.application.settings import LoggingSettings
from streamdeck_monitor.infrastructure.logging_adapter import CombinedLoggingSink


def test_writes_jsonl_and_rotates(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    sink = CombinedLoggingSink(
        LoggingSettings(level="INFO", file=str(path), max_bytes=220, backup_count=2)
    )
    timestamp = datetime(2026, 8, 4, tzinfo=timezone.utc)

    for sequence in range(10):
        sink.emit(
            "INFO",
            "input",
            timestamp,
            {"port": "COM4", "sequence": sequence},
        )

    files = sorted(tmp_path.glob("events.jsonl*"))
    assert len(files) > 1
    lines = [line for file in files for line in file.read_text().splitlines()]
    assert lines
    assert all(json.loads(line)["event"] == "input" for line in lines)


def test_keeps_console_when_file_cannot_be_opened(monkeypatch, capsys) -> None:
    def fail_to_open(*args, **kwargs):
        raise OSError("read only")

    monkeypatch.setattr(
        "streamdeck_monitor.infrastructure.logging_adapter.RotatingFileHandler",
        fail_to_open,
    )
    sink = CombinedLoggingSink(LoggingSettings(file="unavailable/events.jsonl"))
    sink.emit(
        "INFO",
        "monitor_started",
        datetime(2026, 8, 4, tzinfo=timezone.utc),
        {},
    )
    captured = capsys.readouterr()
    assert "console logging remains active" in captured.err
    assert "monitor_started" in captured.out
