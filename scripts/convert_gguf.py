"""
scripts/convert_gguf.py
Converte o modelo mesclado (HuggingFace) para GGUF usando o llama.cpp.

Pré-requisito: llama.cpp clonado e compilado (ou instalado via pip install llama-cpp-python).

Uso:
    python scripts/convert_gguf.py
    python scripts/convert_gguf.py --model models/qwen-invoice-merged --output models/qwen-invoice.gguf --quantization Q4_K_M
"""

import argparse
import subprocess
import sys
from pathlib import Path


QUANTIZATIONS = ["Q4_K_M", "Q5_K_M", "Q8_0", "F16"]

# Caminho padrão do llama.cpp — ajuste se necessário
DEFAULT_LLAMACPP = Path("C:/Users/bruno/OneDrive/Documentos/GitHub/Local-LLM-Document-Assistant/llama.cpp")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converte modelo HuggingFace para GGUF via llama.cpp",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model",        type=Path, default=Path("models/qwen-invoice-merged"))
    parser.add_argument("--output",       type=Path, default=Path("models/qwen-invoice.gguf"))
    parser.add_argument("--quantization", type=str,  default="Q4_K_M", choices=QUANTIZATIONS)
    parser.add_argument("--llamacpp",     type=Path, default=DEFAULT_LLAMACPP,
                        help="Diretório raiz do llama.cpp")
    return parser.parse_args()


def main():
    args = parse_args()

    convert_script = args.llamacpp / "convert_hf_to_gguf.py"
    quantize_bin   = args.llamacpp / "build" / "bin" / "llama-quantize"

    if not convert_script.exists():
        print(f"ERRO: Script de conversão não encontrado: {convert_script}")
        print("Clone e compile o llama.cpp: https://github.com/ggerganov/llama.cpp")
        sys.exit(1)

    # Passo 1: HuggingFace → GGUF F16
    gguf_f16 = args.output.with_suffix(".f16.gguf")
    print(f"[1/2] Convertendo {args.model} → {gguf_f16} (F16)...")
    result = subprocess.run(
        [sys.executable, str(convert_script), str(args.model),
         "--outfile", str(gguf_f16), "--outtype", "f16"],
        check=True,
    )

    # Passo 2: Quantização
    if not quantize_bin.exists():
        print(f"\nAVISO: llama-quantize não encontrado em {quantize_bin}")
        print(f"Arquivo F16 salvo em: {gguf_f16}")
        print("Compile o llama.cpp para aplicar quantização.")
        return

    print(f"[2/2] Quantizando para {args.quantization} → {args.output}...")
    subprocess.run(
        [str(quantize_bin), str(gguf_f16), str(args.output), args.quantization],
        check=True,
    )

    # Remove o F16 intermediário
    gguf_f16.unlink(missing_ok=True)

    print(f"\nConcluído! GGUF salvo em: {args.output.resolve()}")
    print("Copie o arquivo para o diretório models/ do Local-LLM-Document-Assistant.")


if __name__ == "__main__":
    main()
