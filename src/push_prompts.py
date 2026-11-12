"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

Uso:
    python src/push_prompts.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

from utils import check_env_vars, load_yaml, print_section_header, validate_prompt_structure

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_NAME = "bug_to_user_story_v2"
REQUIRED_INPUT_VARIABLE = "bug_report"


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o ChatPromptTemplate (system + user) a partir dos dados do YAML."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    full_name = f"{username}/{prompt_name}"

    try:
        prompt = build_chat_prompt(prompt_data)
    except Exception as e:
        print(f"❌ Erro ao montar o ChatPromptTemplate: {e}")
        return False

    techniques = prompt_data.get("techniques_applied", [])
    tags = list(dict.fromkeys(
        list(prompt_data.get("tags", []))
        + [prompt_data.get("version", "v2")]
        + [f"technique:{t}" for t in techniques]
    ))
    description = prompt_data.get("description", "")
    if techniques:
        description = f"{description} | Técnicas: {', '.join(techniques)}"

    print(f"⬆️  Fazendo push de '{full_name}'...")
    print(f"   Variáveis: {prompt.input_variables}")
    print(f"   Tags: {tags}")

    client = Client()
    try:
        url = client.push_prompt(
            full_name,
            object=prompt,
            is_public=True,
            description=description,
            readme=prompt_data.get("readme"),
            tags=tags,
        )
    except Exception as e:
        # O Hub rejeita commits idênticos ao último: não é um erro real
        if "nothing to commit" in str(e).lower() or "409" in str(e):
            print("ℹ️  Nenhuma alteração desde o último push — o prompt já está atualizado.")
            return True
        print(f"❌ Erro ao fazer push: {e}")
        return False

    print(f"✅ Push realizado: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)
    errors = list(errors)

    system_prompt = prompt_data.get("system_prompt", "") or ""
    user_prompt = prompt_data.get("user_prompt", "") or ""

    if not user_prompt.strip():
        errors.append("user_prompt está vazio")

    placeholder = "{" + REQUIRED_INPUT_VARIABLE + "}"
    if placeholder not in user_prompt:
        errors.append(f"user_prompt deve conter a variável {placeholder}")
    if placeholder in system_prompt:
        errors.append(f"{placeholder} não deve aparecer no system_prompt (duplicação)")

    if "[TODO]" in system_prompt or "[TODO]" in user_prompt:
        errors.append("Prompt ainda contém [TODO]")

    if not errors:
        try:
            variables = build_chat_prompt(prompt_data).input_variables
            if variables != [REQUIRED_INPUT_VARIABLE]:
                errors.append(
                    f"Variáveis de entrada inesperadas: {variables} "
                    f"(esperado apenas ['{REQUIRED_INPUT_VARIABLE}']; escape chaves literais com {{{{ }}}})"
                )
        except Exception as e:
            errors.append(f"Template inválido: {e}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data:
        return 1

    prompt_data = data.get(PROMPT_NAME)
    if not prompt_data:
        print(f"❌ Chave '{PROMPT_NAME}' não encontrada em {PROMPT_FILE.name}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1
    print("✅ Prompt validado")

    if not push_prompt_to_langsmith(PROMPT_NAME, prompt_data):
        return 1

    print("\nPróximo passo: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
