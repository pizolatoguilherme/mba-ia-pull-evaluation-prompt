"""
Avaliação de linha de base: roda o prompt ORIGINAL (v1) contra o mesmo dataset
e com as mesmas métricas usadas para a v2.

O src/evaluate.py (fornecido pelo desafio, não alterado) avalia apenas a v2.
Este script reaproveita as funções dele, sem modificá-lo, para gerar o
experimento de comparação v1 × v2 citado no README.

Uso (a partir da raiz do repositório):
    python src/evaluate_baseline.py
    python src/evaluate_baseline.py <owner/prompt>   # avaliar outro prompt do Hub
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

import evaluate as ev
from utils import check_env_vars, print_section_header

load_dotenv()

DEFAULT_PROMPT = "leonanluppi/bug_to_user_story_v1"
JSONL_PATH = "datasets/bug_to_user_story.jsonl"


def main():
    prompt_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    print_section_header(f"AVALIAÇÃO DE LINHA DE BASE: {prompt_name}")

    required = ["LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "LLM_PROVIDER", "LLM_MODEL", "EVAL_MODEL"]
    provider = os.getenv("LLM_PROVIDER", "")
    if provider == "openai":
        required.append("OPENAI_API_KEY")
    elif provider in ("google", "gemini"):
        required.append("GOOGLE_API_KEY")
    if not check_env_vars(required):
        return 1

    if not Path(JSONL_PATH).exists():
        print(f"❌ Dataset não encontrado: {JSONL_PATH} (execute a partir da raiz do repositório)")
        return 1

    client = Client()
    dataset_name = f"{os.getenv('LANGSMITH_PROJECT')}-eval"
    ev.create_evaluation_dataset(client, dataset_name, JSONL_PATH)

    scores, experiment_url = ev.run_experiment(client, prompt_name, dataset_name)
    passed = ev.display_results(prompt_name, scores)
    print(f"\nExperimento: {experiment_url}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
