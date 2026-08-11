"""Testes do extrator heurístico de genes (F2 replay).

Valida que texto clínico de anamnese/evolução é convertido em Expressões
de genes (0-10 + direção) com evidência de texto.
"""

from __future__ import annotations

from services.historical_gene_extractor import extract_genes_from_text


class TestExtractGenesFromText:
    def test_sono_insonia(self):
        genes = extract_genes_from_text("Paciente relata insônia crônica")
        by_gene = {g.gene: g for g in genes}
        assert "sono" in by_gene
        assert by_gene["sono"].value == 2.0
        assert by_gene["sono"].direction == "worse"
        assert by_gene["sono"].evidence_text == "insônia"

    def test_dor_alta(self):
        genes = extract_genes_from_text("dor intensa em membro inferior")
        by_gene = {g.gene: g for g in genes}
        assert "dor" in by_gene
        assert by_gene["dor"].value == 8.0  # escala dor: alto = mais dor
        assert by_gene["dor"].direction == "worse"  # dor: maior = pior

    def test_sem_dor(self):
        genes = extract_genes_from_text("sem dor")
        by_gene = {g.gene: g for g in genes}
        assert "dor" in by_gene
        assert by_gene["dor"].value == 1.0  # escala dor: baixo = sem dor
        assert by_gene["dor"].direction == "better"

    def test_evolucao_boa(self):
        genes = extract_genes_from_text("Paciente com boa evolução, dorme bem")
        by_gene = {g.gene: g for g in genes}
        assert "saude" in by_gene
        assert by_gene["saude"].value == 8.0
        assert by_gene["saude"].direction == "better"
        assert "sono" in by_gene

    def test_empty_text(self):
        assert extract_genes_from_text("") == ()
        assert extract_genes_from_text(None) == ()

    def test_one_expression_per_gene(self):
        # A primeira keyword que casa define a expressão do gene
        genes = extract_genes_from_text("insônia, mas hoje dorme bem")
        by_gene = {g.gene: g for g in genes}
        assert "sono" in by_gene
        # 'insônia' vem primeiro no mapa → 2.0 (não sobrescreve para 'dorme bem')
        assert by_gene["sono"].value == 2.0

    def test_une_cene_gene_multiples(self):
        genes = extract_genes_from_text("Paciente com ansiedade, estresse e dor")
        genes_set = {g.gene for g in genes}
        assert {"ansiedade", "estresse", "dor"} <= genes_set
