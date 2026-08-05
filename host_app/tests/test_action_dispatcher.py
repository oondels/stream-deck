from datetime import datetime, timezone
import threading

from streamdeck_monitor.domain.actions import Binding, MediaAction
from streamdeck_monitor.infrastructure.action_dispatcher import QueuedActionDispatcher
from streamdeck_monitor.infrastructure.action_executors import DryRunActionExecutor


class Clock:
    def __init__(self):
        self.elapsed = 0.0

    def now(self):
        return datetime(2026, 8, 5, tzinfo=timezone.utc)

    def monotonic(self):
        self.elapsed += 0.001
        return self.elapsed


class Sink:
    def __init__(self):
        self.entries = []
        self.called = threading.Event()

    def emit(self, level, event, timestamp, details):
        self.entries.append((level, event, dict(details)))
        self.called.set()


class Executor:
    success_event = "action_succeeded"

    def __init__(self, fail=False):
        self.actions = []
        self.fail = fail
        self.called = threading.Event()

    def execute(self, action):
        self.actions.append(action)
        self.called.set()
        if self.fail:
            raise RuntimeError("boom")


def binding(identifier="test"):
    return Binding(identifier, "key_1", "press", MediaAction("play_pause"))


def test_executes_queued_action_and_logs_success() -> None:
    sink = Sink()
    executor = Executor()
    dispatcher = QueuedActionDispatcher(executor, sink, Clock(), queue_size=2)

    dispatcher.submit(binding())
    assert executor.called.wait(1)
    dispatcher.close()

    assert executor.actions == [MediaAction("play_pause")]
    assert any(entry[1] == "action_succeeded" for entry in sink.entries)


def test_action_failure_is_logged_without_escaping_worker() -> None:
    sink = Sink()
    executor = Executor(fail=True)
    dispatcher = QueuedActionDispatcher(executor, sink, Clock())

    dispatcher.submit(binding())
    assert executor.called.wait(1)
    dispatcher.close()

    assert any(entry[1] == "action_failed" for entry in sink.entries)


def test_dry_run_logs_resolved_action() -> None:
    sink = Sink()
    dispatcher = QueuedActionDispatcher(DryRunActionExecutor(), sink, Clock())

    dispatcher.submit(binding())
    assert sink.called.wait(1)
    dispatcher.close()

    entry = next(entry for entry in sink.entries if entry[1] == "action_dry_run")
    assert entry[2]["action"] == {"command": "play_pause", "type": "media"}


def test_full_queue_drops_newest_action() -> None:
    class BlockingExecutor(Executor):
        def __init__(self):
            super().__init__()
            self.release = threading.Event()

        def execute(self, action):
            super().execute(action)
            self.release.wait(1)

    sink = Sink()
    executor = BlockingExecutor()
    dispatcher = QueuedActionDispatcher(executor, sink, Clock(), queue_size=1)

    dispatcher.submit(binding("running"))
    assert executor.called.wait(1)
    dispatcher.submit(binding("queued"))
    dispatcher.submit(binding("dropped"))
    executor.release.set()
    dispatcher.close()

    dropped = [entry for entry in sink.entries if entry[1] == "action_dropped"]
    assert any(entry[2]["reason"] == "queue_full" for entry in dropped)
