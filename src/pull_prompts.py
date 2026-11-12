"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

Uso:
    python src/pull_prompts.py
"""

import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import (
    AIMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langsmith import Client

from utils import check_env_vars, print_section_header, save_yaml

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Prompts semente a serem baixados: (identificador no Hub, nome local)
PROMPTS_TO_PULL = [
    ("leonanluppi/bug_to_user_story_v1", "bug_to_user_story_v1"),
]


def prompt_to_dict(prompt: ChatPromptTemplate, hub_id: str) -> dict:
    """
    Converte um ChatPromptTemplate no formato YAML usado pelo projeto
    (system_prompt / user_prompt + metadados).
    """
    system_parts, user_parts, other_messages = [], [], []

    for message in prompt.messages:
        template = getattr(getattr(message, "prompt", None), "template", None)
        if template is None:
            # Mensagens sem template (ex: placeholders) são registradas à parte
            other_messages.append(repr(message))
            continue

        if isinstance(message, SystemMessagePromptTemplate):
            system_parts.append(template)
        elif isinstance(message, HumanMessagePromptTemplate):
            user_parts.append(template)
        elif isinstance(message, AIMessagePromptTemplate):
            other_messages.append(f"ai: {template}")
        else:
            other_messages.append(f"{type(message).__name__}: {template}")

    metadata = getattr(prompt, "metadata", None) or {}

    data = {
        "description": metadata.get(
            "description", "Prompt para converter relatos de bugs em User Stories"
        ),
        "system_prompt": "\n\n".join(system_parts),
        "user_prompt": "\n\n".join(user_parts),
        "input_variables": list(prompt.input_variables),
        "source": hub_id,
        "version": hub_id.rsplit("_", 1)[-1] if "_v" in hub_id else "v1",
        "pulled_at": date.today().isoformat(),
        "tags": ["bug-analysis", "user-story", "product-management"],
    }
    if other_messages:
        data["other_messages"] = other_messages
    return data


HEADER = """\
# Prompt inicial de BAIXA QUALIDADE, obtido do LangSmith Prompt Hub com
#   python src/pull_prompts.py   (fonte: {hub_id})
# Problemas intencionais: {{bug_report}} duplicado no system e no user prompt,
# instruções vagas, falta de exemplos, sem persona definida e sem formato de saída.
# A versão otimizada está em prompts/bug_to_user_story_v2.yml.

"""


def add_header(path: Path, hub_id: str) -> None:
    """Acrescenta um cabeçalho explicativo ao YAML gerado (save_yaml não grava comentários)."""
    content = path.read_text(encoding="utf-8")
    path.write_text(HEADER.format(hub_id=hub_id) + content, encoding="utf-8")


def pull_prompts_from_langsmith() -> bool:
    """Faz pull de todos os prompts semente e salva cada um em prompts/<nome>.yml."""
    client = Client()
    all_ok = True

    for hub_id, local_name in PROMPTS_TO_PULL:
        print(f"⬇️  Fazendo pull de '{hub_id}'...")
        try:
            prompt = client.pull_prompt(hub_id, dangerously_pull_public_prompt=True)
        except Exception as e:
            print(f"❌ Erro ao fazer pull de '{hub_id}': {e}")
            all_ok = False
            continue

        if not isinstance(prompt, ChatPromptTemplate):
            print(f"❌ Tipo inesperado retornado: {type(prompt).__name__}")
            all_ok = False
            continue

        data = {local_name: prompt_to_dict(prompt, hub_id)}
        output_path = PROMPTS_DIR / f"{local_name}.yml"

        if save_yaml(data, str(output_path)):
            add_header(output_path, hub_id)
            print(f"✅ Prompt salvo em {output_path.relative_to(PROJECT_ROOT)}")
            print(f"   Variáveis de entrada: {data[local_name]['input_variables']}")
        else:
            all_ok = False

    return all_ok


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if not pull_prompts_from_langsmith():
        print("\n❌ Pull concluído com erros.")
        return 1

    print("\n✅ Pull concluído com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
