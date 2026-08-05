import json

from streamdeck_monitor import bootstrap


def action_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "logging": {"file": str(tmp_path / "events.jsonl")},
                "actions": {
                    "bindings": [
                        {
                            "id": "play",
                            "control": "key_1",
                            "event": "press",
                            "action": {"type": "media", "command": "play_pause"},
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_non_windows_actions_require_explicit_dry_run(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(bootstrap.os, "name", "posix")

    result = bootstrap.main(["--config", str(action_config(tmp_path))])

    assert result == 2
    assert "--dry-run-actions" in capsys.readouterr().err


def test_dry_run_starts_and_closes_monitor(tmp_path, monkeypatch):
    class Monitor:
        def __init__(self):
            self.closed = False

        def run_forever(self):
            raise KeyboardInterrupt

        def close(self):
            self.closed = True

    monitor = Monitor()
    calls = []

    def create(settings, dry_run_actions=False):
        calls.append(dry_run_actions)
        return monitor

    monkeypatch.setattr(bootstrap, "create_monitor", create)

    result = bootstrap.main(
        ["--config", str(action_config(tmp_path)), "--dry-run-actions"]
    )

    assert result == 0
    assert calls == [True]
    assert monitor.closed
