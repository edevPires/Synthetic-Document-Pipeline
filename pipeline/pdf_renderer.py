"""
pipeline/pdf_renderer.py
Renderização de HTML → PDF via WeasyPrint.
"""

import logging
from pathlib import Path

from weasyprint import HTML

from .utils import PDFRenderError

logger = logging.getLogger(__name__)


class PDFRenderer:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, html_string: str, filename: str) -> Path:
        """
        Converte html_string em PDF e salva em output_dir/filename.pdf.

        Args:
            html_string: HTML completo como string.
            filename: Nome do arquivo sem extensão.

        Returns:
            Path do arquivo PDF gerado.

        Raises:
            PDFRenderError: Se a renderização falhar.
        """
        output_path = self.output_dir / f"{filename}.pdf"
        try:
            HTML(string=html_string).write_pdf(str(output_path))
            logger.debug("PDF salvo: %s", output_path)
            return output_path
        except Exception as exc:
            raise PDFRenderError(
                f"Falha ao renderizar '{filename}.pdf': {exc}"
            ) from exc
