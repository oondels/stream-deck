from __future__ import annotations

import argparse
import os
import sys

from streamdeck_monitor.application.monitor import DeckMonitor
from streamdeck_monitor.application.settings import AppSettings, SerialSettings
from streamdeck_monitor.infrastructure.configuration import (
    ConfigurationError,
    load_settings,
)
from streamdeck_monitor.infrastructure.action_dispatcher import QueuedActionDispatcher
from streamdeck_monitor.infrastructure.action_executors import (
    DryRunActionExecutor,
    WindowsActionExecutor,
)
from streamdeck_monitor.infrastructure.logging_adapter import CombinedLoggingSink
from streamdeck_monitor.infrastructure.protocol import JsonProtocolCodec
from streamdeck_monitor.infrastructure.runtime import SystemClock
from streamdeck_monitor.infrastructure.serial_adapter import PySerialProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor serial do Stream Deck Mini")
    parser.add_argument(
        "--config",
        default="host_app/config.example.json",
        help="arquivo JSON de configuração",
    )
    parser.add_argument("--port", help="porta serial fixa, por exemplo COM4")
    parser.add_argument(
        "--dry-run-actions",
        action="store_true",
        help="registra bindings sem executar ações externas",
    )
    return parser


def create_monitor(settings: AppSettings, dry_run_actions: bool = False) -> DeckMonitor:
    clock = SystemClock()
    sink = CombinedLoggingSink(settings.logging)
    dispatcher = None
    if settings.actions.bindings:
        executor = (
            DryRunActionExecutor() if dry_run_actions else WindowsActionExecutor()
        )
        dispatcher = QueuedActionDispatcher(
            executor=executor,
            sink=sink,
            clock=clock,
            queue_size=settings.actions.queue_size,
        )
    return DeckMonitor(
        settings=settings.serial,
        provider=PySerialProvider(),
        codec=JsonProtocolCodec(),
        clock=clock,
        sink=sink,
        bindings=settings.actions.bindings,
        dispatcher=dispatcher,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(args.config)
    except ConfigurationError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return 2

    if args.port:
        settings = AppSettings(
            serial=SerialSettings(
                port=args.port,
                baud_rate=settings.serial.baud_rate,
                scan_interval_seconds=settings.serial.scan_interval_seconds,
                handshake_timeout_seconds=settings.serial.handshake_timeout_seconds,
            ),
            logging=settings.logging,
            actions=settings.actions,
        )

    if settings.actions.bindings and os.name != "nt" and not args.dry_run_actions:
        print(
            "actions error: Windows actions require Windows; use --dry-run-actions "
            "on this platform",
            file=sys.stderr,
        )
        return 2

    monitor = create_monitor(settings, dry_run_actions=args.dry_run_actions)
    try:
        monitor.run_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        monitor.close()


if __name__ == "__main__":
    raise SystemExit(main())
