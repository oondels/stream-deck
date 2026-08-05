from __future__ import annotations

from dataclasses import asdict
import queue
import threading

from streamdeck_monitor.application.ports import ActionExecutor, LogSink, RuntimeClock
from streamdeck_monitor.domain.actions import Binding


class QueuedActionDispatcher:
    def __init__(
        self,
        executor: ActionExecutor,
        sink: LogSink,
        clock: RuntimeClock,
        queue_size: int = 64,
    ) -> None:
        self._executor = executor
        self._sink = sink
        self._clock = clock
        self._queue: queue.Queue[Binding | None] = queue.Queue(maxsize=queue_size)
        self._closed = False
        self._thread = threading.Thread(
            target=self._run, name="streamdeck-actions", daemon=True
        )
        self._thread.start()

    def submit(self, binding: Binding) -> None:
        if self._closed:
            self._log_dropped(binding, "dispatcher_closed")
            return
        try:
            self._queue.put_nowait(binding)
        except queue.Full:
            self._log_dropped(binding, "queue_full")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        while True:
            try:
                binding = self._queue.get_nowait()
            except queue.Empty:
                break
            if binding is not None:
                self._log_dropped(binding, "shutdown")
            self._queue.task_done()
        try:
            self._queue.put_nowait(None)
        except queue.Full:  # pragma: no cover - queue was drained above
            pass
        self._thread.join(timeout=1.0)

    def _run(self) -> None:
        while True:
            binding = self._queue.get()
            try:
                if binding is None:
                    return
                self._execute(binding)
            finally:
                self._queue.task_done()

    def _execute(self, binding: Binding) -> None:
        started = self._clock.monotonic()
        details = self._details(binding)
        try:
            self._executor.execute(binding.action)
        except Exception as error:
            details["reason"] = str(error)
            self._sink.emit("ERROR", "action_failed", self._clock.now(), details)
            return
        details["duration_ms"] = round((self._clock.monotonic() - started) * 1000, 3)
        if self._executor.success_event == "action_dry_run":
            details["action"] = asdict(binding.action)
        self._sink.emit(
            "INFO", self._executor.success_event, self._clock.now(), details
        )

    def _log_dropped(self, binding: Binding, reason: str) -> None:
        details = self._details(binding)
        details["reason"] = reason
        self._sink.emit("WARNING", "action_dropped", self._clock.now(), details)

    @staticmethod
    def _details(binding: Binding) -> dict[str, object]:
        return {
            "binding_id": binding.id,
            "control": binding.control,
            "input_event": binding.event,
            "action_type": binding.action.type,
        }
