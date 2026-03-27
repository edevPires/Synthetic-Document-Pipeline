"""
pipeline/image_converter.py
Converte PDFs em imagens PNG para consumo pelo Donut.
Requer Poppler instalado no sistema.
  Windows: https://github.com/oschwartz10612/poppler-windows/releases
  Linux:   apt-get install poppler-utils
"""

import logging
from pathlib import Path

from pdf2image import convert_from_path

from .utils import ExportError

logger = logging.getLogger(__name__)


class ImageConverter:
    def __init__(self, output_dir: Path, dpi: int = 150, poppler_path: str = None) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        self.poppler_path = poppler_path

    def convert(self, pdf_path: Path) -> Path:
        """
        Converte a primeira página do PDF em PNG.

        Args:
            pdf_path: Caminho do arquivo PDF.

        Returns:
            Path do arquivo PNG gerado.

        Raises:
            ExportError: Se a conversão falhar.
        """
        pdf_path = Path(pdf_path)
        output_path = self.output_dir / f"{pdf_path.stem}.png"

        kwargs = {"dpi": self.dpi, "first_page": 1, "last_page": 1}
        if self.poppler_path:
            kwargs["poppler_path"] = self.poppler_path

        try:
            pages = convert_from_path(str(pdf_path), **kwargs)
            pages[0].save(str(output_path), "PNG")
            logger.debug("PNG salvo: %s", output_path)
            return output_path
        except Exception as exc:
            raise ExportError(
                f"Falha ao converter '{pdf_path.name}' para PNG: {exc}\n"
                "Verifique se o Poppler está instalado e no PATH."
            ) from exc
