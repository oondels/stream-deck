"""Converte o SVG da aplicacao em um ICO aceito pelo PyInstaller no Windows."""

from pathlib import Path
import sys

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def main(source: Path, destination: Path) -> None:
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise ValueError(f"SVG invalido: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    png_path = destination.with_suffix(".png")
    if not image.save(str(png_path), "PNG"):
        raise RuntimeError(f"Nao foi possivel gerar o PNG temporario: {png_path}")

    try:
        with Image.open(png_path) as icon:
            icon.save(
                destination,
                format="ICO",
                sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )
    finally:
        png_path.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: generate_windows_icon.py ORIGEM.svg DESTINO.ico")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
