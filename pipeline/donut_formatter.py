"""
pipeline/donut_formatter.py
Converte o ground truth do pipeline para o formato esperado pelo Donut
(CLova AI — Document Understanding Transformer).

Formato de saída:
{
    "gt_parse": {
        "numero_fatura": "FAT-2024-00312",
        "data_emissao": "15/03/2024",
        ...
    }
}
"""

import json
import logging
from pathlib import Path

from .utils import ExportError

logger = logging.getLogger(__name__)

# Campos extraíveis pelo modelo — exclui metadados internos do pipeline
EXTRACTION_FIELDS = [
    "numero_fatura",
    "data_emissao",
    "data_vencimento",
    "emitente",
    "cliente",
    "itens",
    "subtotal",
    "impostos",
    "valor_total",
]


class DonutFormatter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def format(self, ground_truth: dict) -> dict:
        """Converte ground truth completo para formato Donut."""
        gt_parse = {
            field: ground_truth[field]
            for field in EXTRACTION_FIELDS
            if field in ground_truth
        }
        return {"gt_parse": gt_parse}

    def convert_file(self, json_path: Path, filename: str) -> Path:
        """
        Lê um JSON de ground truth e salva em formato Donut.

        Args:
            json_path: Caminho do JSON original do pipeline.
            filename: Nome do arquivo de saída (sem extensão).

        Returns:
            Path do JSON no formato Donut.

        Raises:
            ExportError: Se a leitura ou escrita falhar.
        """
        output_path = self.output_dir / f"{filename}.json"
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            donut_data = self.format(data)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(donut_data, f, ensure_ascii=False, indent=2)
            logger.debug("Donut JSON salvo: %s", output_path)
            return output_path
        except OSError as exc:
            raise ExportError(f"Falha ao gerar Donut JSON '{filename}': {exc}") from exc
