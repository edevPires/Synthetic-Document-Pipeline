"""
documents/invoice/data_generator.py
Geração de dados sintéticos brasileiros com Faker + randomização visual.
"""

import random
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta

from faker import Faker

from pipeline.utils import DataGenerationError


class DataGenerator:
    FONT_FAMILIES = [
        "Arial, sans-serif",
        "Georgia, serif",
        "'Courier New', monospace",
        "Verdana, sans-serif",
        "Trebuchet MS, sans-serif",
        "'Palatino Linotype', Palatino, serif",
        "Garamond, serif",
        "Tahoma, sans-serif",
        "'Century Gothic', sans-serif",
        "'Book Antiqua', Palatino, serif",
    ]

    PRIMARY_COLORS = [
        "#1a5276",  # azul escuro
        "#1e8449",  # verde escuro
        "#2e4057",  # azul aço
        "#6c3483",  # roxo
        "#784212",  # marrom
        "#1a6b8a",  # azul petróleo
        "#145a32",  # verde floresta
        "#2c3e50",  # azul meia-noite
        "#b7950b",  # dourado escuro
        "#922b21",  # vermelho escuro
        "#1f618d",  # azul royal
        "#117a65",  # verde água
        "#6e2f1a",  # terracota
        "#4a235a",  # vinho
        "#1b4f72",  # azul marinho
        "#0e6655",  # verde musgo
        "#5d6d7e",  # cinza azulado
        "#2e86c1",  # azul médio
    ]

    BORDER_WIDTHS = ["1px", "1.5px", "2px"]
    BORDER_STYLES = ["solid", "dashed"]
    BORDER_RADIUS = ["0px", "4px", "8px"]

    ALIGNMENTS = ["left", "right", "center"]
    FONT_SIZES = ["10px", "11px", "12px"]

    LOGO_STYLES = ["nenhum", "circulo", "quadrado"]
    HEADER_LAYOUTS = ["horizontal", "centralizado"]
    TABLE_HEADER_STYLES = ["preenchido", "contornado"]
    TABLE_DENSITIES = ["compacto", "normal", "espacoso"]
    LAYOUTS = ["classico", "minimal", "lateral", "corporativo", "moderno", "simples"]

    PRODUTOS_SERVICOS = [
        "Consultoria em TI",
        "Desenvolvimento de Software",
        "Suporte Técnico",
        "Licença de Software",
        "Treinamento Corporativo",
        "Análise de Dados",
        "Infraestrutura Cloud",
        "Segurança da Informação",
        "Design Gráfico",
        "Marketing Digital",
        "Auditoria de Sistemas",
        "Gestão de Projetos",
        "Integração de APIs",
        "Migração de Banco de Dados",
        "Hospedagem de Servidores",
        "Manutenção Preventiva",
        "Desenvolvimento Mobile",
        "UX/UI Research",
        "Backup e Recuperação de Dados",
        "Implantação de ERP",
        "Automação de Processos",
        "Consultoria em LGPD",
        "Desenvolvimento de APIs REST",
        "Monitoramento de Sistemas",
        "Gestão de Identidade e Acesso",
    ]

    def __init__(self) -> None:
        self.fake = Faker("pt_BR")

    def generate(self, layout: str = None) -> dict:
        """Retorna dict completo com dados do documento + metadados visuais."""
        try:
            visuais = self._gerar_visuais(layout=layout)
            itens = self._gerar_itens()
            subtotal = sum(item["subtotal"] for item in itens)
            aliquota = Decimal(str(random.randint(5, 12))) / Decimal("100")
            impostos = (subtotal * aliquota).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            valor_total = subtotal + impostos

            data_emissao = self.fake.date_between(start_date="-1y", end_date="today")
            data_vencimento = data_emissao + timedelta(days=30)

            emitente = self._gerar_emitente()
            iniciais = self._extrair_iniciais(emitente["nome"])
            logo_svg = self._gerar_logo(visuais["cor_primaria"], visuais["cor_secundaria"], iniciais)

            return {
                "numero_fatura": self._gerar_numero_fatura(data_emissao),
                "data_emissao": data_emissao.strftime("%d/%m/%Y"),
                "data_vencimento": data_vencimento.strftime("%d/%m/%Y"),
                "emitente": emitente,
                "emitente_iniciais": iniciais,
                "logo_svg": logo_svg,
                "cliente": self._gerar_cliente(),
                "itens": itens,
                "subtotal": subtotal,
                "aliquota_imposto": aliquota,
                "impostos": impostos,
                "valor_total": valor_total,
                "observacoes": self._gerar_observacoes(),
                "metadados_visuais": visuais,
            }
        except Exception as exc:
            raise DataGenerationError(f"Falha ao gerar dados: {exc}") from exc

    def _gerar_numero_fatura(self, data_emissao: date) -> str:
        sequencial = random.randint(1, 99999)
        return f"FAT-{data_emissao.year}-{sequencial:05d}"

    def _gerar_emitente(self) -> dict:
        nome = f"{self.fake.company()} {self.fake.company_suffix()}"
        return {
            "nome": nome,
            "cnpj": self.fake.cnpj(),
            "endereco": (
                f"{self.fake.street_name()}, {self.fake.building_number()}, "
                f"{self.fake.bairro()}, {self.fake.city()}/{self.fake.state_abbr()}, "
                f"{self.fake.postcode()}"
            ),
            "telefone": self.fake.phone_number(),
            "email": f"faturamento@{nome.lower().split()[0].replace(',', '')}.com.br",
        }

    def _gerar_cliente(self) -> dict:
        is_pj = random.random() < 0.3
        if is_pj:
            nome = f"{self.fake.company()} {self.fake.company_suffix()}"
            cpf_cnpj = self.fake.cnpj()
        else:
            nome = self.fake.name()
            cpf_cnpj = self.fake.cpf()
        return {
            "nome": nome,
            "cpf_cnpj": cpf_cnpj,
            "endereco": (
                f"{self.fake.street_name()}, {self.fake.building_number()}, "
                f"{self.fake.bairro()}, {self.fake.city()}/{self.fake.state_abbr()}, "
                f"{self.fake.postcode()}"
            ),
            "telefone": self.fake.phone_number(),
        }

    def _gerar_itens(self) -> list:
        n = random.randint(3, 8)
        produtos = random.sample(self.PRODUTOS_SERVICOS, min(n, len(self.PRODUTOS_SERVICOS)))
        itens = []
        for produto in produtos:
            qtd = random.randint(1, 20)
            preco_unit = Decimal(str(random.uniform(50, 2000))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            subtotal = (Decimal(qtd) * preco_unit).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            itens.append({
                "descricao": produto,
                "qtd": qtd,
                "preco_unit": preco_unit,
                "subtotal": subtotal,
            })
        return itens

    def _gerar_observacoes(self) -> str:
        if random.random() < 0.5:
            opcoes = [
                "Pagamento via PIX ou transferência bancária. Após o vencimento, incidirá multa de 2% e juros de 1% ao mês.",
                f"Serviços prestados conforme contrato nº {random.randint(100, 999)}/2024. Dúvidas: financeiro@empresa.com.br.",
                "Esta fatura substitui qualquer documento anterior referente ao mesmo período. Conserve-a para fins fiscais.",
                "Os serviços descritos foram executados integralmente no período acordado. Agradecemos a preferência.",
                "Boleto disponível no portal do cliente. Em caso de pagamento efetuado, desconsidere este documento.",
                f"Ref. Pedido nº {random.randint(1000, 9999)}. Prazo de contestação: 5 dias úteis após o recebimento.",
                "NF-e será emitida em até 2 dias úteis após a confirmação do pagamento.",
            ]
            return random.choice(opcoes)
        return ""

    def _gerar_visuais(self, layout: str = None) -> dict:
        cor_primaria = random.choice(self.PRIMARY_COLORS)
        cor_secundaria = self._lighten_hex(cor_primaria, 0.85)
        borda_estilo = random.choice(self.BORDER_STYLES)
        borda_largura = random.choice(self.BORDER_WIDTHS)
        densidade = random.choice(self.TABLE_DENSITIES)
        padding_celula = {"compacto": "5px 8px", "normal": "7px 10px", "espacoso": "10px 14px"}[densidade]

        return {
            "fonte": random.choice(self.FONT_FAMILIES),
            "cor_primaria": cor_primaria,
            "cor_secundaria": cor_secundaria,
            "borda_tabela": f"{borda_largura} {borda_estilo}",
            "borda_estilo": borda_estilo,
            "borda_largura": borda_largura,
            "border_radius": random.choice(self.BORDER_RADIUS),
            "alinhamento_valores": random.choice(self.ALIGNMENTS),
            "tamanho_fonte_base": random.choice(self.FONT_SIZES),
            "logo_estilo": random.choice(self.LOGO_STYLES),
            "header_layout": random.choice(self.HEADER_LAYOUTS),
            "cabecalho_tabela": random.choice(self.TABLE_HEADER_STYLES),
            "densidade_tabela": densidade,
            "padding_celula": padding_celula,
            "layout": layout if layout in self.LAYOUTS else random.choice(self.LAYOUTS),
            "footer_estilo": random.choices(
                ["completo", "minimo", "nenhum"], weights=[50, 30, 20]
            )[0],
        }

    @staticmethod
    def _gerar_logo(cor_primaria: str, cor_secundaria: str, iniciais: str):
        """70% chance de gerar um logo SVG sintético; 30% retorna None."""
        if random.random() < 0.3:
            return None
        estilo = random.randint(1, 5)
        ini = iniciais[:2]
        if estilo == 1:  # Círculo sólido
            return (
                f'<svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">'
                f'<circle cx="25" cy="25" r="24" fill="{cor_primaria}"/>'
                f'<text x="25" y="32" text-anchor="middle" fill="white" '
                f'font-size="18" font-weight="bold" font-family="Arial,sans-serif">{ini}</text>'
                f'</svg>'
            )
        elif estilo == 2:  # Quadrado arredondado
            return (
                f'<svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">'
                f'<rect x="2" y="2" width="46" height="46" rx="10" fill="{cor_primaria}"/>'
                f'<text x="25" y="32" text-anchor="middle" fill="white" '
                f'font-size="18" font-weight="bold" font-family="Arial,sans-serif">{ini}</text>'
                f'</svg>'
            )
        elif estilo == 3:  # Diamante
            return (
                f'<svg width="50" height="50" xmlns="http://www.w3.org/2000/svg">'
                f'<polygon points="25,2 48,25 25,48 2,25" fill="{cor_primaria}"/>'
                f'<text x="25" y="30" text-anchor="middle" fill="white" '
                f'font-size="14" font-weight="bold" font-family="Arial,sans-serif">{ini}</text>'
                f'</svg>'
            )
        elif estilo == 4:  # Escudo
            return (
                f'<svg width="50" height="56" xmlns="http://www.w3.org/2000/svg">'
                f'<path d="M25,2 L48,12 L48,32 Q48,50 25,54 Q2,50 2,32 L2,12 Z" fill="{cor_primaria}"/>'
                f'<text x="25" y="34" text-anchor="middle" fill="white" '
                f'font-size="15" font-weight="bold" font-family="Arial,sans-serif">{ini}</text>'
                f'</svg>'
            )
        else:  # Dois círculos sobrepostos
            return (
                f'<svg width="64" height="42" xmlns="http://www.w3.org/2000/svg">'
                f'<circle cx="21" cy="21" r="20" fill="{cor_primaria}"/>'
                f'<circle cx="43" cy="21" r="20" fill="{cor_secundaria}" '
                f'stroke="{cor_primaria}" stroke-width="1.5"/>'
                f'<text x="32" y="26" text-anchor="middle" fill="white" '
                f'font-size="13" font-weight="bold" font-family="Arial,sans-serif">{ini}</text>'
                f'</svg>'
            )

    @staticmethod
    def _extrair_iniciais(nome: str) -> str:
        """Extrai até 2 iniciais do nome da empresa."""
        palavras = [p for p in nome.split() if p[0].isupper()]
        return "".join(p[0] for p in palavras[:2]).upper()

    @staticmethod
    def _lighten_hex(hex_color: str, factor: float) -> str:
        """Clareia uma cor hex misturando com branco pelo fator informado (0-1)."""
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
