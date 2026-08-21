# Career Memory

**Nunca esqueça o trabalho que você fez.**

Career Memory é uma agent skill que mantém um registro persistente e factual do
seu trabalho profissional — e transforma esse mesmo registro no que você
precisar escrever depois: uma daily, um brag document, uma avaliação de
desempenho, um caso de promoção, bullets de currículo, histórias de entrevista.

Você menciona o que fez, com suas próprias palavras, enquanto já está
trabalhando:

> "Finalmente corrigi aquela race condition no pagamento. A PR é a #1234."

Isso vira uma evidência durável:

```markdown
---
id: 2026-08-20-corrigida-race-condition-no-fluxo-pagamento
date: 2026-08-20
type: problem-solving
project: pagamentos
status: confirmed
tags: [debugging, confiabilidade]
evidence:
  - type: github_pr
    reference: "#1234"
---

# Corrigida a race condition no fluxo de pagamento

Identifiquei e corrigi uma race condition no processamento de pagamentos.

## Impact

Not documented.
```

Seis meses depois, essa entrada escreve parte da sua avaliação. Você registrou
uma única vez.

```text
Trabalho → Evidência → Memória → Narrativa
```

## Por quê

Seu trabalho fica espalhado por PRs, threads de Slack, tickets, reuniões e
memória. Na época da avaliação, a maior parte já se perdeu. A solução de sempre
— "mantenha um brag document" — falha porque exige que você pare e escreva, e
ninguém faz isso de forma consistente.

Career Memory captura durante a conversa que você já está tendo com seu agente
de código, e devolve isso quando você precisa.

## A regra que torna o registro utilizável

**Ele nunca inventa nada.** Nenhuma métrica que você não disse, nenhum resultado
que você não relatou, nenhum feedback que você não recebeu. Quando algo é
desconhecido, o registro diz `Impact: not documented` em vez de chutar.

Essa restrição é o produto. Um registro de carreira que infla é um registro que
você não consegue defender numa conversa de avaliação — por isso este não infla.

## Instalação

### Claude Code (recomendado)

```bash
/plugin marketplace add emerlopes/career-memory
```

```bash
/plugin install career-memory@emerlopes-plugins
```

### Qualquer agente que leia `SKILL.md`

Copie o diretório da skill para onde seu agente procura skills:

```bash
git clone https://github.com/emerlopes/career-memory.git
cp -r career-memory/skills/career-memory ~/.claude/skills/career-memory
```

A skill é Markdown puro mais um único script Python sem dependências — nada
aqui é específico do Claude, exceto o caminho de instalação.

## Primeiro uso

```text
/career-memory:career-init
```

Isso cria seu store (por padrão em `~/career-memory`) e ajuda a preencher um
perfil curto. Depois é só trabalhar — e mencionar o que você fez.

Você pode fixar o local onde preferir:

```bash
export CAREER_MEMORY_HOME="$HOME/Documents/career-memory"
```

## Como usar

Na maior parte do tempo você não precisa invocar nada. Diga o que aconteceu e
será capturado:

> "Subi o dashboard novo hoje, o cliente já está usando."
>
> "Passei a manhã ajudando o João a debugar o fluxo de autenticação."
>
> "Meu gestor disse que a reunião de planejamento foi boa porque eu conduzi."

Depois, peça o que precisar:

| Você pede                                      | Você recebe                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------------- |
| "prepara minha daily"                          | Uma daily de 30–90 segundos, dividida em Ontem / Hoje / Impedimentos      |
| "o que eu fiz esse trimestre?"                 | Suas entradas reais, com datas e evidências                               |
| "gera meu brag document"                       | Destaques agrupados por tema, com evidências e o que não está documentado |
| "monta minha avaliação de desempenho"          | Avaliação estruturada, com cada afirmação rastreável                      |
| "que evidências eu tenho para Staff Engineer?" | Pontos fortes, padrões e as lacunas específicas                           |
| "transforma isso em bullets de currículo"      | Bullets de uma linha, só com números reais                                |
| "me prepara para entrevista comportamental"    | Histórias STAR construídas a partir de eventos reais                      |

Há slash commands para as mesmas coisas: `/career-memory:career-daily`,
`career-add`, `career-brag`, `career-review`, `career-promotion`,
`career-resume`, `career-interview`, `career-search`, `career-github`.

## GitHub

Seu trabalho já está registrado em algum lugar: PRs, issues, reviews e commits.
Career Memory lê essa atividade (somente leitura) e transforma em evidência —
sempre como **candidata**, nunca como registro confirmado sem você dizer.

```text
/career-memory:career-github last-month
```

> "o que eu mergeei esse mês?" · "importa minhas PRs da semana" ·
> "linka a PR #1234 na entrada de ontem"

```bash
python3 $CM github check                       # verifica o acesso e a conta
python3 $CM github discover --window 7d        # mostra a atividade e o que já está registrado
python3 $CM github import --window 7d          # grava as novidades em candidates/
python3 $CM github link <id> <url-da-pr>       # anexa uma PR a uma entrada existente
```

Precisa da CLI do GitHub (`gh auth login`) ou de um `GITHUB_TOKEN` de leitura.
Nada é enviado para lugar nenhum: a descoberta só lê o GitHub e escreve nos seus
arquivos locais.

O que a descoberta faz e o que ela não faz:

- PRs, issues e reviews entram por padrão; commits só quando você pede
  (`--kinds commit`) — uma semana de commits não é uma semana de evidências.
- Uma PR mergeada vira uma entrada `delivery`; uma review vira `collaboration`;
  uma issue que você abriu vira `problem-solving`. São padrões mecânicos, para
  você corrigir antes de confirmar.
- Se a evidência já está registrada, ela é ignorada — reimportar é seguro.
- Se o sinal se parece com algo que você já contou, ele sugere **linkar** a PR na
  entrada existente em vez de duplicar.
- O título da PR é a evidência, não o impacto. `Impact: not documented` continua
  lá até você dizer o que aquilo mudou.

## Seus dados

Markdown puro, num diretório que é seu:

```text
~/career-memory/
├── profile.md          seu cargo, foco e objetivos
├── entries/            evidências confirmadas, um arquivo por evento
├── candidates/         possíveis evidências aguardando sua confirmação (inclusive as do GitHub)
├── feedback/           feedbacks recebidos
├── projects/           contexto por projeto
└── outputs/            documentos gerados
```

Local por padrão. Sem banco de dados, sem conta, sem servidor, nada é enviado
para lugar nenhum. Legível e editável sem nenhum agente. Coloque num repositório
git privado se quiser histórico:

```bash
cd ~/career-memory && git init && git add . && git commit -m "career memory"
```

## CLI

A skill usa uma CLI pequena para que ids, front matter e busca sejam exatos em
vez de improvisados. Você também pode usá-la diretamente:

```bash
CM=skills/career-memory/scripts/career_memory.py

python3 $CM init
python3 $CM add "Liderei a migração de 4 serviços" --type leadership --project plataforma
python3 $CM update 2026-08-20-liderei-migracao-4-servicos --add-evidence 'github_pr:#88'
python3 $CM list --window last-quarter
python3 $CM search "confiabilidade" --format full
python3 $CM stats --window 6m
python3 $CM validate

python3 $CM github discover --window last-month
python3 $CM github import --window last-month --dry-run
python3 $CM github link 2026-08-20-liderei-migracao-4-servicos acme/plataforma#88
```

Python 3.9+, apenas biblioteca padrão. PyYAML é usado se estiver disponível, mas
não é necessário.

## Roadmap

- **v0.1** — Armazenamento em Markdown, captura, candidatos, busca, brag documents e modo daily
- **v0.2** — GitHub: descobrir PRs, issues, commits e reviews como evidências candidatas _(atual)_
- **v0.3** — Memória proativa: resumos semanais/mensais, detecção de evidências faltantes
- **v0.4** — Mais interfaces: Telegram, CLI independente, outros agentes
- **v0.5** — Inteligência de carreira: evolução de competências, análise de lacunas para promoção ao longo do tempo

Especificação completa: [`docs/SPEC.md`](docs/SPEC.md).

## Contribuindo

Issues e pull requests são bem-vindos. O contrato de comportamento vive em
[`skills/career-memory/SKILL.md`](skills/career-memory/SKILL.md); qualquer
mudança no que o agente registra ou afirma deve ser argumentada lá primeiro.

Rode a suíte de testes antes de abrir um PR:

```bash
./tests/test_cli.sh
```

## Licença

MIT — veja [LICENSE](LICENSE).
