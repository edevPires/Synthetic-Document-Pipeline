"""
documents/invoice/exporter.py
Orquestrador do pipeline completo:
  DataGenerator → TemplateEngine → PDFRenderer → ImageConverter → Augmentor
  → ground truth JSON → Donut JSON
"""

import json
import logging
from decimal import Decimal
from pathlib import Path

from pipeline.augmentor import Augmentor
from .data_generator import DataGenerator
from pipeline.donut_formatter import DonutFormatter
from pipeline.image_converter import ImageConverter
from pipeline.pdf_renderer import PDFRenderer
from .template_engine import TemplateEngine
from pipeline.utils import ExportError, PDFRenderError

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """Serializa Decimal como string para preservar precisão financeira."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Exporter:
    def __init__(
        self,
        pdf_dir: Path,
        labels_dir: Path,
        images_dir: Path,
        donut_dir: Path,
        dpi: int = 150,
        augment: bool = True,
        augment_prob: float = 0.7,
        poppler_path: str = None,
    ) -> None:
        self.labels_dir = Path(labels_dir)
        self.labels_dir.mkdir(parents=True, exist_ok=True)

        self.generator = DataGenerator()
        self.engine = TemplateEngine()
        self.renderer = PDFRenderer(pdf_dir)
        self.image_converter = ImageConverter(images_dir, dpi=dpi, poppler_path=poppler_path)
        self.augmentor = Augmentor(augment_prob=augment_prob) if augment else None
        self.donut_formatter = DonutFormatter(donut_dir)

    def generate_one(self, index: int, layout: str = None) -> tuple:
        """
        Gera um documento completo: PDF + PNG + JSON ground truth + JSON Donut.

        Returns:
            Tupla (pdf_path, png_path, json_path, donut_path).

        Raises:
            PDFRenderError: Se a renderização do PDF falhar.
            ExportError: Se qualquer etapa de I/O falhar.
        """
        data = self.generator.generate(layout=layout)
        filename = data["numero_fatura"].replace("/", "-")

        html = self.engine.render(data)
        pdf_path = self.renderer.render(html, filename)
        png_path = self.image_converter.convert(pdf_path)

        if self.augmentor:
            self.augmentor.augment(png_path)

        json_path = self._save_ground_truth(data, filename)
        donut_path = self.donut_formatter.convert_file(json_path, filename)

        return pdf_path, png_path, json_path, donut_path

    def _save_ground_truth(self, data: dict, filename: str) -> Path:
        """Serializa os campos de ground truth para JSON."""
        ground_truth = {
            "numero_fatura": data["numero_fatura"],
            "data_emissao": data["data_emissao"],
            "data_vencimento": data["data_vencimento"],
            "emitente": data["emitente"],
            "cliente": data["cliente"],
            "itens": [
                {
                    "descricao": item["descricao"],
                    "qtd": item["qtd"],
                    "preco_unit": item["preco_unit"],
                    "subtotal": item["subtotal"],
                }
                for item in data["itens"]
            ],
            "subtotal": data["subtotal"],
            "impostos": data["impostos"],
            "valor_total": data["valor_total"],
            "metadados_visuais": data["metadados_visuais"],
        }

        json_path = self.labels_dir / f"{filename}.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(ground_truth, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
            logger.debug("JSON salvo: %s", json_path)
            return json_path
        except OSError as exc:
            raise ExportError(f"Falha ao salvar '{json_path}': {exc}") from exc
