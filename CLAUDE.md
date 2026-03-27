# context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding. A single unrouted command can dump 56 KB into context and waste the entire session.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Any Bash command containing `curl` or `wget` is intercepted and replaced with an error message. Do NOT retry.
Instead use:
- `ctx_fetch_and_index(url, source)` to fetch and index web pages
- `ctx_execute(language: "javascript", code: "const r = await fetch(...)")` to run HTTP calls in sandbox

### Inline HTTP — BLOCKED
Any Bash command containing `fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, or `http.request(` is intercepted and replaced with an error message. Do NOT retry with Bash.
Instead use:
- `ctx_execute(language, code)` to run HTTP calls in sandbox — only stdout enters context

### WebFetch — BLOCKED
WebFetch calls are denied entirely. The URL is extracted and you are told to use `ctx_fetch_and_index` instead.
Instead use:
- `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` to query the indexed content

## REDIRECTED tools — use sandbox equivalents

### Bash (>20 lines output)
Bash is ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`, and other short-output commands.
For everything else, use:
- `ctx_batch_execute(commands, queries)` — run multiple commands + search in ONE call
- `ctx_execute(language: "shell", code: "...")` — run in sandbox, only stdout enters context

### Read (for analysis)
If you are reading a file to **Edit** it → Read is correct (Edit needs content in context).
If you are reading to **analyze, explore, or summarize** → use `ctx_execute_file(path, language, code)` instead. Only your printed summary enters context. The raw file content stays in the sandbox.

### Grep (large results)
Grep results can flood context. Use `ctx_execute(language: "shell", code: "grep ...")` to run searches in sandbox. Only your printed summary enters context.

## Tool selection hierarchy

1. **GATHER**: `ctx_batch_execute(commands, queries)` — Primary tool. Runs all commands, auto-indexes output, returns search results. ONE call replaces 30+ individual calls.
2. **FOLLOW-UP**: `ctx_search(queries: ["q1", "q2", ...])` — Query indexed content. Pass ALL questions as array in ONE call.
3. **PROCESSING**: `ctx_execute(language, code)` | `ctx_execute_file(path, language, code)` — Sandbox execution. Only stdout enters context.
4. **WEB**: `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` — Fetch, chunk, index, query. Raw HTML never enters context.
5. **INDEX**: `ctx_index(content, source)` — Store content in FTS5 knowledge base for later search.

## Subagent routing

When spawning subagents (Agent/Task tool), the routing block is automatically injected into their prompt. Bash-type subagents are upgraded to general-purpose so they have access to MCP tools. You do NOT need to manually instruct subagents about context-mode.

## Output constraints

- Keep responses under 500 words.
- Write artifacts (code, configs, PRDs) to FILES — never return them as inline text. Return only: file path + 1-line description.
- When indexing content, use descriptive source labels so others can `ctx_search(source: "label")` later.

## ctx commands

| Command | Action |
|---------|--------|
| `ctx stats` | Call the `ctx_stats` MCP tool and display the full output verbatim |
| `ctx doctor` | Call the `ctx_doctor` MCP tool, run the returned shell command, display as checklist |
| `ctx upgrade` | Call the `ctx_upgrade` MCP tool, run the returned shell command, display as checklist |

---

# Arquitetura do Projeto

## Objetivo
Fábrica de documentos sintéticos para treinar modelos de Document AI (Donut, LayoutLM, etc.).
Cada tipo de documento gera: PDF · PNG (augmentado) · JSON ground truth · JSON formato Donut.

## Estrutura de Diretórios

```
Synthetic-Document-Pipeline/
│
├── documents/                  ← um pacote por tipo de documento
│   ├── base.py                 ← BaseDataGenerator, BaseExporter (ABCs)
│   ├── invoice/                ← faturas brasileiras (implementado)
│   │   ├── data_generator.py   ← Faker pt_BR + randomização visual
│   │   ├── template_engine.py  ← Jinja2 + 6 layouts HTML/CSS A4
│   │   └── exporter.py         ← orquestrador do tipo invoice
│   ├── contract/               ← futuro
│   ├── receipt/                ← futuro
│   ├── presentation/           ← futuro (pptx)
│   └── report/                 ← futuro (docx)
│
├── pipeline/                   ← infraestrutura compartilhada entre todos os tipos
│   ├── utils.py                ← exceções (PipelineError, PDFRenderError, etc.)
│   ├── pdf_renderer.py         ← WeasyPrint: HTML → PDF
│   ├── image_converter.py      ← pdf2image: PDF → PNG (requer Poppler)
│   ├── augmentor.py            ← Pillow+numpy: augmentação de imagens
│   └── donut_formatter.py      ← converte ground truth → formato Donut
│
├── scripts/
│   └── split_dataset.py        ← divide output/ em train/val/test (70/15/15)
│
├── output/<tipo>/              ← gitignored — gerado pelo generate.py
│   ├── pdfs/
│   ├── images/
│   ├── labels/
│   └── donut_labels/
│
├── dataset/                    ← gitignored — gerado pelo split_dataset.py
│   ├── train/  val/  test/
│
└── generate.py                 ← CLI principal
```

## CLI

```bash
python generate.py --type invoice --count 60 --workers 4 --dpi 150
python scripts/split_dataset.py --input output/invoice --output dataset
```

## Adicionar Novo Tipo de Documento

1. Criar `documents/<tipo>/` com `data_generator.py`, `template_engine.py`, `exporter.py`
2. Herdar de `documents.base.BaseDataGenerator` e `BaseExporter`
3. Registrar em `generate.py` dentro de `_load_registry()`
4. Infraestrutura de `pipeline/` é reaproveitada automaticamente

## Dependências do Sistema
- **Poppler** — necessário para `pdf2image` (PDF → PNG)
  - Windows: `C:\Users\bruno\poppler\poppler-25.12.0\Library\bin`
  - Linux: `apt-get install poppler-utils`
