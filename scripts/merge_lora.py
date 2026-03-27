"""
scripts/merge_lora.py
Mescla os adaptadores LoRA no modelo base, gerando um modelo completo pronto
para conversão GGUF.

Uso:
    python scripts/merge_lora.py
    python scripts/merge_lora.py --base models/qwen3.5-9b --lora models/qwen-invoice-lora --output models/qwen-invoice-merged
"""

import argparse
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Mescla adaptadores LoRA no modelo base",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--base",   type=str,  default="models/qwen3.5-9b")
    parser.add_argument("--lora",   type=str,  default="models/qwen-invoice-lora")
    parser.add_argument("--output", type=Path, default=Path("models/qwen-invoice-merged"))
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"Base  : {args.base}")
    print(f"LoRA  : {args.lora}")
    print(f"Saída : {args.output}\n")

    print("Carregando tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.lora, trust_remote_code=True)

    print("Carregando modelo base (float16)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base,
        torch_dtype=torch.float16,
        device_map="cpu",           # CPU para merge — evita OOM na GPU
        trust_remote_code=True,
    )

    print("Aplicando adaptadores LoRA...")
    model = PeftModel.from_pretrained(model, args.lora)

    print("Mesclando pesos...")
    model = model.merge_and_unload()

    print(f"Salvando modelo mesclado em: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.output), safe_serialization=True)
    tokenizer.save_pretrained(str(args.output))

    print("\nConcluído!")
    print(f"Próximo passo: python scripts/convert_gguf.py --model {args.output}")


if __name__ == "__main__":
    main()
