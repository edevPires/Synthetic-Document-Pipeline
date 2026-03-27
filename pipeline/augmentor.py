"""
pipeline/augmentor.py
Augmentação de imagens para simular documentos reais (escaneados, fotografados).
Usa apenas Pillow + numpy — sem dependências pesadas.
"""

import logging
import random
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class Augmentor:
    def __init__(self, augment_prob: float = 0.7) -> None:
        """
        Args:
            augment_prob: Probabilidade de aplicar augmentação (0.0–1.0).
                          Documentos não augmentados são mantidos limpos para
                          representar PDFs digitais no dataset.
        """
        self.augment_prob = augment_prob
        self._pipeline = [
            self._rotate,
            self._adjust_brightness,
            self._adjust_contrast,
            self._add_blur,
            self._add_noise,
            self._jpeg_artifacts,
        ]

    def augment(self, image_path: Path) -> Path:
        """
        Aplica 1–3 augmentações aleatórias na imagem.
        Sobrescreve o arquivo original com a versão augmentada.

        Args:
            image_path: Caminho da imagem PNG.

        Returns:
            Path da imagem (mesmo caminho, arquivo modificado).
        """
        if random.random() > self.augment_prob:
            logger.debug("Augmentação ignorada (prob): %s", image_path.name)
            return image_path

        image = Image.open(image_path).convert("RGB")
        selected = random.sample(self._pipeline, k=random.randint(1, 3))

        for aug in selected:
            image = aug(image)

        image.save(str(image_path), "PNG")
        logger.debug("Augmentação aplicada: %s", image_path.name)
        return image_path

    # ── Augmentações individuais ─────────────────────────────────────────

    @staticmethod
    def _rotate(image: Image.Image) -> Image.Image:
        """Rotação leve (-3° a +3°) — simula documento escaneado torto."""
        angle = random.uniform(-3.0, 3.0)
        return image.rotate(angle, expand=False, fillcolor=(255, 255, 255))

    @staticmethod
    def _adjust_brightness(image: Image.Image) -> Image.Image:
        """Varia brilho 75–125% — simula qualidade de scanner."""
        factor = random.uniform(0.75, 1.25)
        return ImageEnhance.Brightness(image).enhance(factor)

    @staticmethod
    def _adjust_contrast(image: Image.Image) -> Image.Image:
        """Varia contraste 80–120% — simula impressão/cópia."""
        factor = random.uniform(0.80, 1.20)
        return ImageEnhance.Contrast(image).enhance(factor)

    @staticmethod
    def _add_blur(image: Image.Image) -> Image.Image:
        """Blur gaussiano leve — simula foco imperfeito ou movimento."""
        radius = random.uniform(0.3, 1.5)
        return image.filter(ImageFilter.GaussianBlur(radius=radius))

    @staticmethod
    def _add_noise(image: Image.Image) -> Image.Image:
        """Ruído gaussiano — simula granularidade de scanner."""
        arr = np.array(image, dtype=np.int16)
        sigma = random.randint(3, 12)
        noise = np.random.normal(0, sigma, arr.shape).astype(np.int16)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    @staticmethod
    def _jpeg_artifacts(image: Image.Image) -> Image.Image:
        """Artefatos de compressão JPEG — simula foto de documento."""
        quality = random.randint(55, 82)
        buf = BytesIO()
        image.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        return Image.open(buf).copy()
