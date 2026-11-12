# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Solução do desafio do módulo **Prompt Engineering** (MBA IA – Full Cycle).
O enunciado original está no [repositório base](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt).

O projeto:

1. faz **pull** do prompt de baixa qualidade `leonanluppi/bug_to_user_story_v1` do LangSmith Prompt Hub;
2. **refatora** esse prompt em `prompts/bug_to_user_story_v2.yml` com técnicas avançadas de Prompt Engineering;
3. faz **push** público da versão otimizada para `pizolatoguilherme/bug_to_user_story_v2`;
4. **avalia** a v2 contra um dataset de 15 bugs com 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision), todas **≥ 0.8**.

### Resultado final

| Métrica | v1 (original) | **v2 (otimizado)** | Δ |
|---|---|---|---|
| Helpfulness | 0.84 | **0.87** ✓ | +0.03 |
| Correctness | 0.78 ✗ | **0.86** ✓ | +0.08 |
| F1-Score | 0.73 ✗ | **0.88** ✓ | +0.15 |
| Clarity | 0.86 | **0.89** ✓ | +0.03 |
| Precision | 0.82 | **0.85** ✓ | +0.03 |
| **Média** | 0.81 — ❌ REPROVADO | **0.87 — ✅ APROVADO** | +0.06 |

> Os dois prompts foram avaliados com os mesmos modelos (`gpt-5.4-mini` gerando e `gpt-5.4` avaliando), o mesmo dataset e as mesmas métricas. A v2 foi avaliada com `python src/evaluate.py`, e a v1 com `python src/evaluate_baseline.py`, que reaproveita as funções do `evaluate.py` sem alterá-lo.

---

## Técnicas Aplicadas (Fase 2)

O prompt otimizado combina **quatro técnicas**, declaradas nos metadados do YAML (`techniques_applied`):

| Técnica | Por que foi escolhida | Onde está no prompt |
|---|---|---|
| **Role Prompting** | A tarefa exige o olhar de quem escreve backlog. Definir a persona orienta o vocabulário (BDD, OWASP, SLA) e o tom. | Seção `# PAPEL` |
| **Few-shot Learning** (obrigatória) | Os juízes comparam a resposta com uma referência de formato bem específico. Exemplos de entrada e saída são a forma mais eficaz de fixar esse formato. | Seção `# EXEMPLOS (few-shot)`, com 4 exemplos |
| **Chain of Thought (interno)** | Converter um bug em história exige raciocínio: quem é afetado, o que deveria acontecer, qual o benefício, quais dados preservar e qual a complexidade. O raciocínio é feito **sem ser escrito na resposta**, porque texto extra derruba a Precision. | Seção `# PROCESSO DE RACIOCÍNIO` |
| **Skeleton of Thought** | O dataset tem 3 níveis de complexidade, cada um com uma estrutura de resposta diferente. Esqueletos explícitos por nível garantem estrutura e tamanho proporcionais ao bug. | Seções `# CLASSIFICAÇÃO DE COMPLEXIDADE` e `# ESQUELETOS DE SAÍDA` |

Além das técnicas, o prompt inclui **regras explícitas de comportamento** (`# REGRAS OBRIGATÓRIAS`) e **tratamento de edge cases** (`# CASOS ESPECIAIS`): relato vago, logs e stack traces, múltiplos problemas, segurança, perda de dados, pedido de funcionalidade e relato vazio.

### Exemplos práticos de cada técnica

**Role Prompting**

```text
Você é um Product Manager sênior com 10+ anos de experiência em times ágeis (Scrum/Kanban),
especialista em transformar relatos de bugs em User Stories claras, testáveis e prontas para
refinamento. Você domina BDD (Dado/Quando/Então) e conhece bem segurança (OWASP), performance,
integrações e UX.
```

**Chain of Thought interno.** O modelo segue os passos, mas devolve apenas o resultado:

```text
# PROCESSO DE RACIOCÍNIO (faça mentalmente, NÃO escreva na resposta)
1. Quem é afetado? ...  2. O que essa persona quer conseguir fazer? ...
3. Por que isso importa? ...  4. Quais comportamentos observáveis provam que o bug foi corrigido? ...
5. Quais dados concretos o relato traz? ...  6. Qual o nível de complexidade? ...
```

**Skeleton of Thought.** Um esqueleto por nível de complexidade:

```text
- SIMPLES: história + "Critérios de Aceitação:" (4–5 bullets), sem seções extras
- MÉDIO:   + bloco opcional (Critérios de Prevenção / Exemplo de Cálculo / Critérios Adicionais
           para <perfil> / Critérios Técnicos / Critérios de Acessibilidade)
           + seção de contexto (Contexto Técnico / Contexto de Segurança / Contexto do Bug)
- COMPLEXO: === USER STORY PRINCIPAL === / === CRITÉRIOS DE ACEITAÇÃO === (A, B, C… por problema)
            / === CRITÉRIOS TÉCNICOS === / === CONTEXTO DO BUG === / === TASKS TÉCNICAS SUGERIDAS ===
```

**Few-shot.** São 4 exemplos **sintéticos**, de domínios diferentes dos do dataset para evitar vazamento: blog (simples), agendamento com erro 500 (médio, com Contexto Técnico), link de redefinição de senha (médio, segurança) e busca de imóveis lenta e com contador divergente (médio, com metas mensuráveis). Exemplo:

```text
Entrada:
O botão "Salvar rascunho" do editor de posts não faz nada quando clicado.

Saída:
Como um autor escrevendo um post no blog, eu quero salvar meu texto como rascunho, para que eu
possa continuar a edição mais tarde sem perder o conteúdo.

Critérios de Aceitação:
- Dado que estou editando um post no editor
- Quando clico no botão "Salvar rascunho"
- Então o post deve ser salvo como rascunho
- E devo ver uma confirmação visual de que o rascunho foi salvo
- E o rascunho deve aparecer na minha lista de posts com status "Rascunho"
```

**System vs. User Prompt.** O `system_prompt` concentra papel, processo, esqueletos, regras e exemplos. O `user_prompt` contém só a tarefa e o relato delimitado. A variável `{bug_report}` aparece **apenas** no user prompt, o que corrige a duplicação da v1.

---

## Resultados Finais

### Evidências no LangSmith

- **Dataset de avaliação público** (15 exemplos, com todos os experimentos rodados contra ele):
  **https://smith.langchain.com/public/1000187d-a852-494a-8125-33ee315c81d1/d**
- **Prompt publicado no Hub:** `pizolatoguilherme/bug_to_user_story_v2` (público)

### Tracing detalhado (links públicos)

Traces completos de 3 exemplos da rodada final, um de cada nível de complexidade. Eles mostram a entrada, as mensagens system e user enviadas ao modelo, a resposta gerada, o modelo usado e os tempos:

| Exemplo | Nível | Trace público |
|---|---|---|
| #1 – Botão de adicionar ao carrinho não funciona | simples | https://smith.langchain.com/public/591ee238-3722-4ecc-9dc1-2e007dd5a278/r |
| #7 – Relatório de vendas demora mais de 2 minutos | médio | https://smith.langchain.com/public/0ce60bea-cc8e-42fb-9e58-077397673ae5/r |
| #14 – Sistema de relatórios gerenciais (N+1, MRR, cache, CSV) | complexo | https://smith.langchain.com/public/d22701b2-26ab-4ccb-8ea9-deb689e2adcf/r |

### Notas por exemplo (rodada final)

Notas gravadas como feedback no experimento final, com o F1 do mesmo exemplo na v1 para comparação. Os números de exemplo seguem a ordem de `datasets/bug_to_user_story.jsonl`.

| # | Nível | Bug | Help. | Corr. | F1 | Clar. | Prec. | F1 na v1 |
|---|---|---|---|---|---|---|---|---|
| 1 | simples | Botão de adicionar ao carrinho não funciona no produ… | 0.92 | 0.94 | 0.97 | 0.93 | 0.90 | 0.60 |
| 2 | simples | Campo de email aceita texto sem @, permitindo cadast… | 0.94 | 0.91 | 0.90 | 0.95 | 0.93 | 0.57 |
| 3 | simples | No iOS, ao girar o celular para landscape, o layout … | 0.91 | 0.95 | 0.97 | 0.89 | 0.93 | 0.92 |
| 4 | simples | Dashboard mostra contagem errada de usuários ativos.… | 0.85 | 0.86 | 0.90 | 0.87 | 0.83 | 0.50 |
| 5 | simples | Imagens de produtos não aparecem no Safari. No Chrom… | 0.88 | 0.88 | 0.89 | 0.89 | 0.87 | 0.62 |
| 6 | médio | Webhook de pagamento aprovado não está sendo chamado. | 0.78 | 0.77 | 0.85 | 0.85 | 0.70 | 0.81 |
| 7 | médio | Relatório de vendas demora mais de 2 minutos para ge… | 0.89 | 0.88 | 0.89 | 0.90 | 0.87 | 0.75 |
| 8 | médio | Endpoint /api/users/:id retorna dados de qualquer us… | 0.90 | 0.90 | 0.90 | 0.90 | 0.90 | 0.76 |
| 9 | médio | Pipeline de vendas calcula valor total errado quando… | 0.87 | 0.86 | 0.83 | 0.85 | 0.89 | 0.85 |
| 10 | médio | App Android trava ao carregar lista de notificações … | 0.86 | 0.84 | 0.84 | 0.89 | 0.84 | 0.79 |
| 11 | médio | Carrinho permite finalizar compra mesmo com produto … | 0.89 | 0.86 | 0.85 | 0.90 | 0.87 | 0.77 |
| 12 | médio | Modal de confirmação de exclusão aparece atrás do me… | 0.81 | 0.76 | 0.75 | 0.85 | 0.77 | 0.64 |
| 13 | complexo | Sistema de checkout com múltiplas falhas críticas. | 0.85 | 0.86 | 0.89 | 0.88 | 0.82 | 0.79 |
| 14 | complexo | Sistema de relatórios gerenciais com problemas sever… | 0.82 | 0.83 | 0.86 | 0.84 | 0.80 | 0.78 |
| 15 | complexo | App de produtividade offline-first com bugs críticos… | 0.85 | 0.83 | 0.85 | 0.89 | 0.82 | 0.75 |

O critério de aprovação vale para a **média** de cada métrica no experimento. Individualmente, dois exemplos ainda ficam abaixo de 0.8 em algumas notas. Segundo os comentários dos juízes:
- **#6 (webhook):** a resposta usou o cliente como persona, em vez de "o sistema". Também omitiu o retorno HTTP 200, o e-mail de confirmação e o log de auditoria esperados.
- **#12 (modal):** a resposta não trouxe o bloco de acessibilidade esperado (backdrop, foco no modal, fechar com ESC). Além disso, pediu o modal "acima do menu lateral", e não "acima de todos os elementos".

Esses são os próximos alvos se houver uma nova iteração.

Saída do `python src/evaluate.py` na versão final:

```text
==================================================
Prompt: pizolatoguilherme/bug_to_user_story_v2
==================================================

Métricas Derivadas:
  - Helpfulness: 0.87 ✓
  - Correctness: 0.86 ✓

Métricas Base:
  - F1-Score: 0.88 ✓
  - Clarity: 0.89 ✓
  - Precision: 0.85 ✓

--------------------------------------------------
📊 MÉDIA GERAL: 0.8683
--------------------------------------------------

✅ STATUS: APROVADO - Todas as métricas >= 0.8
```

### Jornada de otimização (iterações)

Cada linha é um experimento no LangSmith, e todos aparecem no dataset público acima. Entre as rodadas, analisei os comentários dos juízes nos exemplos com nota mais baixa.

| Rodada | Help. | Corr. | F1 | Clar. | Prec. | Média | O que mudou |
|---|---|---|---|---|---|---|---|
| v1 (base) | 0.84 | 0.78 | 0.73 | 0.86 | 0.82 | 0.806 | Prompt original: sem persona, sem formato, sem exemplos, `{bug_report}` duplicado |
| v2 – 1 | 0.85 | 0.83 | 0.84 | 0.88 | 0.82 | 0.842 | Primeira versão: persona, CoT interno, 3 esqueletos, regras, edge cases, 3 exemplos |
| v2 – 2 | 0.86 | 0.85 | 0.87 | 0.89 | 0.84 | 0.863 | Critérios descrevem a **regra geral** (não o sintoma); **metas mensuráveis melhores** que o valor atual; soluções técnicas consagradas para bugs complexos; 4º exemplo (performance) |
| v2 – 3 | 0.87 | 0.86 | 0.87 | 0.89 | 0.85 | 0.866 | Corte de **excesso de escopo** em bugs simples (sem seções extras, no máximo 1–2 expectativas padrão); personas mais óbvias |
| **v2 – 4** | **0.87** | **0.86** | **0.88** | **0.89** | **0.85** | **0.868** | Classificação de MÉDIO explícita (qualquer bloco "Detalhes/Cenário/Fluxo"); seções "Exemplo de Cálculo" e "Critérios de Prevenção" |

**O que os juízes apontaram e como foi corrigido:**

1. **Sintoma em vez de regra (rodada 1).** No bug "Dashboard mostra 50 mas há 42", a resposta dizia "a contagem deve exibir 42", e a referência espera "considerar apenas usuários com status ativo, em tempo real". Correção: a regra 5 pede que os critérios descrevam o comportamento correto geral.
2. **Meta igual ao valor quebrado (rodada 1).** No relatório que demora mais de 2 minutos, a resposta exigia "não ultrapassar 2 minutos", e a referência espera "< 30 segundos". Correção: a regra 6 pede metas melhores que o atual (SLA, CPU < 70%, cache ≤ 5 min…).
3. **Excesso de escopo em bugs simples (rodada 2).** A regra de "expectativas padrão" fez o modelo inventar fallbacks e incluir seção de contexto em bugs de uma frase, o que derrubou a Precision. Correção: limite de 1–2 expectativas e bugs simples sem seções extras.
4. **Bugs médios tratados como simples (rodada 3).** "Fluxo do bug" e "Cenário" não eram reconhecidos como detalhes, e a resposta saía sem o "Exemplo de Cálculo" e os "Critérios de Prevenção" esperados. Correção: critério de classificação explícito e seções opcionais nomeadas no esqueleto MÉDIO.

### Comparação v1 × v2: o que mudou e por quê

| Aspecto | v1 | v2 | Por quê |
|---|---|---|---|
| Persona | "assistente que ajuda…" | Product Manager sênior especialista em BDD, OWASP, performance e UX | Contexto e vocabulário de backlog |
| Uso de system/user | `{bug_report}` no system **e** no user (duplicado) | System com instruções; user só com o relato delimitado por `"""` | Separação de responsabilidades, sem ruído duplicado |
| Formato de saída | Não definido | "Como um…, eu quero…, para que…" + Dado/Quando/Então + esqueletos por complexidade | Os juízes comparam com uma referência estruturada |
| Raciocínio | Nenhum | CoT em 6 passos, feito internamente | Melhor análise sem texto extra na resposta |
| Exemplos | Nenhum | 4 exemplos sintéticos (few-shot) | Fixam formato, tamanho e tom |
| Regras | Nenhuma | 13 regras (sem preâmbulo, preservar dados, regra geral, metas mensuráveis, proporcionalidade, persona…) | Cada regra veio de um problema observado nas iterações |
| Edge cases | Nenhum | Relato vago, logs, múltiplos problemas, segurança, perda de dados, feature request, relato vazio | Robustez fora do caminho feliz |
| Metadados | version e tags | + `techniques_applied`, `techniques_details`, descrição | Rastreabilidade das técnicas no Hub e nos testes |

O maior ganho foi em **F1-Score** (+0.15) e **Correctness** (+0.08). A v1 até produzia histórias legíveis (Clarity 0.86), mas sem formato definido. Ela errava o tamanho e a estrutura esperados, sobretudo nos **bugs simples**: 4 dos 5 exemplos com F1 abaixo de 0.70 eram simples (o mínimo foi 0.50, no bug do dashboard). Nos médios e complexos, faltavam critérios e contexto técnico (recall baixo). Na v2 final nenhum exemplo fica abaixo de 0.75 de F1, e o F1 médio subiu de 0.73 para 0.88.

---

## Como Executar

### Pré-requisitos

- Python **3.10+** (testado com 3.14)
- Conta no [LangSmith](https://smith.langchain.com) com **API Key** (Settings → API Keys → Personal Access Token)
- **Handle público do LangSmith Hub**: em Prompts, abra qualquer prompt → **⋯** → **Make Public** → escolha o handle (é definitivo)
- API Key da **OpenAI** (com créditos) **ou** do **Google Gemini**

### 1. Instalação

```bash
git clone https://github.com/pizolatoguilherme/mba-ia-pull-evaluation-prompt.git
cd mba-ia-pull-evaluation-prompt

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> Em Debian/Ubuntu sem o pacote `python3-venv`, use `python3 -m venv --without-pip venv` e instale o pip com `curl -sSL https://bootstrap.pypa.io/get-pip.py | venv/bin/python`.

### 2. Configuração

```bash
cp .env.example .env
```

Preencha o `.env`:

| Variável | Valor |
|---|---|
| `LANGSMITH_API_KEY` | sua chave `lsv2_pt_...` |
| `LANGSMITH_PROJECT` | `mba-ia-pull-evaluation-prompt` (o dataset vira `<projeto>-eval`) |
| `USERNAME_LANGSMITH_HUB` | seu handle público do Hub |
| `LLM_PROVIDER` | `openai` ou `google` |
| `OPENAI_API_KEY` / `GOOGLE_API_KEY` | chave do provider escolhido |
| `LLM_MODEL` | modelo que gera as respostas (usado aqui: `gpt-5.4-mini`) |
| `EVAL_MODEL` | modelo avaliador (usado aqui: `gpt-5.4`) |

> Os modelos precisam aceitar `temperature=0`. Na conta usada, `gpt-5`, `gpt-5.5`, `gpt-6*` e `o3` retornaram erro 400 com esse valor, enquanto `gpt-4.1`, `gpt-4o`, `gpt-5.1`, `gpt-5.2` e `gpt-5.4*` funcionaram.

### 3. Fases do projeto

Execute todos os comandos a partir da **raiz do repositório**:

```bash
# Fase 1 – Pull do prompt original (gera prompts/bug_to_user_story_v1.yml)
python src/pull_prompts.py

# Fase 2 – Otimização: edite prompts/bug_to_user_story_v2.yml
#          e valide a estrutura com os testes
pytest tests/test_prompts.py -v

# Fase 3 – Push público da v2 para <seu_handle>/bug_to_user_story_v2
python src/push_prompts.py

# Fase 4 – Avaliação (cria um experimento no LangSmith e imprime o link)
python src/evaluate.py
```

Para iterar, repita: editar o YAML → `pytest` → `push_prompts.py` → `evaluate.py`.

Opcional: para gerar a linha de base de comparação, avalie o prompt original (v1) com as mesmas métricas:

```bash
python src/evaluate_baseline.py                      # avalia leonanluppi/bug_to_user_story_v1
python src/evaluate_baseline.py <owner/prompt>       # ou qualquer outro prompt do Hub
```

Para gerar o link público do dataset (rode **uma vez**, porque o link muda a cada novo compartilhamento):

```bash
python -c "from dotenv import load_dotenv; load_dotenv('.env'); import os; from langsmith import Client; print(Client().share_dataset(dataset_name=os.environ['LANGSMITH_PROJECT'] + '-eval')['url'])"
```

### O que cada script faz

| Arquivo | Responsabilidade |
|---|---|
| `src/pull_prompts.py` | Conecta ao LangSmith, faz `pull_prompt("leonanluppi/bug_to_user_story_v1", dangerously_pull_public_prompt=True)`, separa as mensagens system e user do `ChatPromptTemplate` e salva o YAML com `save_yaml`. |
| `src/push_prompts.py` | Lê o YAML, valida (campos obrigatórios, ≥ 2 técnicas, `{bug_report}` só no user prompt, única variável do template, sem `[TODO]`), monta o `ChatPromptTemplate` e faz `push_prompt(..., is_public=True)` com descrição e tags (`technique:*`). |
| `tests/test_prompts.py` | 6 testes obrigatórios (system prompt, persona, formato, few-shot, sem TODO, ≥ 2 técnicas) + 3 extras (variável só no user prompt, template com uma variável, `validate_prompt_structure`). |
| `src/evaluate_baseline.py` | Script **adicional**: avalia o prompt v1 (ou outro do Hub) com as mesmas funções e métricas do `evaluate.py`, para a comparação v1 × v2. |
| `src/evaluate.py`, `src/metrics.py`, `src/utils.py` | Fornecidos pelo desafio (não alterados). |

### Testes

```bash
pytest tests/test_prompts.py -v
```

```text
tests/test_prompts.py::TestPrompts::test_prompt_has_system_prompt PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_role_definition PASSED
tests/test_prompts.py::TestPrompts::test_prompt_mentions_format PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_few_shot_examples PASSED
tests/test_prompts.py::TestPrompts::test_prompt_no_todos PASSED
tests/test_prompts.py::TestPrompts::test_minimum_techniques PASSED
tests/test_prompts.py::TestPrompts::test_bug_report_variable_only_in_user_prompt PASSED
tests/test_prompts.py::TestPrompts::test_template_has_single_input_variable PASSED
tests/test_prompts.py::TestPrompts::test_validate_prompt_structure PASSED
```

---

## Estrutura do projeto

```
├── .env.example
├── requirements.txt
├── README.md
├── docs/images/                     # screenshots das evidências
├── prompts/
│   ├── bug_to_user_story_v1.yml     # prompt original (gerado pelo pull)
│   └── bug_to_user_story_v2.yml     # prompt otimizado
├── datasets/
│   └── bug_to_user_story.jsonl      # 15 bugs (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py              # implementado
│   ├── push_prompts.py              # implementado
│   ├── evaluate.py                  # fornecido
│   ├── evaluate_baseline.py         # adicional (linha de base v1)
│   ├── metrics.py                   # fornecido
│   └── utils.py                     # fornecido
└── tests/
    └── test_prompts.py              # implementado
```
