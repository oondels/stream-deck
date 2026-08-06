from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stream Deck Mini")
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="inicia o aplicativo minimizado",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        from streamdeck_monitor.gui.application import run
    except ImportError as error:
        if error.name and error.name.startswith("PySide6"):
            print(
                "GUI unavailable: install the project with the 'gui' extra",
                file=sys.stderr,
            )
            return 2
        raise
    return run(minimized=args.minimized)


if __name__ == "__main__":
    raise SystemExit(main())
