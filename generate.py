"""
generate.py
CLI para geração em lote de documentos sintéticos para Document AI / Donut.

Uso:
    python generate.py --type invoice --count 60
    python generate.py --type invoice --count 1000 --workers 4 --dpi 200
    python generate.py --type invoice --count 60 --no-augment
    python generate.py --type invoice --count 60 --poppler-path "C:/poppler/bin"
"""

import argparse
import logging
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pipeline.utils import ExportError, PDFRenderError, PipelineError

# ── Registro de tipos de documento disponíveis ──────────────────────────────
# Para adicionar um novo tipo: crie documents/<tipo>/ e registre aqui.

def _load_registry() -> dict:
    from documents.invoice.exporter import Exporter as InvoiceExporter
    from documents.invoice.data_generator import DataGenerator as InvoiceDataGenerator
    return {
        "invoice": {
            "exporter": InvoiceExporter,
            "layouts": InvoiceDataGenerator.LAYOUTS,
        },
    }


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def build_layout_queue(layouts: list, count: int) -> list:
    """Distribui layouts igualmente; resto é sorteado sem repetição preferencial."""
    base = count // len(layouts)
    remainder = count % len(layouts)
    queue = layouts * base + random.sample(layouts, remainder)
    random.shuffle(queue)
    return queue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gerador de Documentos Sintéticos para Document AI / Donut",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--type", "-t", default="invoice",
                        help="Tipo de documento a gerar (ex: invoice)")
    parser.add_argument("--count", "-n", type=int, default=12,
                        help="Número de documentos a gerar")
    parser.add_argument("--output-dir", type=Path, default=Path("output"),
                        help="Diretório base de saída")
    parser.add_argument("--workers", "-w", type=int, default=1,
                        help="Número de threads paralelas")
    parser.add_argument("--dpi", type=int, default=150,
                        help="Resolução das imagens PNG")
    parser.add_argument("--no-augment", action="store_true",
                        help="Desativa augmentação de imagens")
    parser.add_argument("--augment-prob", type=float, default=0.7,
                        help="Probabilidade de augmentação por imagem")
    parser.add_argument("--poppler-path", type=str, default=None,
                        help="Caminho para binários do Poppler (Windows)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Habilita logging detalhado (DEBUG)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    registry = _load_registry()
    if args.type not in registry:
        available = ", ".join(registry.keys())
        logger.error("Tipo '%s' não encontrado. Disponíveis: %s", args.type, available)
        sys.exit(1)

    entry = registry[args.type]
    ExporterClass = entry["exporter"]
    layouts = entry["layouts"]

    base = args.output_dir / args.type
    pdf_dir    = base / "pdfs"
    images_dir = base / "images"
    labels_dir = base / "labels"
    donut_dir  = base / "donut_labels"

    layout_queue = build_layout_queue(layouts, args.count)
    dist_str = "  ".join(f"{k}:{v}" for k, v in sorted(Counter(layout_queue).items()))

    logger.info("Tipo: %s | %d documento(s) | %d worker(s)", args.type, args.count, args.workers)
    logger.info("Layouts: %s", dist_str)
    logger.info("DPI: %d | Augmentação: %s", args.dpi, "não" if args.no_augment else f"sim ({int(args.augment_prob*100)}%)")

    def make_exporter():
        return ExporterClass(
            pdf_dir=pdf_dir,
            labels_dir=labels_dir,
            images_dir=images_dir,
            donut_dir=donut_dir,
            dpi=args.dpi,
            augment=not args.no_augment,
            augment_prob=args.augment_prob,
            poppler_path=args.poppler_path,
        )

    success = 0
    failures = 0

    if args.workers == 1:
        exporter = make_exporter()
        for i, layout in enumerate(layout_queue, start=1):
            try:
                pdf_path, *_ = exporter.generate_one(index=i, layout=layout)
                logger.info("[%d/%d] OK %-12s — %s", i, args.count, f"({layout})", pdf_path.name)
                success += 1
            except (PDFRenderError, ExportError, PipelineError) as exc:
                logger.error("[%d/%d] FALHA (%s) — %s", i, args.count, layout, exc)
                failures += 1
            except Exception as exc:
                logger.error("[%d/%d] ERRO INESPERADO (%s) — %s", i, args.count, layout, exc)
                failures += 1
    else:
        def _gerar(i: int, layout: str) -> tuple:
            exp = make_exporter()
            pdf_path, *_ = exp.generate_one(index=i, layout=layout)
            return pdf_path.name, layout

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(_gerar, i, layout): (i, layout)
                for i, layout in enumerate(layout_queue, start=1)
            }
            for future in as_completed(futures):
                i, layout = futures[future]
                try:
                    nome, lay = future.result()
                    logger.info("[%d/%d] OK %-12s — %s", i, args.count, f"({lay})", nome)
                    success += 1
                except (PDFRenderError, ExportError, PipelineError) as exc:
                    logger.error("[%d/%d] FALHA (%s) — %s", i, args.count, layout, exc)
                    failures += 1
                except Exception as exc:
                    logger.error("[%d/%d] ERRO INESPERADO (%s) — %s", i, args.count, layout, exc)
                    failures += 1

    logger.info("─" * 50)
    logger.info("Concluído: %d sucesso(s), %d falha(s).", success, failures)

    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
