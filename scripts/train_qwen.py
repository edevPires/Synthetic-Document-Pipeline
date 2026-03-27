"""
scripts/train_qwen.py
Fine-tuning do Qwen3.5-9B com QLoRA (4-bit) para geração de faturas brasileiras.

Configurado para RTX 3060 12 GB:
  - Quantização 4-bit (bitsandbytes) → ~5 GB para pesos
  - LoRA rank=64 nos módulos de atenção e FFN
  - batch_size=1 + grad_accum=16 → batch efetivo=16
  - fp16

Uso:
    pip install trl peft bitsandbytes datasets
    python scripts/train_qwen.py
    python scripts/train_qwen.py --model models/qwen3.5-9b --epochs 3 --output models/qwen-invoice-lora
"""

import argparse
from pathlib import Path

from datasets import load_dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer, SFTConfig
import torch


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fine-tuning Qwen3.5-9B com QLoRA para geração de faturas",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model",      type=str,  default="models/qwen3.5-9b",
                        help="Caminho local ou ID HuggingFace do modelo base")
    parser.add_argument("--dataset",    type=Path, default=Path("dataset/qwen"),
                        help="Diretório com train.jsonl e val.jsonl")
    parser.add_argument("--output",     type=Path, default=Path("models/qwen-invoice-lora"),
                        help="Onde salvar os adaptadores LoRA")
    parser.add_argument("--epochs",     type=int,  default=3)
    parser.add_argument("--batch-size", type=int,  default=1)
    parser.add_argument("--grad-accum", type=int,  default=16,
                        help="Gradient accumulation → batch efetivo = batch-size × grad-accum")
    parser.add_argument("--lr",         type=float, default=2e-4)
    parser.add_argument("--lora-rank",  type=int,  default=64)
    parser.add_argument("--max-length", type=int,  default=2048)
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"Modelo base : {args.model}")
    print(f"Dataset     : {args.dataset}")
    print(f"Saída LoRA  : {args.output}")
    print(f"Epochs      : {args.epochs}")
    print(f"Batch efetivo: {args.batch_size * args.grad_accum}\n")

    # ── Quantização 4-bit ─────────────────────────────────────────────────────
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # ── Tokenizer ─────────────────────────────────────────────────────────────
    print("Carregando tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # ── Modelo ────────────────────────────────────────────────────────────────
    print("Carregando modelo em 4-bit...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False

    # ── LoRA ──────────────────────────────────────────────────────────────────
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_rank,
        lora_alpha=args.lora_rank * 2,
        lora_dropout=0.05,
        bias="none",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ── Dataset ───────────────────────────────────────────────────────────────
    print("Carregando dataset...")
    train_path = str(args.dataset / "train.jsonl")
    val_path   = str(args.dataset / "val.jsonl")

    dataset = load_dataset("json", data_files={
        "train": train_path,
        "validation": val_path,
    })

    # ── Treinamento ───────────────────────────────────────────────────────────
    training_args = SFTConfig(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        bf16=True,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="none",
        max_length=args.max_length,
        dataset_text_field=None,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        processing_class=tokenizer,
    )

    print("\nIniciando fine-tuning...\n")
    trainer.train()

    print(f"\nSalvando adaptadores LoRA em: {args.output}")
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))

    print("\nConcluído!")
    print(f"Próximo passo: python scripts/merge_lora.py --base {args.model} --lora {args.output}")


if __name__ == "__main__":
    main()
