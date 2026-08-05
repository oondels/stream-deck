import pytest

from streamdeck_monitor.domain.actions import (
    HotkeyAction,
    LaunchAction,
    MediaAction,
    OpenUrlAction,
)
from streamdeck_monitor.infrastructure.action_executors import (
    MEDIA_VK_CODES,
    VK_CODES,
    WindowsActionExecutor,
    _launch_process,
)


def make_executor(events):
    return WindowsActionExecutor(
        key_sender=lambda key, pressed: events.append(("key", key, pressed)),
        process_launcher=lambda command: events.append(("process", command)),
        url_opener=lambda url: events.append(("url", url)),
    )


def test_executes_media_and_hotkey_with_balanced_key_events() -> None:
    events = []
    executor = make_executor(events)

    executor.execute(MediaAction("volume_up"))
    executor.execute(HotkeyAction(("win", "d")))

    assert events == [
        ("key", MEDIA_VK_CODES["volume_up"], True),
        ("key", MEDIA_VK_CODES["volume_up"], False),
        ("key", VK_CODES["win"], True),
        ("key", VK_CODES["d"], True),
        ("key", VK_CODES["d"], False),
        ("key", VK_CODES["win"], False),
    ]


def test_releases_pressed_modifiers_when_hotkey_fails() -> None:
    events = []

    def sender(key, pressed):
        events.append((key, pressed))
        if key == VK_CODES["d"] and pressed:
            raise OSError("injection failed")

    executor = WindowsActionExecutor(sender, lambda command: None, lambda url: None)

    with pytest.raises(OSError):
        executor.execute(HotkeyAction(("win", "d")))

    assert events[-1] == (VK_CODES["win"], False)


def test_launches_without_shell_and_opens_url_through_injected_adapters() -> None:
    events = []
    executor = make_executor(events)

    executor.execute(LaunchAction("program.exe", ("--safe", "value")))
    executor.execute(OpenUrlAction("https://example.com"))

    assert events == [
        ("process", ["program.exe", "--safe", "value"]),
        ("url", "https://example.com"),
    ]


def test_process_adapter_never_uses_shell(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "streamdeck_monitor.infrastructure.action_executors.subprocess.Popen",
        lambda command, shell: calls.append((command, shell)),
    )

    _launch_process(["program.exe", "argument"])

    assert calls == [(["program.exe", "argument"], False)]
