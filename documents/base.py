"""
documents/base.py
Classes abstratas que definem o contrato de cada tipo de documento.
Todo novo tipo de documento deve herdar e implementar estas interfaces.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseDataGenerator(ABC):
    """Gera os dados sintéticos de um tipo de documento."""

    @abstractmethod
    def generate(self, **kwargs) -> dict:
        """
        Retorna um dict com todos os dados do documento + metadados_visuais.
        O dict deve ser serializável em JSON (use str para Decimal).
        """


class BaseExporter(ABC):
    """Orquestra a geração completa de um documento: arquivo + labels."""

    @abstractmethod
    def generate_one(self, index: int, **kwargs) -> tuple:
        """
        Gera um documento completo.

        Returns:
            Tupla com os paths dos arquivos gerados.
            Mínimo esperado: (arquivo_principal, json_ground_truth)
        """
