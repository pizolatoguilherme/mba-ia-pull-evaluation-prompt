"""
Testes automatizados para validação de prompts.
"""
import re
import sys
from pathlib import Path

import pytest
import yaml

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    data = load_prompts(PROMPT_FILE)
    assert data and PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' ausente em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


def _all_text(prompt: dict) -> str:
    return f"{prompt.get('system_prompt', '')}\n{prompt.get('user_prompt', '')}"


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt
        assert isinstance(prompt["system_prompt"], str)
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system = prompt["system_prompt"]
        assert re.search(r"Você é (um|uma)\s+\w+", system), "Persona ('Você é um ...') não definida"
        assert re.search(r"Product Manager|Product Owner|Analista", system, re.IGNORECASE)

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system = prompt["system_prompt"]
        has_user_story_format = all(
            term in system for term in ("Como um", "eu quero", "para que")
        )
        assert has_user_story_format or "Markdown" in system, "Formato de User Story não exigido"
        assert "Critérios de Aceitação" in system
        assert all(term in system for term in ("Dado que", "Quando", "Então"))

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system = prompt["system_prompt"]
        examples = re.findall(r"Exemplo \d+", system)
        assert len(examples) >= 2, f"Esperado >= 2 exemplos, encontrado {len(examples)}"
        assert system.count("Entrada:") >= 2
        assert system.count("Saída:") >= 2

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        raw = PROMPT_FILE.read_text(encoding="utf-8")
        assert "[TODO]" not in raw
        assert "TODO" not in _all_text(prompt)

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied")
        assert isinstance(techniques, list)
        assert len(techniques) >= 2
        assert any("few_shot" in t for t in techniques), "Few-shot é obrigatório"

    def test_bug_report_variable_only_in_user_prompt(self, prompt):
        """{bug_report} deve estar no user_prompt e não duplicado no system_prompt."""
        assert "{bug_report}" in prompt["user_prompt"]
        assert "{bug_report}" not in prompt["system_prompt"]

    def test_template_has_single_input_variable(self, prompt):
        """O template deve ter apenas {bug_report} como variável (chaves literais escapadas)."""
        from langchain_core.prompts import ChatPromptTemplate

        template = ChatPromptTemplate.from_messages(
            [("system", prompt["system_prompt"]), ("user", prompt["user_prompt"])]
        )
        assert template.input_variables == ["bug_report"]

    def test_validate_prompt_structure(self, prompt):
        """A estrutura deve passar no validador de utils.py."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
