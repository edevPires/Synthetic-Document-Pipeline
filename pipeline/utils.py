"""
pipeline/utils.py
Exceções customizadas centralizadas do Synthetic Document Pipeline.
Todos os módulos importam suas exceções daqui.
"""


class PipelineError(Exception):
    """Classe base para todos os erros do pipeline."""


class DataGenerationError(PipelineError):
    """Falha na geração de dados com Faker."""


class TemplateRenderError(PipelineError):
    """Falha na renderização do template Jinja2."""


class PDFRenderError(PipelineError):
    """Falha na renderização HTML → PDF via WeasyPrint."""


class ExportError(PipelineError):
    """Falha ao salvar arquivo (PDF ou JSON) no disco."""
