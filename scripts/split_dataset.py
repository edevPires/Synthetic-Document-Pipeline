"""
scripts/split_dataset.py
Divide o dataset gerado em splits train/val/test estratificados por layout.

Estrutura de saída:
  dataset/
    train/  images/  labels/  donut_labels/
    val/    images/  labels/  donut_labels/
    test/   images/  labels/  donut_labels/

Uso:
    python scripts/split_dataset.py
    python scripts/split_dataset.py --input output --output dataset --train 0.7 --val 0.15
"""

import argparse
import json
import random
import shutil
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split de dataset estratificado por layout",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", type=Path, default=Path("output"),
                        help="Diretório base gerado pelo generate.py")
    parser.add_argument("--output", type=Path, default=Path("dataset"),
                        help="Diretório base de saída do dataset")
    parser.add_argument("--train", type=float, default=0.70,
                        help="Proporção do split de treino")
    parser.add_argument("--val", type=float, default=0.15,
                        help="Proporção do split de validação")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed para reprodutibilidade")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    test_ratio = round(1.0 - args.train - args.val, 6)
    if test_ratio <= 0:
        raise ValueError("--train + --val deve ser menor que 1.0")

    images_dir = args.input / "images"
    labels_dir = args.input / "labels"
    donut_dir  = args.input / "donut_labels"

    if not images_dir.exists():
        raise FileNotFoundError(f"Diretório de imagens não encontrado: {images_dir}")

    # Agrupa por layout para garantir distribuição uniforme em cada split
    by_layout: dict[str, list[str]] = defaultdict(list)
    for img_path in sorted(images_dir.glob("*.png")):
        label_path = labels_dir / f"{img_path.stem}.json"
        if not label_path.exists():
            print(f"  [AVISO] Label não encontrado para {img_path.name}, ignorando.")
            continue
        with open(label_path, encoding="utf-8") as f:
            data = json.load(f)
        layout = data.get("metadados_visuais", {}).get("layout", "desconhecido")
        by_layout[layout].append(img_path.stem)

    total = sum(len(v) for v in by_layout.values())
    if total == 0:
        raise ValueError("Nenhum documento encontrado no diretório de entrada.")

    train_ids, val_ids, test_ids = [], [], []

    for layout, ids in sorted(by_layout.items()):
        random.shuffle(ids)
        n = len(ids)
        n_train = int(n * args.train)
        n_val   = int(n * args.val)
        train_ids.extend(ids[:n_train])
        val_ids.extend(ids[n_train:n_train + n_val])
        test_ids.extend(ids[n_train + n_val:])

    splits = {"train": train_ids, "val": val_ids, "test": test_ids}
    subdirs = ["images", "labels", "donut_labels"]

    print(f"\nSplit estratificado por layout ({total} documentos):")
    print(f"  Treino:    {len(train_ids):>5} ({args.train*100:.0f}%)")
    print(f"  Validação: {len(val_ids):>5} ({args.val*100:.0f}%)")
    print(f"  Teste:     {len(test_ids):>5} ({test_ratio*100:.0f}%)")
    print()

    for split_name, ids in splits.items():
        for sub in subdirs:
            (args.output / split_name / sub).mkdir(parents=True, exist_ok=True)

        copied = 0
        for doc_id in ids:
            for sub, ext in [("images", ".png"), ("labels", ".json"), ("donut_labels", ".json")]:
                src = args.input / sub / f"{doc_id}{ext}"
                if src.exists():
                    shutil.copy2(src, args.output / split_name / sub / f"{doc_id}{ext}")
                    if ext == ".png":
                        copied += 1

        print(f"  {split_name:6s} → {copied} imagens copiadas")

    print(f"\nDataset salvo em: {args.output.resolve()}")
    print("\nEstrutura:")
    for split_name in splits:
        print(f"  {args.output}/{split_name}/")
        for sub in subdirs:
            n = len(list((args.output / split_name / sub).iterdir()))
            print(f"    {sub}/  ({n} arquivos)")


if __name__ == "__main__":
    main()
