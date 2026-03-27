"""
scripts/prepare_donut_dataset.py
Converte dataset/ (saída do split_dataset.py) para o formato exigido pelo Donut:

  dataset/donut/
    train/
      metadata.jsonl
      invoice_001.png
      invoice_002.png
      ...
    validation/
      metadata.jsonl
      ...
    test/
      metadata.jsonl
      ...

Formato de cada linha do metadata.jsonl:
  {"file_name": "invoice_001.png", "ground_truth": "{\"gt_parse\": {...}}"}

Uso:
    python scripts/prepare_donut_dataset.py
    python scripts/prepare_donut_dataset.py --input dataset --output dataset/donut
"""

import argparse
import json
import shutil
from pathlib import Path


SPLIT_MAP = {
    "train":      "train",
    "val":        "validation",
    "test":       "test",
}


def prepare_split(src_dir: Path, dst_dir: Path, split_label: str) -> int:
    images_dir      = src_dir / "images"
    donut_labels_dir = src_dir / "donut_labels"

    if not images_dir.exists():
        print(f"  [AVISO] {images_dir} não encontrado, pulando.")
        return 0

    dst_dir.mkdir(parents=True, exist_ok=True)

    metadata_lines = []
    for img_path in sorted(images_dir.glob("*.png")):
        label_path = donut_labels_dir / f"{img_path.stem}.json"
        if not label_path.exists():
            print(f"  [AVISO] donut_label não encontrado para {img_path.name}, ignorando.")
            continue

        # Copia imagem para a pasta do split
        shutil.copy2(img_path, dst_dir / img_path.name)

        # Lê o donut_label (já no formato {"gt_parse": {...}})
        gt = json.loads(label_path.read_text(encoding="utf-8"))

        # ground_truth deve ser uma string JSON (não objeto)
        metadata_lines.append({
            "file_name":    img_path.name,
            "ground_truth": json.dumps(gt, ensure_ascii=False),
        })

    jsonl_path = dst_dir / "metadata.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in metadata_lines:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"  {split_label:10s} → {len(metadata_lines):>5} amostras  ({dst_dir})")
    return len(metadata_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara dataset no formato Donut (metadata.jsonl)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input",  type=Path, default=Path("dataset"),
                        help="Diretório base gerado pelo split_dataset.py")
    parser.add_argument("--output", type=Path, default=Path("dataset/donut"),
                        help="Diretório de saída no formato Donut")
    args = parser.parse_args()

    print(f"\nConvertendo {args.input} → {args.output}\n")

    total = 0
    for src_name, dst_name in SPLIT_MAP.items():
        src = args.input / src_name
        if src.exists():
            total += prepare_split(src, args.output / dst_name, dst_name)

    print(f"\nTotal: {total} amostras prontas para treino.")
    print(f"Dataset Donut salvo em: {args.output.resolve()}\n")
    print("Próximo passo:")
    print("  python scripts/train.py --dataset dataset/donut --output models/donut-invoice")


if __name__ == "__main__":
    main()
