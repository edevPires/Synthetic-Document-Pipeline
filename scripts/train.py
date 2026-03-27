"""
scripts/train.py
Fine-tuning do Donut (naver-clova-ix/donut-base) em dataset de faturas sintéticas.

Configurado para RTX 3060 (6 GB VRAM):
  - Imagem reduzida para 1280x960 (padrão 2560x1920 estouraria VRAM)
  - fp16 (mixed precision)
  - batch_size=2 + gradient_accumulation=8 → batch efetivo=16
  - Salva o melhor modelo por validation loss

Uso:
    python scripts/train.py
    python scripts/train.py --dataset dataset/donut --output models/donut-invoice --epochs 30
"""

import argparse
import json
import logging
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import DonutProcessor, VisionEncoderDecoderModel, get_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Tokens especiais da tarefa de fatura ──────────────────────────────────────

TASK_START = "<s_invoice>"
TASK_END   = "</s_invoice>"

SPECIAL_TOKENS = [
    "<s_invoice>",    "</s_invoice>",
    "<s_emitente>",   "</s_emitente>",
    "<s_nome>",       "</s_nome>",
    "<s_cnpj>",       "</s_cnpj>",
    "<s_cpf_cnpj>",   "</s_cpf_cnpj>",
    "<s_endereco>",   "</s_endereco>",
    "<s_municipio>",  "</s_municipio>",
    "<s_uf>",         "</s_uf>",
    "<s_cep>",        "</s_cep>",
    "<s_telefone>",   "</s_telefone>",
    "<s_email>",      "</s_email>",
    "<s_ie>",         "</s_ie>",
    "<s_destinatario>", "</s_destinatario>",
    "<s_cpf>",        "</s_cpf>",
    "<s_itens>",      "</s_itens>",
    "<s_item>",       "</s_item>",
    "<s_descricao>",  "</s_descricao>",
    "<s_quantidade>", "</s_quantidade>",
    "<s_unidade>",    "</s_unidade>",
    "<s_valor_unitario>", "</s_valor_unitario>",
    "<s_valor_total>", "</s_valor_total>",
    "<s_ncm>",        "</s_ncm>",
    "<s_totais>",     "</s_totais>",
    "<s_subtotal>",   "</s_subtotal>",
    "<s_desconto>",   "</s_desconto>",
    "<s_acrescimo>",  "</s_acrescimo>",
    "<s_total>",      "</s_total>",
    "<s_dados_fiscais>", "</s_dados_fiscais>",
    "<s_numero>",     "</s_numero>",
    "<s_serie>",      "</s_serie>",
    "<s_chave_nfe>",  "</s_chave_nfe>",
    "<s_data_emissao>", "</s_data_emissao>",
    "<s_natureza_operacao>", "</s_natureza_operacao>",
    "<s_forma_pagamento>", "</s_forma_pagamento>",
    "<s_vencimento>", "</s_vencimento>",
    "<s_observacoes>", "</s_observacoes>",
]

# ── Serialização do gt_parse para tokens XML-like ─────────────────────────────

def serialize(obj, key: str = "invoice") -> str:
    """Converte dict/list/valor para sequência de tokens XML-like do Donut."""
    out = f"<s_{key}>"
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += serialize(v, k)
    elif isinstance(obj, list):
        for item in obj:
            out += serialize(item, "item")
    elif obj is not None:
        out += str(obj)
    out += f"</s_{key}>"
    return out


# ── Dataset ───────────────────────────────────────────────────────────────────

class InvoiceDataset(Dataset):
    def __init__(self, data_dir: Path, processor: DonutProcessor, max_length: int):
        self.data_dir   = data_dir
        self.processor  = processor
        self.max_length = max_length
        self.samples    = []

        metadata_path = data_dir / "metadata.jsonl"
        with open(metadata_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.samples.append(json.loads(line))

        logger.info("  %s: %d amostras carregadas", data_dir.name, len(self.samples))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample    = self.samples[idx]
        img_path  = self.data_dir / sample["file_name"]
        image     = Image.open(img_path).convert("RGB")
        gt        = json.loads(sample["ground_truth"])
        gt_parse  = gt.get("gt_parse", gt)

        target_seq = serialize(gt_parse)

        pixel_values = self.processor(
            image, return_tensors="pt"
        ).pixel_values.squeeze(0)

        token_ids = self.processor.tokenizer(
            target_seq,
            add_special_tokens=False,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        ).input_ids.squeeze(0)

        # -100 é ignorado na loss (posições de padding)
        labels = token_ids.clone()
        labels[labels == self.processor.tokenizer.pad_token_id] = -100

        decoder_input_ids = torch.full(
            (1,),
            self.processor.tokenizer.convert_tokens_to_ids(TASK_START),
            dtype=torch.long,
        )

        return {
            "pixel_values":      pixel_values,
            "labels":            labels,
            "decoder_input_ids": decoder_input_ids,
        }


def collate_fn(batch):
    return {
        "pixel_values":      torch.stack([b["pixel_values"]      for b in batch]),
        "labels":            torch.stack([b["labels"]            for b in batch]),
        "decoder_input_ids": torch.stack([b["decoder_input_ids"] for b in batch]),
    }


# ── Treino ────────────────────────────────────────────────────────────────────

def run_epoch(model, loader, optimizer, scaler, scheduler, device, grad_accum, train=True):
    model.train(train)
    total_loss = 0.0
    steps = 0

    ctx = torch.cuda.amp.autocast(dtype=torch.float16) if scaler else torch.no_grad()

    with (ctx if not train else torch.cuda.amp.autocast(dtype=torch.float16)):
        pass  # apenas para import check

    for i, batch in enumerate(tqdm(loader, desc="train" if train else "val", leave=False)):
        pixel_values      = batch["pixel_values"].to(device)
        labels            = batch["labels"].to(device)
        decoder_input_ids = batch["decoder_input_ids"].to(device)

        if train:
            with torch.cuda.amp.autocast(dtype=torch.float16):
                outputs = model(
                    pixel_values=pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    labels=labels,
                )
                loss = outputs.loss / grad_accum

            scaler.scale(loss).backward()

            if (i + 1) % grad_accum == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
        else:
            with torch.no_grad(), torch.cuda.amp.autocast(dtype=torch.float16):
                outputs = model(
                    pixel_values=pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    labels=labels,
                )
                loss = outputs.loss

        total_loss += outputs.loss.item()
        steps += 1

    return total_loss / steps if steps > 0 else float("inf")


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tuning Donut para faturas (RTX 3060)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset",     type=Path,  default=Path("dataset/donut"))
    parser.add_argument("--output",      type=Path,  default=Path("models/donut-invoice"))
    parser.add_argument("--base-model",  type=str,   default="naver-clova-ix/donut-base")
    parser.add_argument("--epochs",      type=int,   default=30)
    parser.add_argument("--batch-size",  type=int,   default=2,
                        help="Batch por step (2 cabe em 6 GB com img 1280x960)")
    parser.add_argument("--grad-accum",  type=int,   default=8,
                        help="Gradient accumulation → batch efetivo = batch-size × grad-accum")
    parser.add_argument("--lr",          type=float, default=3e-5)
    parser.add_argument("--max-length",  type=int,   default=512,
                        help="Comprimento máximo da sequência de labels")
    parser.add_argument("--img-height",  type=int,   default=960)
    parser.add_argument("--img-width",   type=int,   default=1280)
    parser.add_argument("--warmup-steps",type=int,   default=100)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Dispositivo: %s", device)
    if device.type == "cuda":
        logger.info("GPU: %s (%.1f GB)", torch.cuda.get_device_name(), torch.cuda.get_device_properties(0).total_memory / 1e9)

    # ── Processor e modelo ────────────────────────────────────────────────────
    logger.info("Carregando processor e modelo base: %s", args.base_model)
    processor = DonutProcessor.from_pretrained(args.base_model)
    model     = VisionEncoderDecoderModel.from_pretrained(args.base_model)

    # Ajusta resolução de entrada para 6 GB de VRAM
    processor.image_processor.size = {"height": args.img_height, "width": args.img_width}
    processor.image_processor.do_align_long_axis = False
    model.config.encoder.image_size = [args.img_height, args.img_width]

    # Adiciona tokens especiais da tarefa
    processor.tokenizer.add_special_tokens({"additional_special_tokens": SPECIAL_TOKENS})
    model.decoder.resize_token_embeddings(len(processor.tokenizer))

    task_start_id = processor.tokenizer.convert_tokens_to_ids(TASK_START)
    pad_token_id  = processor.tokenizer.pad_token_id

    model.config.decoder_start_token_id = task_start_id
    model.config.pad_token_id           = pad_token_id
    model.config.eos_token_id           = processor.tokenizer.eos_token_id

    model.to(device)

    # ── Datasets e loaders ───────────────────────────────────────────────────
    logger.info("Carregando datasets de: %s", args.dataset)
    train_ds = InvoiceDataset(args.dataset / "train",      processor, args.max_length)
    val_ds   = InvoiceDataset(args.dataset / "validation", processor, args.max_length)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,  collate_fn=collate_fn, num_workers=2, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn, num_workers=2, pin_memory=True)

    # ── Otimizador e scheduler ───────────────────────────────────────────────
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    total_steps = (len(train_loader) // args.grad_accum) * args.epochs
    scheduler   = get_scheduler(
        "cosine",
        optimizer=optimizer,
        num_warmup_steps=args.warmup_steps,
        num_training_steps=total_steps,
    )

    scaler = torch.cuda.amp.GradScaler()

    # ── Loop de treino ───────────────────────────────────────────────────────
    args.output.mkdir(parents=True, exist_ok=True)
    best_val_loss = float("inf")

    logger.info("Iniciando treino: %d epochs, batch efetivo=%d", args.epochs, args.batch_size * args.grad_accum)
    logger.info("Resolução de entrada: %dx%d", args.img_width, args.img_height)

    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(model, train_loader, optimizer, scaler, scheduler, device, args.grad_accum, train=True)
        val_loss   = run_epoch(model, val_loader,   optimizer, scaler, scheduler, device, args.grad_accum, train=False)

        logger.info("Epoch %2d/%d | train_loss=%.4f | val_loss=%.4f", epoch, args.epochs, train_loss, val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            model.save_pretrained(args.output)
            processor.save_pretrained(args.output)
            logger.info("  ✓ Melhor modelo salvo (val_loss=%.4f)", best_val_loss)

    logger.info("Treino concluído. Modelo salvo em: %s", args.output.resolve())
    logger.info("Para inferência: python scripts/inference.py --model %s --image <caminho>", args.output)


if __name__ == "__main__":
    main()
