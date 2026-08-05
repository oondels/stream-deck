from __future__ import annotations

import argparse
import sys

from streamdeck_monitor.application.monitor import DeckMonitor
from streamdeck_monitor.application.settings import AppSettings, SerialSettings
from streamdeck_monitor.infrastructure.configuration import ConfigurationError, load_settings
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
    return parser


def create_monitor(settings: AppSettings) -> DeckMonitor:
    clock = SystemClock()
    sink = CombinedLoggingSink(settings.logging)
    return DeckMonitor(
        settings=settings.serial,
        provider=PySerialProvider(),
        codec=JsonProtocolCodec(),
        clock=clock,
        sink=sink,
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
        )

    monitor = create_monitor(settings)
    try:
        monitor.run_forever()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
