"""
scripts/prepare_qwen_dataset.py
Converte dataset/train|val|test/labels/ para JSONL conversacional no formato
de fine-tuning do Qwen3.5 via TRL SFTTrainer.

Cada amostra vira:
  {"messages": [
    {"role": "system", "content": "..."},
    {"role": "user",   "content": "<prompt criativo gerado dos dados>"},
    {"role": "assistant", "content": "<json da fatura sem metadados_visuais>"}
  ]}

Uso:
    python scripts/prepare_qwen_dataset.py
    python scripts/prepare_qwen_dataset.py --input dataset --output dataset/qwen
"""

import argparse
import json
import random
from pathlib import Path

SYSTEM_PROMPT = (
    "Você é um assistente especializado em gerar faturas brasileiras em formato JSON estruturado. "
    "Dado um pedido do usuário, retorne APENAS o JSON completo da fatura, sem explicações, "
    "sem markdown, sem blocos de código. O JSON deve conter: numero_fatura, data_emissao, "
    "data_vencimento, emitente (nome, cnpj, endereco, telefone, email), cliente (nome, "
    "cpf_cnpj, endereco, telefone), itens (descricao, qtd, preco_unit, subtotal), "
    "subtotal, impostos e valor_total."
)

# Templates de prompts criativos — preenchidos com dados reais da fatura
PROMPT_TEMPLATES = [
    "Gera uma fatura de serviços para {cliente} no valor total de R$ {total}.",
    "Preciso de uma nota fiscal da empresa {emitente} para o cliente {cliente}.",
    "Emite uma fatura com {n_itens} itens de serviço para {cliente}, totalizando R$ {total}.",
    "Cria uma fatura brasileira da {emitente} com vencimento em {vencimento}.",
    "Gera uma fatura de {servicos} para {cliente}.",
    "Preciso de uma fatura no valor de R$ {total} emitida por {emitente}.",
    "Emite uma nota para {cliente} com serviços de {servicos}, valor total R$ {total}.",
    "Gera uma fatura da empresa {emitente} com {n_itens} serviços distintos.",
    "Cria uma fatura brasileira para {cliente}, emitida por {emitente}.",
    "Preciso de uma nota fiscal de serviços no valor de R$ {total} para {cliente}.",
    "Emite uma fatura com data de vencimento {vencimento} para o cliente {cliente}.",
    "Gera uma nota fiscal de serviços de {servicos}.",
    "Cria uma fatura para {cliente} com itens de {servicos}, total R$ {total}.",
    "Preciso de uma fatura da {emitente} para {cliente} com {n_itens} serviços.",
    "Emite uma fatura brasileira de serviços de {servicos} para {cliente}.",
    "Gera uma nota fiscal no valor de R$ {total} com data de emissão {emissao}.",
    "Cria uma fatura para a empresa {cliente} com serviços prestados por {emitente}.",
    "Preciso de uma fatura de serviços de TI no valor de R$ {total}.",
    "Emite uma nota fiscal brasileira para {cliente} totalizando R$ {total}.",
    "Gera uma fatura da {emitente} com serviços variados para {cliente}.",
]


def build_prompt(data: dict) -> str:
    """Gera um prompt criativo a partir dos dados da fatura."""
    emitente  = data.get("emitente", {}).get("nome", "uma empresa")
    cliente   = data.get("cliente", {}).get("nome", "um cliente")
    total     = data.get("valor_total", "0.00")
    vencimento = data.get("data_vencimento", "")
    emissao   = data.get("data_emissao", "")
    itens     = data.get("itens", [])
    n_itens   = len(itens)

    # Extrai até 2 serviços para mencionar no prompt
    servicos_list = [i.get("descricao", "") for i in itens[:2] if i.get("descricao")]
    servicos = " e ".join(servicos_list) if servicos_list else "serviços diversos"

    template = random.choice(PROMPT_TEMPLATES)
    return template.format(
        emitente=emitente,
        cliente=cliente,
        total=total,
        vencimento=vencimento,
        emissao=emissao,
        n_itens=n_itens,
        servicos=servicos,
    )


def strip_visual_metadata(data: dict) -> dict:
    """Remove metadados_visuais — não faz parte do documento gerado."""
    return {k: v for k, v in data.items() if k != "metadados_visuais"}


def convert_split(labels_dir: Path, output_path: Path) -> int:
    if not labels_dir.exists():
        print(f"  [AVISO] {labels_dir} não encontrado, pulando.")
        return 0

    samples = []
    for label_path in sorted(labels_dir.glob("*.json")):
        data = json.loads(label_path.read_text(encoding="utf-8"))
        prompt    = build_prompt(data)
        assistant = json.dumps(strip_visual_metadata(data), ensure_ascii=False)

        samples.append({
            "messages": [
                {"role": "system",    "content": SYSTEM_PROMPT},
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": assistant},
            ]
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    return len(samples)


def main():
    parser = argparse.ArgumentParser(
        description="Prepara dataset conversacional para fine-tuning do Qwen",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input",  type=Path, default=Path("dataset"))
    parser.add_argument("--output", type=Path, default=Path("dataset/qwen"))
    parser.add_argument("--seed",   type=int,  default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    print(f"\nConvertendo {args.input} → {args.output}\n")

    splits = {"train": "train.jsonl", "val": "val.jsonl", "test": "test.jsonl"}
    total = 0
    for split, filename in splits.items():
        labels_dir  = args.input / split / "labels"
        output_path = args.output / filename
        n = convert_split(labels_dir, output_path)
        total += n
        print(f"  {split:10s} → {n:>5} amostras  ({output_path})")

    print(f"\nTotal: {total} amostras")
    print(f"Dataset Qwen salvo em: {args.output.resolve()}\n")
    print("Próximo passo:")
    print("  python scripts/train_qwen.py")


if __name__ == "__main__":
    main()
