"""
documents/invoice/template_engine.py
Motor de template Jinja2 com 6 estruturas de layout distintas.
Suporta logo SVG sintético (70% dos docs) e 3 estilos de footer.
"""

from decimal import Decimal

from jinja2 import BaseLoader, Environment

from pipeline.utils import TemplateRenderError

# ---------------------------------------------------------------------------
# Macros Jinja2 reutilizáveis (logo + footer) — prefixados em cada template
# ---------------------------------------------------------------------------

MACROS = """
{% macro render_logo(logo_svg, size="normal") %}
  {% if logo_svg %}
    <div class="logo-wrap logo-{{ size }}">{{ logo_svg }}</div>
  {% endif %}
{% endmacro %}

{% macro render_footer(metadados_visuais, emitente, numero_fatura) %}
  {% if metadados_visuais.footer_estilo == "completo" %}
  <div class="footer">
    <p>{{ emitente.nome }} &mdash; CNPJ: {{ emitente.cnpj }} &mdash; {{ emitente.endereco }}</p>
    <p>Fatura N&ordm; {{ numero_fatura }} &mdash; {{ emitente.telefone }} &mdash; {{ emitente.email }}</p>
  </div>
  {% elif metadados_visuais.footer_estilo == "minimo" %}
  <div class="footer">
    <p>Fatura N&ordm; {{ numero_fatura }} &mdash; CNPJ: {{ emitente.cnpj }}</p>
  </div>
  {% endif %}
{% endmacro %}
"""

CSS_BASE = """
  @page { size: A4; margin: 20mm 15mm 20mm 15mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: {{ metadados_visuais.fonte }};
    font-size: {{ metadados_visuais.tamanho_fonte_base }};
    color: #2c2c2c;
    line-height: 1.5;
  }
  .logo-wrap { display: inline-flex; align-items: center; flex-shrink: 0; }
  .logo-wrap svg { display: block; }
"""

# ---------------------------------------------------------------------------
# 1. CLÁSSICO
# ---------------------------------------------------------------------------
TEMPLATE_CLASSICO = MACROS + """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<style>
""" + CSS_BASE + """
  .header { background: {{ metadados_visuais.cor_primaria }}; color: #fff; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; border-radius: {{ metadados_visuais.border_radius }}; margin-bottom: 16px; gap: 12px; }
  .header-left { display: flex; align-items: center; gap: 12px; }
  .header .co-name { font-size: 1.3em; font-weight: bold; }
  .header .co-cnpj { font-size: 0.82em; opacity: 0.85; }
  .header .fat-title { font-size: 1.6em; font-weight: bold; letter-spacing: 3px; }
  .meta-bar { background: {{ metadados_visuais.cor_secundaria }}; border-left: 4px solid {{ metadados_visuais.cor_primaria }}; padding: 8px 16px; display: flex; gap: 36px; margin-bottom: 16px; border-radius: 0 {{ metadados_visuais.border_radius }} {{ metadados_visuais.border_radius }} 0; }
  .meta-bar .lbl { font-size: 0.75em; color: #666; text-transform: uppercase; display: block; }
  .meta-bar .val { font-weight: bold; }
  .parties { display: flex; gap: 14px; margin-bottom: 16px; }
  .party { flex: 1; border: {{ metadados_visuais.borda_tabela }} {{ metadados_visuais.cor_primaria }}; border-radius: {{ metadados_visuais.border_radius }}; padding: 10px 13px; }
  .party h4 { color: {{ metadados_visuais.cor_primaria }}; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid {{ metadados_visuais.cor_secundaria }}; padding-bottom: 5px; margin-bottom: 7px; }
  .party p { font-size: 0.88em; margin-bottom: 2px; }
  .party .lbl { color: #777; font-size: 0.8em; }
  .sec-title { color: {{ metadados_visuais.cor_primaria }}; font-size: 0.78em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 7px; }
  table.items { width: 100%; border-collapse: collapse; margin-bottom: 14px; }
  table.items thead th { background: {{ metadados_visuais.cor_primaria }}; color: #fff; padding: {{ metadados_visuais.padding_celula }}; font-size: 0.78em; text-transform: uppercase; text-align: left; }
  table.items thead th.r { text-align: right; }
  table.items tbody tr:nth-child(even) { background: {{ metadados_visuais.cor_secundaria }}; }
  table.items tbody td { padding: {{ metadados_visuais.padding_celula }}; border-bottom: 1px solid #eee; font-size: 0.88em; }
  table.items tbody td.r { text-align: {{ metadados_visuais.alinhamento_valores }}; }
  .totals-wrap { display: flex; justify-content: flex-end; margin-bottom: 18px; }
  .totals { width: 300px; border: {{ metadados_visuais.borda_tabela }} #ccc; border-radius: {{ metadados_visuais.border_radius }}; overflow: hidden; }
  .totals .row { display: flex; justify-content: space-between; padding: 6px 13px; border-bottom: 1px solid #eee; font-size: 0.88em; }
  .totals .row:last-child { border-bottom: none; }
  .totals .row.final { background: {{ metadados_visuais.cor_primaria }}; color: #fff; font-weight: bold; }
  .totals .row.final label, .totals .row label { color: inherit; }
  .totals .row label { color: #555; }
  .obs { background: #f8f8f8; border: 1px solid #e0e0e0; border-radius: {{ metadados_visuais.border_radius }}; padding: 9px 13px; margin-bottom: 14px; font-size: 0.8em; color: #555; }
  .footer { border-top: 2px {{ metadados_visuais.borda_estilo }} {{ metadados_visuais.cor_primaria }}; padding-top: 8px; text-align: center; font-size: 0.73em; color: #888; line-height: 1.6; }
</style></head><body>
<div class="header">
  <div class="header-left">
    {{ render_logo(logo_svg) }}
    <div><div class="co-name">{{ emitente.nome }}</div><div class="co-cnpj">CNPJ: {{ emitente.cnpj }}</div></div>
  </div>
  <div class="fat-title">FATURA</div>
</div>
<div class="meta-bar">
  <div><span class="lbl">Número</span><span class="val">{{ numero_fatura }}</span></div>
  <div><span class="lbl">Emissão</span><span class="val">{{ data_emissao }}</span></div>
  <div><span class="lbl">Vencimento</span><span class="val">{{ data_vencimento }}</span></div>
</div>
<div class="parties">
  <div class="party"><h4>Emitente</h4><p><strong>{{ emitente.nome }}</strong></p><p><span class="lbl">CNPJ:</span> {{ emitente.cnpj }}</p><p><span class="lbl">End.:</span> {{ emitente.endereco }}</p><p><span class="lbl">Tel:</span> {{ emitente.telefone }} &nbsp; <span class="lbl">E-mail:</span> {{ emitente.email }}</p></div>
  <div class="party"><h4>Cliente</h4><p><strong>{{ cliente.nome }}</strong></p><p><span class="lbl">CPF/CNPJ:</span> {{ cliente.cpf_cnpj }}</p><p><span class="lbl">End.:</span> {{ cliente.endereco }}</p><p><span class="lbl">Tel:</span> {{ cliente.telefone }}</p></div>
</div>
<p class="sec-title">Itens / Serviços</p>
<table class="items">
  <thead><tr><th style="width:5%">#</th><th style="width:47%">Descrição</th><th class="r" style="width:10%">Qtd.</th><th class="r" style="width:18%">Unit.</th><th class="r" style="width:20%">Subtotal</th></tr></thead>
  <tbody>{% for item in itens %}<tr><td>{{ loop.index }}</td><td>{{ item.descricao }}</td><td class="r">{{ item.qtd }}</td><td class="r">{{ item.preco_unit | brl }}</td><td class="r">{{ item.subtotal | brl }}</td></tr>{% endfor %}</tbody>
</table>
<div class="totals-wrap"><div class="totals">
  <div class="row"><label>Subtotal</label><span>{{ subtotal | brl }}</span></div>
  <div class="row"><label>Impostos ({{ (aliquota_imposto * 100) | round(1) }}%)</label><span>{{ impostos | brl }}</span></div>
  <div class="row final"><label>TOTAL</label><span>{{ valor_total | brl }}</span></div>
</div></div>
{% if observacoes %}<div class="obs"><strong>Obs.:</strong> {{ observacoes }}</div>{% endif %}
{{ render_footer(metadados_visuais, emitente, numero_fatura) }}
</body></html>
"""

# ---------------------------------------------------------------------------
# 2. MINIMAL
# ---------------------------------------------------------------------------
TEMPLATE_MINIMAL = MACROS + """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<style>
""" + CSS_BASE + """
  .header { border-bottom: 3px solid {{ metadados_visuais.cor_primaria }}; padding-bottom: 12px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; }
  .header-left { display: flex; align-items: center; gap: 12px; }
  .header .co-name { font-size: 1.3em; font-weight: bold; color: {{ metadados_visuais.cor_primaria }}; }
  .header .co-cnpj { font-size: 0.82em; color: #666; }
  .header .fat-title { font-size: 2em; font-weight: bold; color: {{ metadados_visuais.cor_primaria }}; letter-spacing: 4px; }
  .meta-line { display: flex; gap: 30px; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #ddd; }
  .meta-line .field .lbl { font-size: 0.73em; color: #999; text-transform: uppercase; display: block; }
  .meta-line .field .val { font-weight: bold; color: #333; }
  .parties { display: flex; gap: 20px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid #ddd; }
  .party { flex: 1; }
  .party h4 { font-size: 0.73em; text-transform: uppercase; letter-spacing: 1px; color: #999; margin-bottom: 5px; }
  .party p { font-size: 0.88em; margin-bottom: 2px; color: #333; }
  .sec-title { font-size: 0.73em; text-transform: uppercase; letter-spacing: 1px; color: #999; margin-bottom: 7px; }
  table.items { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  table.items thead th { border-bottom: 2px solid {{ metadados_visuais.cor_primaria }}; padding: {{ metadados_visuais.padding_celula }}; font-size: 0.78em; text-transform: uppercase; color: {{ metadados_visuais.cor_primaria }}; text-align: left; }
  table.items thead th.r { text-align: right; }
  table.items tbody td { padding: {{ metadados_visuais.padding_celula }}; border-bottom: 1px solid #eee; font-size: 0.88em; color: #333; }
  table.items tbody td.r { text-align: {{ metadados_visuais.alinhamento_valores }}; }
  .totals { margin-left: auto; width: 260px; margin-bottom: 16px; }
  .totals .row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; font-size: 0.88em; }
  .totals .row.final { border-top: 2px solid {{ metadados_visuais.cor_primaria }}; border-bottom: none; font-weight: bold; color: {{ metadados_visuais.cor_primaria }}; font-size: 1em; margin-top: 4px; padding-top: 7px; }
  .obs { font-size: 0.8em; color: #666; margin-bottom: 14px; padding-left: 10px; border-left: 3px solid {{ metadados_visuais.cor_primaria }}; }
  .footer { border-top: 1px solid #ccc; padding-top: 8px; font-size: 0.73em; color: #aaa; display: flex; justify-content: space-between; }
</style></head><body>
<div class="header">
  <div class="header-left">
    {{ render_logo(logo_svg) }}
    <div><div class="co-name">{{ emitente.nome }}</div><div class="co-cnpj">CNPJ: {{ emitente.cnpj }}</div></div>
  </div>
  <div class="fat-title">FATURA</div>
</div>
<div class="meta-line">
  <div class="field"><span class="lbl">Número</span><span class="val">{{ numero_fatura }}</span></div>
  <div class="field"><span class="lbl">Emissão</span><span class="val">{{ data_emissao }}</span></div>
  <div class="field"><span class="lbl">Vencimento</span><span class="val">{{ data_vencimento }}</span></div>
</div>
<div class="parties">
  <div class="party"><h4>De</h4><p><strong>{{ emitente.nome }}</strong></p><p>{{ emitente.endereco }}</p><p>{{ emitente.telefone }} &nbsp;&bull;&nbsp; {{ emitente.email }}</p></div>
  <div class="party"><h4>Para</h4><p><strong>{{ cliente.nome }}</strong></p><p>CPF/CNPJ: {{ cliente.cpf_cnpj }}</p><p>{{ cliente.endereco }}</p><p>{{ cliente.telefone }}</p></div>
</div>
<p class="sec-title">Itens</p>
<table class="items">
  <thead><tr><th style="width:5%">#</th><th style="width:47%">Descrição</th><th class="r" style="width:10%">Qtd.</th><th class="r" style="width:18%">Unit.</th><th class="r" style="width:20%">Subtotal</th></tr></thead>
  <tbody>{% for item in itens %}<tr><td>{{ loop.index }}</td><td>{{ item.descricao }}</td><td class="r">{{ item.qtd }}</td><td class="r">{{ item.preco_unit | brl }}</td><td class="r">{{ item.subtotal | brl }}</td></tr>{% endfor %}</tbody>
</table>
<div class="totals">
  <div class="row"><span>Subtotal</span><span>{{ subtotal | brl }}</span></div>
  <div class="row"><span>Impostos ({{ (aliquota_imposto * 100) | round(1) }}%)</span><span>{{ impostos | brl }}</span></div>
  <div class="row final"><span>Total</span><span>{{ valor_total | brl }}</span></div>
</div>
{% if observacoes %}<div class="obs">{{ observacoes }}</div>{% endif %}
{{ render_footer(metadados_visuais, emitente, numero_fatura) }}
</body></html>
"""

# ---------------------------------------------------------------------------
# 3. LATERAL
# ---------------------------------------------------------------------------
TEMPLATE_LATERAL = MACROS + """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<style>
""" + CSS_BASE + """
  .layout { width: 100%; border-collapse: collapse; }
  .sidebar { width: 28%; background: {{ metadados_visuais.cor_primaria }}; color: #fff; vertical-align: top; padding: 18px 13px; border-radius: {{ metadados_visuais.border_radius }} 0 0 {{ metadados_visuais.border_radius }}; }
  .sidebar .logo-wrap { margin-bottom: 12px; }
  .sidebar .fat-title { font-size: 1.3em; font-weight: bold; letter-spacing: 3px; margin-bottom: 14px; opacity: 0.9; }
  .sidebar .s-lbl { font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; display: block; margin-top: 9px; }
  .sidebar .s-val { font-size: 0.88em; font-weight: bold; }
  .sidebar .divider { border: none; border-top: 1px solid rgba(255,255,255,0.25); margin: 13px 0; }
  .sidebar .co-name { font-size: 0.85em; font-weight: bold; margin-bottom: 3px; }
  .sidebar .co-detail { font-size: 0.75em; opacity: 0.8; margin-bottom: 2px; }
  .main { vertical-align: top; padding: 18px 0 18px 18px; }
  .cliente-box { margin-bottom: 14px; padding-bottom: 11px; border-bottom: 2px {{ metadados_visuais.borda_estilo }} {{ metadados_visuais.cor_primaria }}; }
  .cliente-box h4 { font-size: 0.75em; text-transform: uppercase; color: {{ metadados_visuais.cor_primaria }}; letter-spacing: 1px; margin-bottom: 5px; }
  .cliente-box p { font-size: 0.88em; margin-bottom: 2px; }
  table.items { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  table.items thead th { background: {{ metadados_visuais.cor_primaria }}; color: #fff; padding: {{ metadados_visuais.padding_celula }}; font-size: 0.76em; text-transform: uppercase; text-align: left; }
  table.items thead th.r { text-align: right; }
  table.items tbody tr:nth-child(even) { background: {{ metadados_visuais.cor_secundaria }}; }
  table.items tbody td { padding: {{ metadados_visuais.padding_celula }}; border-bottom: 1px solid #eee; font-size: 0.86em; }
  table.items tbody td.r { text-align: {{ metadados_visuais.alinhamento_valores }}; }
  .totals .row { display: flex; justify-content: space-between; padding: 5px 8px; border-bottom: 1px solid #eee; font-size: 0.86em; }
  .totals .row.final { background: {{ metadados_visuais.cor_primaria }}; color: #fff; font-weight: bold; border-radius: {{ metadados_visuais.border_radius }}; }
  .totals .row label { color: #666; }
  .totals .row.final label { color: #fff; }
  .obs { font-size: 0.78em; color: #666; padding: 8px; background: #f7f7f7; border-radius: {{ metadados_visuais.border_radius }}; margin: 10px 0; }
  .footer { font-size: 0.72em; color: #aaa; border-top: 1px solid #ddd; padding-top: 7px; margin-top: 8px; }
</style></head><body>
<table class="layout"><tr>
<td class="sidebar">
  {{ render_logo(logo_svg) }}
  <div class="fat-title">FATURA</div>
  <span class="s-lbl">Número</span><span class="s-val">{{ numero_fatura }}</span>
  <span class="s-lbl">Emissão</span><span class="s-val">{{ data_emissao }}</span>
  <span class="s-lbl">Vencimento</span><span class="s-val">{{ data_vencimento }}</span>
  <hr class="divider">
  <div class="co-name">{{ emitente.nome }}</div>
  <div class="co-detail">{{ emitente.cnpj }}</div>
  <div class="co-detail">{{ emitente.telefone }}</div>
  <div class="co-detail">{{ emitente.email }}</div>
</td>
<td class="main">
  <div class="cliente-box">
    <h4>Faturar para</h4>
    <p><strong>{{ cliente.nome }}</strong></p>
    <p>CPF/CNPJ: {{ cliente.cpf_cnpj }}</p>
    <p>{{ cliente.endereco }}</p>
    <p>{{ cliente.telefone }}</p>
  </div>
  <table class="items">
    <thead><tr><th style="width:5%">#</th><th style="width:45%">Descrição</th><th class="r" style="width:10%">Qtd.</th><th class="r" style="width:20%">Unit.</th><th class="r" style="width:20%">Subtotal</th></tr></thead>
    <tbody>{% for item in itens %}<tr><td>{{ loop.index }}</td><td>{{ item.descricao }}</td><td class="r">{{ item.qtd }}</td><td class="r">{{ item.preco_unit | brl }}</td><td class="r">{{ item.subtotal | brl }}</td></tr>{% endfor %}</tbody>
  </table>
  <div class="totals">
    <div class="row"><label>Subtotal</label><span>{{ subtotal | brl }}</span></div>
    <div class="row"><label>Impostos ({{ (aliquota_imposto * 100) | round(1) }}%)</label><span>{{ impostos | brl }}</span></div>
    <div class="row final"><label>TOTAL</label><span>{{ valor_total | brl }}</span></div>
  </div>
  {% if observacoes %}<div class="obs"><strong>Obs.:</strong> {{ observacoes }}</div>{% endif %}
  {{ render_footer(metadados_visuais, emitente, numero_fatura) }}
</td>
</tr></table>
</body></html>
"""

# ---------------------------------------------------------------------------
# 4. CORPORATIVO
# ---------------------------------------------------------------------------
TEMPLATE_CORPORATIVO = MACROS + """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<style>
""" + CSS_BASE + """
  .header-top { background: {{ metadados_visuais.cor_primaria }}; color: #fff; padding: 10px 16px; border-radius: {{ metadados_visuais.border_radius }} {{ metadados_visuais.border_radius }} 0 0; display: flex; align-items: center; justify-content: center; gap: 14px; }
  .header-top .co-info { text-align: center; }
  .header-top .co-name { font-size: 1.25em; font-weight: bold; }
  .header-top .co-sub { font-size: 0.78em; opacity: 0.85; }
  .header-bot { background: {{ metadados_visuais.cor_secundaria }}; border: {{ metadados_visuais.borda_tabela }} {{ metadados_visuais.cor_primaria }}; border-top: none; padding: 7px 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-radius: 0 0 {{ metadados_visuais.border_radius }} {{ metadados_visuais.border_radius }}; }
  .header-bot .fat-id { font-size: 1.05em; font-weight: bold; color: {{ metadados_visuais.cor_primaria }}; }
  .header-bot .dates { font-size: 0.82em; color: #444; }
  .header-bot .dates span { font-weight: bold; }
  table.info { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  table.info td { padding: 8px 12px; vertical-align: top; font-size: 0.86em; border: 1px solid #ddd; }
  table.info .info-lbl { font-size: 0.72em; text-transform: uppercase; color: {{ metadados_visuais.cor_primaria }}; font-weight: bold; display: block; margin-bottom: 3px; }
  table.items { width: 100%; border-collapse: collapse; }
  table.items thead th { background: {{ metadados_visuais.cor_primaria }}; color: #fff; padding: {{ metadados_visuais.padding_celula }}; font-size: 0.78em; text-transform: uppercase; text-align: left; border: 1px solid {{ metadados_visuais.cor_primaria }}; }
  table.items thead th.r { text-align: right; }
  table.items tbody td { padding: {{ metadados_visuais.padding_celula }}; border: 1px solid #ccc; font-size: 0.86em; }
  table.items tbody td.r { text-align: {{ metadados_visuais.alinhamento_valores }}; }
  table.items tfoot td { padding: {{ metadados_visuais.padding_celula }}; border: 1px solid #ccc; font-size: 0.86em; background: #f5f5f5; }
  table.items tfoot td.r { text-align: right; }
  table.items tfoot tr.final td { background: {{ metadados_visuais.cor_primaria }}; color: #fff; font-weight: bold; }
  .obs { font-size: 0.78em; color: #555; padding: 8px 12px; border: 1px solid #ddd; margin-top: 12px; margin-bottom: 10px; }
  .footer { margin-top: 10px; border-top: 2px solid {{ metadados_visuais.cor_primaria }}; padding-top: 8px; font-size: 0.72em; color: #777; display: flex; justify-content: space-between; }
</style></head><body>
<div class="header-top">
  {{ render_logo(logo_svg) }}
  <div class="co-info">
    <div class="co-name">{{ emitente.nome }}</div>
    <div class="co-sub">CNPJ: {{ emitente.cnpj }} &nbsp;&bull;&nbsp; {{ emitente.telefone }} &nbsp;&bull;&nbsp; {{ emitente.email }}</div>
  </div>
</div>
<div class="header-bot">
  <div class="fat-id">FATURA N&ordm; {{ numero_fatura }}</div>
  <div class="dates">Emissão: <span>{{ data_emissao }}</span> &nbsp;&nbsp; Vencimento: <span>{{ data_vencimento }}</span></div>
</div>
<table class="info">
  <tr>
    <td style="width:50%"><span class="info-lbl">Emitente</span><strong>{{ emitente.nome }}</strong><br>{{ emitente.endereco }}</td>
    <td style="width:50%"><span class="info-lbl">Cliente</span><strong>{{ cliente.nome }}</strong><br>CPF/CNPJ: {{ cliente.cpf_cnpj }}<br>{{ cliente.endereco }}</td>
  </tr>
</table>
<table class="items">
  <thead><tr><th style="width:5%">#</th><th style="width:45%">Descrição</th><th class="r" style="width:10%">Qtd.</th><th class="r" style="width:20%">Unit.</th><th class="r" style="width:20%">Subtotal</th></tr></thead>
  <tbody>{% for item in itens %}<tr><td>{{ loop.index }}</td><td>{{ item.descricao }}</td><td class="r">{{ item.qtd }}</td><td class="r">{{ item.preco_unit | brl }}</td><td class="r">{{ item.subtotal | brl }}</td></tr>{% endfor %}</tbody>
  <tfoot>
    <tr><td colspan="4" class="r">Subtotal</td><td class="r">{{ subtotal | brl }}</td></tr>
    <tr><td colspan="4" class="r">Impostos ({{ (aliquota_imposto * 100) | round(1) }}%)</td><td class="r">{{ impostos | brl }}</td></tr>
    <tr class="final"><td colspan="4" class="r">TOTAL GERAL</td><td class="r">{{ valor_total | brl }}</td></tr>
  </tfoot>
</table>
{% if observacoes %}<div class="obs"><strong>Observações:</strong> {{ observacoes }}</div>{% endif %}
{{ render_footer(metadados_visuais, emitente, numero_fatura) }}
</body></html>
"""

# ---------------------------------------------------------------------------
# 5. MODERNO
# ---------------------------------------------------------------------------
TEMPLATE_MODERNO = MACROS + """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<style>
""" + CSS_BASE + """
  .header { background: {{ metadados_visuais.cor_primaria }}; color: #fff; padding: 20px 22px; margin-bottom: 0; border-radius: {{ metadados_visuais.border_radius }} {{ metadados_visuais.border_radius }} 0 0; display: flex; align-items: center; gap: 16px; }
  .header .co-name { font-size: 1.25em; font-weight: bold; }
  .header .co-sub { font-size: 0.78em; opacity: 0.8; margin-top: 2px; }
  .header .fat-badge { margin-left: auto; text-align: right; }
  .header .fat-badge .fat-word { font-size: 0.73em; text-transform: uppercase; letter-spacing: 2px; opacity: 0.8; }
  .header .fat-badge .fat-num { font-size: 1.25em; font-weight: bold; }
  .badges { background: {{ metadados_visuais.cor_secundaria }}; padding: 9px 22px; display: flex; gap: 10px; margin-bottom: 16px; border-radius: 0 0 {{ metadados_visuais.border_radius }} {{ metadados_visuais.border_radius }}; }
  .badge { background: #fff; border: 1px solid {{ metadados_visuais.cor_primaria }}; border-radius: 20px; padding: 4px 14px; font-size: 0.8em; }
  .badge .b-lbl { color: #888; font-size: 0.85em; }
  .badge .b-val { color: {{ metadados_visuais.cor_primaria }}; font-weight: bold; }
  .cards { display: flex; gap: 13px; margin-bottom: 16px; }
  .card { flex: 1; border: {{ metadados_visuais.borda_tabela }} {{ metadados_visuais.cor_primaria }}; border-radius: {{ metadados_visuais.border_radius }}; overflow: hidden; }
  .card-head { background: {{ metadados_visuais.cor_primaria }}; color: #fff; font-size: 0.72em; text-transform: uppercase; letter-spacing: 1px; padding: 5px 12px; }
  .card-body { padding: 10px 12px; font-size: 0.86em; }
  .card-body p { margin-bottom: 3px; }
  table.items { width: 100%; border-collapse: collapse; margin-bottom: 14px; }
  table.items thead th { background: {{ metadados_visuais.cor_primaria }}; color: #fff; padding: {{ metadados_visuais.padding_celula }}; font-size: 0.76em; text-transform: uppercase; text-align: left; }
  table.items thead th.r { text-align: right; }
  table.items tbody tr:nth-child(even) { background: {{ metadados_visuais.cor_secundaria }}; }
  table.items tbody td { padding: {{ metadados_visuais.padding_celula }}; border-bottom: 1px solid #eee; font-size: 0.86em; }
  table.items tbody td.r { text-align: {{ metadados_visuais.alinhamento_valores }}; }
  .total-banner { background: {{ metadados_visuais.cor_primaria }}; color: #fff; border-radius: {{ metadados_visuais.border_radius }}; padding: 10px 18px; display: flex; justify-content: flex-end; gap: 36px; margin-bottom: 14px; }
  .total-banner .t-item .t-lbl { font-size: 0.75em; opacity: 0.8; display: block; }
  .total-banner .t-item .t-val { font-weight: bold; font-size: 0.92em; }
  .total-banner .t-item.big .t-val { font-size: 1.15em; }
  .obs { font-size: 0.78em; color: #555; padding: 9px 13px; background: #f8f8f8; border-radius: {{ metadados_visuais.border_radius }}; margin-bottom: 12px; }
  .footer { text-align: center; font-size: 0.72em; color: #aaa; border-top: 1px solid #e0e0e0; padding-top: 8px; }
</style></head><body>
<div class="header">
  {{ render_logo(logo_svg) }}
  <div><div class="co-name">{{ emitente.nome }}</div><div class="co-sub">{{ emitente.cnpj }} &nbsp;&bull;&nbsp; {{ emitente.email }}</div></div>
  <div class="fat-badge"><div class="fat-word">Fatura</div><div class="fat-num">{{ numero_fatura }}</div></div>
</div>
<div class="badges">
  <div class="badge"><span class="b-lbl">Emissão </span><span class="b-val">{{ data_emissao }}</span></div>
  <div class="badge"><span class="b-lbl">Vencimento </span><span class="b-val">{{ data_vencimento }}</span></div>
</div>
<div class="cards">
  <div class="card"><div class="card-head">Emitente</div><div class="card-body"><p><strong>{{ emitente.nome }}</strong></p><p>{{ emitente.endereco }}</p><p>{{ emitente.telefone }}</p></div></div>
  <div class="card"><div class="card-head">Cliente</div><div class="card-body"><p><strong>{{ cliente.nome }}</strong></p><p>CPF/CNPJ: {{ cliente.cpf_cnpj }}</p><p>{{ cliente.endereco }}</p></div></div>
</div>
<table class="items">
  <thead><tr><th style="width:5%">#</th><th style="width:45%">Descrição</th><th class="r" style="width:10%">Qtd.</th><th class="r" style="width:20%">Unit.</th><th class="r" style="width:20%">Subtotal</th></tr></thead>
  <tbody>{% for item in itens %}<tr><td>{{ loop.index }}</td><td>{{ item.descricao }}</td><td class="r">{{ item.qtd }}</td><td class="r">{{ item.preco_unit | brl }}</td><td class="r">{{ item.subtotal | brl }}</td></tr>{% endfor %}</tbody>
</table>
<div class="total-banner">
  <div class="t-item"><span class="t-lbl">Subtotal</span><span class="t-val">{{ subtotal | brl }}</span></div>
  <div class="t-item"><span class="t-lbl">Impostos ({{ (aliquota_imposto * 100) | round(1) }}%)</span><span class="t-val">{{ impostos | brl }}</span></div>
  <div class="t-item big"><span class="t-lbl">TOTAL</span><span class="t-val">{{ valor_total | brl }}</span></div>
</div>
{% if observacoes %}<div class="obs"><strong>Obs.:</strong> {{ observacoes }}</div>{% endif %}
{{ render_footer(metadados_visuais, emitente, numero_fatura) }}
</body></html>
"""

# ---------------------------------------------------------------------------
# 6. SIMPLES
# ---------------------------------------------------------------------------
TEMPLATE_SIMPLES = MACROS + """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<style>
""" + CSS_BASE + """
  .header-simple { display: flex; align-items: center; gap: 14px; margin-bottom: 6px; }
  .fat-title { font-size: 2em; font-weight: bold; color: {{ metadados_visuais.cor_primaria }}; }
  .fat-num { font-size: 0.9em; color: #555; margin-bottom: 12px; }
  hr { border: none; border-top: 1px solid #ccc; margin: 10px 0; }
  hr.thick { border-top: 2px solid {{ metadados_visuais.cor_primaria }}; }
  .two-col { display: flex; gap: 22px; margin-bottom: 10px; }
  .col { flex: 1; }
  .col h4 { font-size: 0.75em; text-transform: uppercase; color: {{ metadados_visuais.cor_primaria }}; letter-spacing: 1px; margin-bottom: 4px; }
  .col p { font-size: 0.88em; margin-bottom: 2px; color: #333; }
  .dates-row { display: flex; gap: 28px; margin-bottom: 10px; font-size: 0.86em; }
  .dates-row .d .lbl { color: #888; font-size: 0.85em; display: block; }
  .dates-row .d .val { font-weight: bold; }
  table.items { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
  table.items thead th { border-bottom: 2px solid #333; padding: {{ metadados_visuais.padding_celula }}; font-size: 0.82em; text-align: left; }
  table.items thead th.r { text-align: right; }
  table.items tbody td { padding: {{ metadados_visuais.padding_celula }}; border-bottom: 1px solid #ddd; font-size: 0.86em; }
  table.items tbody td.r { text-align: {{ metadados_visuais.alinhamento_valores }}; }
  .totals-simple { margin-left: auto; width: 240px; margin-bottom: 12px; }
  .totals-simple .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.86em; border-bottom: 1px dotted #ccc; }
  .totals-simple .row.final { border-bottom: none; border-top: 2px solid {{ metadados_visuais.cor_primaria }}; font-weight: bold; color: {{ metadados_visuais.cor_primaria }}; font-size: 1em; padding-top: 6px; margin-top: 4px; }
  .obs { font-size: 0.8em; color: #555; margin-bottom: 10px; }
  .footer { font-size: 0.72em; color: #999; text-align: center; margin-top: 8px; }
</style></head><body>
<div class="header-simple">
  {{ render_logo(logo_svg) }}
  <div class="fat-title">FATURA</div>
</div>
<div class="fat-num">N&ordm; {{ numero_fatura }}</div>
<hr class="thick">
<div class="two-col">
  <div class="col"><h4>Emitente</h4><p><strong>{{ emitente.nome }}</strong></p><p>CNPJ: {{ emitente.cnpj }}</p><p>{{ emitente.endereco }}</p><p>{{ emitente.telefone }} &nbsp;&bull;&nbsp; {{ emitente.email }}</p></div>
  <div class="col"><h4>Cliente</h4><p><strong>{{ cliente.nome }}</strong></p><p>CPF/CNPJ: {{ cliente.cpf_cnpj }}</p><p>{{ cliente.endereco }}</p><p>{{ cliente.telefone }}</p></div>
</div>
<hr>
<div class="dates-row">
  <div class="d"><span class="lbl">Data de Emissão</span><span class="val">{{ data_emissao }}</span></div>
  <div class="d"><span class="lbl">Vencimento</span><span class="val">{{ data_vencimento }}</span></div>
</div>
<hr>
<table class="items">
  <thead><tr><th style="width:5%">#</th><th style="width:47%">Descrição</th><th class="r" style="width:10%">Qtd.</th><th class="r" style="width:18%">Unit.</th><th class="r" style="width:20%">Subtotal</th></tr></thead>
  <tbody>{% for item in itens %}<tr><td>{{ loop.index }}</td><td>{{ item.descricao }}</td><td class="r">{{ item.qtd }}</td><td class="r">{{ item.preco_unit | brl }}</td><td class="r">{{ item.subtotal | brl }}</td></tr>{% endfor %}</tbody>
</table>
<div class="totals-simple">
  <div class="row"><span>Subtotal</span><span>{{ subtotal | brl }}</span></div>
  <div class="row"><span>Impostos ({{ (aliquota_imposto * 100) | round(1) }}%)</span><span>{{ impostos | brl }}</span></div>
  <div class="row final"><span>TOTAL</span><span>{{ valor_total | brl }}</span></div>
</div>
{% if observacoes %}<hr><div class="obs">{{ observacoes }}</div>{% endif %}
<hr>
{{ render_footer(metadados_visuais, emitente, numero_fatura) }}
</body></html>
"""

# ---------------------------------------------------------------------------
# Mapa de layouts
# ---------------------------------------------------------------------------
TEMPLATES = {
    "classico":    TEMPLATE_CLASSICO,
    "minimal":     TEMPLATE_MINIMAL,
    "lateral":     TEMPLATE_LATERAL,
    "corporativo": TEMPLATE_CORPORATIVO,
    "moderno":     TEMPLATE_MODERNO,
    "simples":     TEMPLATE_SIMPLES,
}


class TemplateEngine:
    def __init__(self) -> None:
        self.env = Environment(loader=BaseLoader(), autoescape=False)
        self.env.filters["brl"] = self._format_brl
        self.env.filters["round"] = round

    def render(self, data: dict) -> str:
        layout = data["metadados_visuais"]["layout"]
        template_str = TEMPLATES.get(layout, TEMPLATE_CLASSICO)
        try:
            template = self.env.from_string(template_str)
            return template.render(**data)
        except Exception as exc:
            raise TemplateRenderError(f"Falha ao renderizar template '{layout}': {exc}") from exc

    @staticmethod
    def _format_brl(value: Decimal) -> str:
        formatted = f"{float(value):,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
