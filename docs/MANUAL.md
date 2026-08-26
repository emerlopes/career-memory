# Manual de uso — Career Memory

Este é o manual completo da skill: o que cada funcionalidade faz, como pedir em
linguagem natural, qual slash command corresponde a ela, qual comando de CLI está
por baixo e quais são as armadilhas de cada uma.

Se você só quer começar, leia [Antes de tudo](#antes-de-tudo) e
[Captura](#1-captura--registrar-o-que-você-fez). O resto é referência: consulte
quando precisar.

---

## Sumário

- [Conceitos que valem entender primeiro](#conceitos-que-valem-entender-primeiro)
- [Antes de tudo](#antes-de-tudo)
  - [Instalação](#instalação)
  - [Onde a memória fica](#onde-a-memória-fica)
  - [Três formas de usar](#três-formas-de-usar)
- [Funcionalidades](#funcionalidades)
  - [0. Setup e configuração](#0-setup-e-configuração)
  - [1. Captura — registrar o que você fez](#1-captura--registrar-o-que-você-fez)
  - [2. Busca e recuperação](#2-busca-e-recuperação)
  - [3. Daily / standup](#3-daily--standup)
  - [4. GitHub como evidência](#4-github-como-evidência)
  - [5. Resumo semanal](#5-resumo-semanal)
  - [6. Resumo mensal](#6-resumo-mensal)
  - [7. Checkup — o que está pendente](#7-checkup--o-que-está-pendente)
  - [8. Gaps — o que o registro ainda não prova](#8-gaps--o-que-o-registro-ainda-não-prova)
  - [9. Trends — como o registro evoluiu](#9-trends--como-o-registro-evoluiu)
  - [10. Promotion — cobertura para um nível-alvo](#10-promotion--cobertura-para-um-nível-alvo)
  - [11. Graph — o que aparece junto](#11-graph--o-que-aparece-junto)
  - [12. Brag document](#12-brag-document)
  - [13. Avaliação de desempenho](#13-avaliação-de-desempenho)
  - [14. Caso de promoção](#14-caso-de-promoção)
  - [15. Bullets de currículo](#15-bullets-de-currículo)
  - [16. Histórias de entrevista (STAR)](#16-histórias-de-entrevista-star)
  - [17. Manutenção do store](#17-manutenção-do-store)
- [Referência](#referência)
  - [Janelas de tempo](#janelas-de-tempo)
  - [Schema de uma entrada](#schema-de-uma-entrada)
  - [Referência completa da CLI](#referência-completa-da-cli)
  - [Estrutura do store](#estrutura-do-store)
- [Receitas](#receitas)
- [Solução de problemas](#solução-de-problemas)
- [O que a skill nunca faz](#o-que-a-skill-nunca-faz)

---

## Conceitos que valem entender primeiro

Cinco palavras aparecem o tempo todo neste manual. Entender as cinco resolve 90%
das dúvidas sobre o comportamento da skill.

| Conceito      | O que é                                                                                                                                                                     |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Entrada**   | Um arquivo Markdown descrevendo **um** evento profissional: o que aconteceu, quando, em qual projeto, com qual evidência. É a unidade da memória.                           |
| **Candidato** | Uma entrada que a skill escreveu mas **você ainda não confirmou**. Tudo que vem do GitHub nasce candidato; sinais ambíguos também. Fica em `candidates/` até você promover. |
| **Evidência** | Uma referência verificável: `PR #1234`, um dashboard, um feedback, uma ata. "Uma PR" não é evidência; "PR #1234" é.                                                         |
| **Impacto**   | O que aquilo mudou para alguém. Quando você não disse, fica literalmente `Impact: not documented` — nunca é chutado.                                                        |
| **Store**     | O diretório de Markdown com tudo isso. É seu, é local, é legível sem nenhum agente.                                                                                         |

A regra que sustenta todas: **a skill nunca inventa**. Nenhuma métrica, nenhum
resultado, nenhuma data, nenhum feedback que você não tenha dito. Interpretação é
permitida (`skills:`, seções "Interpretation"), mas fica marcada como
interpretação — nunca vira fato.

---

## Antes de tudo

### Instalação

**Claude Code (recomendado)**

```bash
/plugin marketplace add emerlopes/career-memory
```

```bash
/plugin install career-memory@emerlopes-plugins
```

**Qualquer agente que leia `SKILL.md`**

```bash
git clone https://github.com/emerlopes/career-memory.git
cp -r career-memory/skills/career-memory ~/.claude/skills/career-memory
```

Requisitos: Python 3.9+ (só biblioteca padrão). O `gh` CLI ou um `GITHUB_TOKEN`
só são necessários para a parte de GitHub — todo o resto funciona sem.

### Onde a memória fica

O store é resolvido nesta ordem:

1. `$CAREER_MEMORY_HOME`
2. `./career-memory` no projeto atual, se existir
3. `~/career-memory`

Para fixar um lugar:

```bash
export CAREER_MEMORY_HOME="$HOME/Documents/career-memory"
```

Para descobrir qual está valendo agora:

```bash
python3 $CM where
```

Em todos os exemplos deste manual, `$CM` é o caminho do script:

```bash
CM=~/.claude/skills/career-memory/scripts/career_memory.py
```

(No Claude Code com o plugin instalado, o caminho fica sob `$CLAUDE_PLUGIN_ROOT`.
Você não precisa disso para o uso normal — a skill resolve sozinha.)

### Três formas de usar

Toda funcionalidade tem três portas de entrada. Escolha a que couber no momento:

1. **Conversa** — você menciona o que fez, ou pede o que precisa, em linguagem
   natural. É o modo principal e o de menor atrito.
2. **Slash command** — `/career-memory:career-daily`, `/career-memory:career-brag`,
   etc. Útil quando você quer exatamente aquilo, sem ambiguidade.
3. **CLI** — `python3 $CM ...`. Útil para scripts, para inspecionar o store, e
   para quando você quer o dado bruto em vez do texto redigido.

As três escrevem nos mesmos arquivos. Não existe estado escondido.

---

## Funcionalidades

### 0. Setup e configuração

#### `career-init` — preparar o store

**Slash command**

```text
/career-memory:career-init
/career-memory:career-init ~/Documents/career-memory
```

**O que acontece:** cria o store (diretórios, `profile.md`, `README.md`,
`config.json`), mostra o layout resultante e conduz **uma conversa curta** para
preencher o perfil: cargo, foco atual, objetivos. Não é formulário — são três
perguntas.

**CLI equivalente**

```bash
python3 $CM init      # cria a estrutura
python3 $CM status    # cria o que faltar e relata o estado
```

**Por que o perfil importa:** um review ou caso de promoção escrito sem saber seu
nível e seu alvo sai genérico, porque é. Por isso o perfil tem um "portão"
configurável (veja `profile_gate` abaixo).

---

#### `status` — o bootstrap de toda interação

Este comando não é uma funcionalidade que você "usa": é o que a skill roda no
início de qualquer interação, silenciosamente.

```bash
python3 $CM status
```

```text
store: /Users/voce/career-memory
settings: language=auto, documents_language=same, profile_gate=documents
profile: incomplete — missing Role, Focus, Current Goals
blocked: documents
```

Ele **cria o que estiver faltando** e é idempotente. Consequência prática: não
existe estado "não inicializado" para tratar, e a skill nunca precisa pedir
permissão para montar a estrutura.

`--format json` para saída programática.

O campo `blocked` diz o que o perfil incompleto está segurando:

| `blocked`    | Significado                                                                                            |
| ------------ | ------------------------------------------------------------------------------------------------------ |
| `nothing`    | Tudo liberado.                                                                                         |
| `documents`  | Captura, busca e daily funcionam. Brag, review, promoção, currículo e entrevista pedem o perfil antes. |
| `everything` | Portão duro: nada acontece antes do perfil.                                                            |

---

#### `career-config` — ajustar comportamento

**Slash command**

```text
/career-memory:career-config
/career-memory:career-config language=pt
```

Aceita fraseado natural: _"responde sempre em português"_ vira `language=pt`;
_"documentos em inglês"_ vira `documents_language=en`; _"não me bloqueie"_ vira
`profile_gate=remind`.

**CLI**

```bash
python3 $CM config                                        # mostra valores e opções
python3 $CM config --get language
python3 $CM config --set language=pt --set documents_language=en
```

**As três configurações**

| Configuração         | Valores                        | Padrão      | O que faz                                                                                |
| -------------------- | ------------------------------ | ----------- | ---------------------------------------------------------------------------------------- |
| `language`           | `auto` · `pt` · `en`           | `auto`      | Idioma das respostas e do corpo das entradas. `auto` segue o idioma da sua mensagem.     |
| `documents_language` | `same` · `pt` · `en` · `ask`   | `same`      | Idioma dos documentos gerados. `same` segue `language`; `ask` pergunta a cada documento. |
| `profile_gate`       | `documents` · `all` · `remind` | `documents` | O que um `profile.md` incompleto bloqueia. `remind` não bloqueia nada, só lembra.        |

O split entre `language` e `documents_language` existe por um motivo concreto:
muita gente fala português com o time e entrega a avaliação de desempenho em
inglês.

**O idioma nunca afeta o schema.** `type`, `status`, tipos de evidência e as
chaves do front matter continuam em inglês em qualquer idioma — o store funciona
igual, e um documento gerado em inglês lê as mesmas entradas escritas em
português.

As configurações vivem em `config.json` **dentro do store**, então sobrevivem
entre sessões e podem ir para o git junto com o resto.

---

### 1. Captura — registrar o que você fez

Esta é a funcionalidade central. As outras 16 só existem porque esta funcionou.

**Em conversa (o modo principal)**

Você não precisa invocar nada. Diga o que aconteceu, no meio do que você já
estava fazendo:

> "Finalmente corrigi aquela race condition no pagamento. A PR é a #1234."
>
> "Subi o dashboard novo hoje, o cliente já está usando."
>
> "Passei a manhã ajudando o João a debugar o fluxo de autenticação."
>
> "Meu gestor disse que a reunião de planejamento foi boa porque eu conduzi."

**Slash command**

```text
/career-memory:career-add corrigi a race condition do pagamento, PR #1234
```

**O que a skill faz, nessa ordem**

1. **Decide se é relevante para carreira.** "Almocei" não é. "Almocei com o
   cliente e descobri que os requisitos mudaram" é. Trabalho rotineiro mencionado
   de passagem normalmente não é — capturar demais dilui o registro.
2. **Extrai só o que você disse**: data, o que aconteceu, projeto, pessoas,
   resultado, evidência, contexto.
3. **Classifica**: tipo, projeto, tags e as competências que o evento
   plausivelmente demonstra (isso é interpretação, e fica marcado como tal).
4. **Faz no máximo uma pergunta**, e só quando a resposta muda o registro de
   verdade — _"esse fix segurou em produção?"_ vale; cinco perguntas transformam
   captura em formulário e você para de contar as coisas.
5. **Escreve** a entrada.
6. **Confirma em três ou quatro linhas**: o que foi registrado, o tipo, a
   evidência, e se o impacto está documentado.

Se você está no meio de uma tarefa e mencionou algo de passagem, a captura não
descarrila a tarefa: uma linha de confirmação e segue.

**Quando o sinal é fraco**, a skill pergunta em vez de decidir sozinha:

> Possível evidência de carreira: você desbloqueou o João no problema de auth.
> Registro?

**CLI**

```bash
python3 $CM add "Corrigida a race condition no fluxo de pagamento" \
  --type problem-solving \
  --project pagamentos \
  --date 2026-08-20 \
  --tags debugging,confiabilidade \
  --skills "resolução de problemas técnicos" \
  --people João \
  --evidence 'github_pr:#1234' \
  --impact "Parou as falhas intermitentes de captura" \
  --context "Intermitente e difícil de reproduzir"
```

Flags úteis:

| Flag                  | Para quê                                                       |
| --------------------- | -------------------------------------------------------------- |
| `--date`              | `YYYY-MM-DD`, `today`, `yesterday`, ou `3d` (três dias atrás). |
| `--status candidate`  | Registrar como candidato, quando o evento é ambíguo.           |
| `--impact-confidence` | `factual` (padrão), `inferred` ou `uncertain`.                 |
| `--body -`            | Ler o corpo Markdown do stdin.                                 |
| `--source`            | Onde você contou (`slack`, `meeting`…).                        |
| `--force`             | Pular a checagem de duplicata. Use com parcimônia.             |

**A checagem de duplicata**

`add` **se recusa a escrever** quando encontra uma entrada recente parecida, e
imprime as candidatas a duplicata. Isso é o comportamento correto, não um erro.
Na maioria das vezes o movimento certo é `update` na entrada existente — não
`add --force`.

**Emendar uma entrada depois**

```bash
python3 $CM update 2026-08-20-corrigida-race-condition \
  --add-evidence 'github_pr:#1234' \
  --set-impact "Alertas de pagamento caíram de 12/semana para 0" \
  --add-tag confiabilidade \
  --add-skill debugging \
  --add-person Maria \
  --append "Detalhe adicional para o corpo"
```

**Confirmar ou descartar um candidato**

```bash
python3 $CM promote <id>    # candidato -> entrada confirmada
python3 $CM dismiss <id>    # apaga o candidato
```

**Armadilhas**

- Impacto que você não mediu deve continuar `not documented`. Essa linha é mais
  valiosa que um chute: ela diz exatamente o que ir buscar.
- Não promova coisas pequenas. "Participei da reunião de planejamento" é uma
  entrada perfeitamente boa. "Demonstrou liderança excepcional ao comparecer a
  uma reunião" destrói a credibilidade de todas as conquistas reais ao lado.

---

### 2. Busca e recuperação

**Em conversa**

> "o que eu fiz esse trimestre?" · "mostra meu trabalho em pagamentos" ·
> "onde eu demonstrei liderança?"

**Slash command**

```text
/career-memory:career-search confiabilidade
```

**CLI**

```bash
python3 $CM list --window last-quarter
python3 $CM list --window 7d --format full
python3 $CM search "confiabilidade" --window last-quarter
python3 $CM search "migração" --project plataforma --type leadership
python3 $CM show 2026-08-20-corrigida-race-condition
```

**Filtros disponíveis** (valem para `list`, `search` e `stats`)

| Filtro                                         | Exemplo                                                                                                       |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `--window`                                     | `7d`, `this-week`, `last-quarter`, `this-year` — veja [Janelas de tempo](#janelas-de-tempo)                   |
| `--from` / `--to`                              | intervalo exato, `YYYY-MM-DD`                                                                                 |
| `--type`                                       | `achievement`, `delivery`, `impact`, `problem-solving`, `feedback`, `learning`, `leadership`, `collaboration` |
| `--project` · `--tag` · `--skill` · `--person` | recorte estrutural                                                                                            |
| `--status`                                     | `confirmed`, `candidate`, `dismissed`                                                                         |
| `--include-candidates`                         | inclui candidatos no resultado                                                                                |
| `--limit`                                      | corta a lista                                                                                                 |
| `--format`                                     | `table` (padrão), `json`, `paths`, `full`                                                                     |

`--format full` traz o texto inteiro das entradas: é o que usar quando a
intenção é **sintetizar**, não listar.

**Temas recorrentes**

```bash
python3 $CM stats --window 6m
```

**Armadilha:** resultado vazio é informação real sobre o seu registro, não um
convite para preencher de memória. Se nada casa, a resposta certa é "nada
registrado nesse período" — e talvez um `github discover` para o mesmo intervalo.

---

### 3. Daily / standup

**Em conversa**

> "prepara minha daily" · "o que eu falo hoje?" · "standup"

**Slash command**

```text
/career-memory:career-daily
/career-memory:career-daily hoje vou pegar o bug do checkout
```

**O que sai:** algo que você consegue falar em voz alta em 30–90 segundos.

```text
Ontem:
- ...

Hoje:
- ...

Impedimentos:
- ...
```

**CLI por baixo**

```bash
python3 $CM list --window 3d --format full
```

**Regras que importam aqui**

- **Trabalho planejado nunca vira trabalho concluído.** "Vou migrar o banco" não
  pode virar "Migrei o banco" — você fala isso para o time, e ser pego
  exagerando custa mais caro do que qualquer update vago já custou.
- O que você **planeja** para hoje normalmente não está no store. A skill
  pergunta — uma pergunta curta — quando as entradas não deixam óbvio.
- Sem impedimentos? "Sem impedimentos". Não se inventa risco.

**Bônus:** a daily é um bom momento de captura. Quando você menciona ter
terminado algo que ainda não está no store, a skill oferece registrar.

---

### 4. GitHub como evidência

Seu trabalho já está registrado em algum lugar: PRs, issues, reviews e commits.
A skill lê essa atividade (**somente leitura**) e transforma em evidência —
sempre **candidata**, nunca confirmada sem você dizer.

O desenho é esse split: **o GitHub fornece a referência, você fornece o
significado.**

**Em conversa**

> "o que eu mergeei esse mês?" · "importa minhas PRs da semana" ·
> "linka a PR #1234 na entrada de ontem"

**Slash command**

```text
/career-memory:career-github last-month
/career-memory:career-github acme/pagamentos
```

#### 4.1 Verificar acesso

```bash
python3 $CM github check
```

Mostra a conta usada e o backend encontrado:

- **`gh`** — o GitHub CLI, com o que o `gh auth login` já configurou. É o
  preferido: nenhum token encosta no store.
- **`api`** — `https://api.github.com` com `$GITHUB_TOKEN` ou `$GH_TOKEN`.
  `$GITHUB_API_URL` aponta para um GitHub Enterprise.

**Exit code 3** significa "sem acesso ao GitHub", não "nada encontrado". Nada
mais na skill depende disso.

#### 4.2 Descobrir

```bash
python3 $CM github discover --window 7d
python3 $CM github discover --window last-month --repo acme/pagamentos
python3 $CM github discover --window this-quarter --org acme --new-only
```

Cada linha vem marcada como `new` ou `saved` — `saved` quer dizer que aquela
referência já está anexada a alguma entrada, casada tanto se foi registrada como
URL quanto como `owner/repo#123`.

| Flag               | Padrão            | Notas                                                               |
| ------------------ | ----------------- | ------------------------------------------------------------------- |
| `--window`         | `30d`             | Mesmo vocabulário de `list` / `search`                              |
| `--from` / `--to`  | —                 | Intervalo exato                                                     |
| `--kinds`          | `pr,issue,review` | Adicione `commit` explicitamente                                    |
| `--repo` · `--org` | —                 | Recorte                                                             |
| `--visibility`     | `all`             | `public` ou `private`                                               |
| `--by`             | `created`         | Qual data a janela filtra: `created`, `updated`, `merged`, `closed` |
| `--limit`          | `50`              | Por tipo                                                            |
| `--new-only`       | —                 | Esconde o que já está registrado                                    |
| `--user`           | conta autenticada | Outro login                                                         |
| `--backend`        | `auto`            | `gh` ou `api`                                                       |
| `--format`         | `table`           | `json`, `refs`                                                      |

#### 4.3 Importar como candidatos

```bash
python3 $CM github import --window 7d
python3 $CM github import --window last-month --dry-run
python3 $CM github import --window 7d --project plataforma --with-body
```

`import` **só escreve candidatos** — não consegue escrever outra coisa. A
confirmação é sua, um `promote` de cada vez.

Os padrões de classificação são mecânicos, feitos para você corrigir antes de
confirmar:

| Sinal do GitHub      | Vira               |
| -------------------- | ------------------ |
| PR mergeada          | entrada `delivery` |
| Review que você fez  | `collaboration`    |
| Issue que você abriu | `problem-solving`  |
| Commit (opt-in)      | `delivery`         |

Reimportar é seguro: evidência já registrada é ignorada. E se o sinal se parece
com algo que você já contou, a skill sugere **linkar** em vez de duplicar.

#### 4.4 Linkar a uma entrada existente

```bash
python3 $CM github link 2026-08-20-liderei-migracao acme/plataforma#88
python3 $CM github link <id> https://github.com/acme/plataforma/pull/88
python3 $CM github link <id> acme/plataforma@a1b2c3d
```

`link` é melhor que `--evidence` para referências do GitHub: resolve o tipo,
busca o título e recusa duplicatas. Use `--no-fetch` para não chamar o GitHub.

#### 4.5 Os três hábitos que importam mais que os comandos

- **Mostre antes de escrever.** Rode `discover`, coloque a lista na frente do
  usuário, importe o que ele apontar. Importar um trimestre sem supervisão produz
  uma pilha de candidatos que ninguém vai ler.
- **Nunca promova um sinal descoberto por conta própria.** Confirmação é sua.
- **Faça a pergunta que o GitHub não responde.** O título de uma PR mergeada é um
  marcador. "O que isso mudou para alguém?" é o que transforma em evidência. PR
  mergeada significa mergeada, não bem-sucedida; linhas alteradas não são
  impacto.

---

### 5. Resumo semanal

**Em conversa**

> "fecha minha semana" · "resumo semanal"

**Slash command**

```text
/career-memory:career-weekly
/career-memory:career-weekly last-week
```

Padrão: a semana passada. A semana corrente só quando você pede.

**CLI**

```bash
python3 $CM summary --window last-week --format markdown
python3 $CM summary --period week
python3 $CM summary --window last-week --project pagamentos --format json
```

**Onde vai parar:** `outputs/summaries/2026-W33.md`. **Mantenha esse nome** — é
por ele que o `checkup` sabe que a semana foi fechada.

**O que o resumo contém:** entradas do período, temas, cobertura de evidência, e
comparação com o período anterior.

**Armadilha central:** o store não é a semana. Duas entradas significam duas
entradas **registradas** — não que você fez duas coisas. Uma semana "quieta" é um
fato sobre a captura, não sobre você. Antes de qualquer um concluir algo, vale um
`github discover` no mesmo intervalo.

---

### 6. Resumo mensal

**Slash command**

```text
/career-memory:career-monthly
/career-memory:career-monthly 2026-07
```

**CLI**

```bash
python3 $CM summary --window last-month --format markdown
python3 $CM stats --window 3m          # temas recorrentes
python3 $CM gaps --window last-month   # o que ficou sem prova
```

**Onde vai parar:** `outputs/summaries/2026-08.md`.

**A diferença para o semanal:** um mês não é quatro semanas grampeadas. O resumo
mensal agrupa por tema e projeto, nomeia o que atravessou semanas, e fecha com as
lacunas e com o que vale carregar para o brag document do trimestre. Continua
legível em um minuto.

---

### 7. Checkup — o que está pendente

**Em conversa**

> "como está minha memória de carreira?" · "tem algo pendente?"

**Slash command**

```text
/career-memory:career-checkup
/career-memory:career-checkup github
```

**CLI**

```bash
python3 $CM checkup
python3 $CM checkup --github --github-days 14
python3 $CM checkup --weeks 8 --months 3 --window 6m --format json
```

| Flag            | Padrão | O que faz                                                |
| --------------- | ------ | -------------------------------------------------------- |
| `--weeks`       | `4`    | Quantas semanas fechadas conferir                        |
| `--months`      | `2`    | Quantos meses fechados conferir                          |
| `--window`      | `6m`   | Janela das contagens de lacuna                           |
| `--stale-days`  | `14`   | Idade a partir da qual um candidato parado vira assunto  |
| `--quiet-weeks` | `2`    | Semanas vazias seguidas antes de reportar período quieto |
| `--github`      | —      | Também procura atividade do GitHub fora do registro      |

**O que ele relata:** há quanto tempo foi a última captura, quais semanas ou
meses têm entradas mas não têm resumo, candidatos ainda esperando, e quantas
entradas não podem ser verificadas.

**`checkup` só lê. Nunca escreve.**

**Como ele aparece na prática — memória proativa**

Registrar só funciona se continuar acontecendo, e normalmente para. Depois de
duas semanas ninguém lembra, e o trimestre inteiro some. A skill roda `checkup`
quando você abre a sessão depois de uma pausa, quando pede uma daily, ou quando
pede um documento gerado — **nunca no meio de uma tarefa**. Aí ela diz **uma
linha, com número**:

> Sua última captura foi há 11 dias, e a semana passada tem 4 entradas sem
> resumo. Quer que eu escreva?

Oferece uma vez. Se você não quiser, o assunto morre ali e não volta na sessão.

---

### 8. Gaps — o que o registro ainda não prova

**Em conversa**

> "o que está faltando na minha memória?" · "o que eu não consigo provar?"

**Slash command**

```text
/career-memory:career-gaps
/career-memory:career-gaps last-quarter
```

**CLI**

```bash
python3 $CM gaps --window last-quarter
python3 $CM gaps --window 6m --kind no-impact --kind stale-candidate
python3 $CM gaps --window 12m --project pagamentos --format json
```

**Os seis tipos de lacuna** (`--kind`)

| Tipo                   | Significa                                                    |
| ---------------------- | ------------------------------------------------------------ |
| `no-evidence`          | Entrada que ninguém conseguiria verificar                    |
| `no-impact`            | Impacto nunca documentado                                    |
| `unverified-impact`    | Impacto ainda marcado como `inferred`                        |
| `stale-candidate`      | Candidato nunca confirmado (padrão: parado há 14+ dias)      |
| `quiet-period`         | Trecho sem nada registrado (padrão: 2+ semanas vazias)       |
| `uncovered-competency` | Competência do seu `profile.md` que nenhuma entrada menciona |

A última é a mais útil antes de uma conversa de promoção.

**Como isso é usado na conversa:** lacunas são **perguntas para fazer, uma de
cada vez** — não uma lista para ler em voz alta.

> O fix da tempestade de retry de segunda não tem impacto registrado. Isso parou
> os alertas?

A resposta é registrada exatamente como você deu, com `update --set-impact` ou
`--add-evidence`.

**A regra dura:** a skill **não preenche lacuna**. Se você não sabe, ou não houve
resultado mensurável, `Impact: not documented` continua sendo o estado final
correto — e é o ponto inteiro do desenho.

Cada lacuna é uma afirmação sobre o **registro**, nunca sobre o trabalho. "Sem
evidência anexada" significa que um leitor futuro não tem o que conferir; não
significa que o trabalho foi pequeno.

---

### 9. Trends — como o registro evoluiu

As mesmas entradas, lidas em trimestres em vez de dias.

**Em conversa**

> "como minhas competências evoluíram?" · "o que mudou no meu último ano?"

**Slash command**

```text
/career-memory:career-trends
/career-memory:career-trends 2y
```

**CLI**

```bash
python3 $CM trends --window 12m
python3 $CM trends --window 2y --format markdown
python3 $CM trends --window 12m --bucket quarter --project plataforma --top 12
```

| Flag        | Padrão  | O que faz                                      |
| ----------- | ------- | ---------------------------------------------- |
| `--window`  | `12m`   | Intervalo analisado                            |
| `--bucket`  | `auto`  | Tamanho do período: `month`, `quarter`, `year` |
| `--project` | —       | Recorte                                        |
| `--top`     | `8`     | Temas por seção                                |
| `--format`  | `table` | `markdown`, `json`                             |

**O que ele mostra**

- Entradas e cobertura de evidência **período a período**.
- A **trajetória de cada competência** entre os períodos, com quatro rótulos:

  | Rótulo         | Leitura                                          |
  | -------------- | ------------------------------------------------ |
  | `steady`       | registrado na maioria dos períodos               |
  | `new`          | apareceu pela primeira vez nos períodos recentes |
  | `intermittent` | registrado de forma intermitente                 |
  | `paused`       | nada registrado ultimamente                      |

- Os temas em que o impacto foi **de fato documentado**.
- A primeira metade do intervalo contra a segunda.

**Documento longitudinal:** com `--format markdown`, sai um documento que vai
para `outputs/trends/<since>_<until>.md` — o caminho que o comando imprime.

**A regra dura:** **sumiço no registro não é declínio no trabalho.** "Nada
registrado ultimamente sobre mentoria" significa que nada foi _registrado_. Você
pode ter mentorado alguém toda semana e não contado para ninguém. A saída oferece
recuperar o período (`github discover` naquele intervalo, ou simplesmente
perguntar) em vez de narrar uma queda. E competências são interpretação — logo,
trajetórias construídas sobre elas também são, e isso fica dito.

---

### 10. Promotion — cobertura para um nível-alvo

**Em conversa**

> "que evidências eu tenho para Staff Engineer?" · "o que falta no meu registro
> para Staff?"

**CLI**

```bash
python3 $CM promotion --role "Staff Engineer"
python3 $CM promotion --role "Staff Engineer" --window 12m --format markdown
python3 $CM promotion --role "Tech Lead" \
  --criterion "Liderança técnica:mentoria,migração,RFC" \
  --criterion "Impacto organizacional:cross-team,roadmap"
```

| Flag            | Padrão          | O que faz                                                        |
| --------------- | --------------- | ---------------------------------------------------------------- |
| `--role`        | do `profile.md` | Nível-alvo                                                       |
| `--criterion`   | —               | `NOME[:PALAVRA,PALAVRA]`, repetível; sobrepõe o `profile.md`     |
| `--window`      | `12m`           | Intervalo                                                        |
| `--bucket`      | `auto`          | Tamanho do período                                               |
| `--min-entries` | `3`             | Abaixo disso, o critério lê como "fino no registro"              |
| `--recent-days` | `180`           | Silêncio a partir do qual um critério é marcado como não recente |
| `--format`      | `table`         | `markdown`, `json`                                               |

**De onde vêm os critérios**, nesta ordem:

1. `--criterion` na linha de comando.
2. Um heading `## Promotion criteria` no seu `profile.md`.
3. Como último recurso, e **dito com todas as letras**, as suas
   `## Competencies`.

**Escreva a régua da sua empresa no `profile.md`** e essa análise para de ser
genérica:

```markdown
## Promotion criteria — Staff Engineer

- Technical leadership: mentoring, migration, RFC
- Organisational impact: cross-team, roadmap
- System design: architecture, design doc
```

**Os três baldes.** Cada critério cai em um:

- **registrado repetidamente**
- **fino no registro**
- **nenhuma entrada menciona**

Ele também lista o trabalho registrado que **não casa com critério nenhum** — o
que costuma ser vocabulário diferente, não ausência.

**A regra dura:** **cobertura não é veredito.** `promotion` relata como o
registro cobre os critérios. Se você está pronto para o nível é um julgamento
sobre uma pessoa, feito por gente que conhece o contexto — não por uma ferramenta
lendo arquivos Markdown. "Nenhuma entrada menciona estratégia organizacional"
ajuda; "você não está pronto" não ajuda e pode estar simplesmente errado.

Um critério sem nada registrado é uma **pergunta** antes de ser uma lacuna:
_isso faltou no registro, ou faltou no ano?_ As duas coisas têm correções bem
diferentes, e só você sabe qual é.

---

### 11. Graph — o que aparece junto

**CLI**

```bash
python3 $CM graph --format mermaid
python3 $CM graph --window 2y --nodes project,skill,tag,person --min-weight 3
python3 $CM graph --top 60 --format json
```

| Flag           | Padrão                 | O que faz                                                                |
| -------------- | ---------------------- | ------------------------------------------------------------------------ |
| `--window`     | `12m`                  | Intervalo                                                                |
| `--nodes`      | `project,skill,person` | Também aceita `tag`                                                      |
| `--min-weight` | `2`                    | Quantas entradas duas coisas precisam compartilhar para serem conectadas |
| `--top`        | `40`                   | Limite de arestas                                                        |
| `--format`     | `table`                | `mermaid`, `json`                                                        |

Conecta projetos, competências, tags e pessoas que aparecem juntos nas entradas —
uma aresta é "N entradas mencionam os dois".

**Para que serve na prática:** achar os agrupamentos em que seu trabalho
realmente cai (que é como um brag document deveria ser organizado), e ver a
competência que só aparece ao lado de **um** projeto — exatamente o que um comitê
de promoção pergunta.

---

### 12. Brag document

**Em conversa**

> "gera meu brag document" · "documento de conquistas do trimestre"

**Slash command**

```text
/career-memory:career-brag
/career-memory:career-brag last-quarter
```

Padrão: último trimestre.

**Como é montado:** `list --format full` para as evidências, `stats` para os
temas recorrentes. Trabalho relacionado agrupado por tema, referências de
evidência incluídas, padrões rotulados como observações — e, no fim, uma lista
honesta do trabalho que não tem evidência documentada.

**Onde vai parar:** `outputs/brag.md`.

Para qualquer coisa que atravesse mais de um trimestre, rode `trends` antes: o
documento passa a descansar sobre o que o registro sustenta ao longo do tempo, e
não sobre a última coisa que você mencionou.

---

### 13. Avaliação de desempenho

**Em conversa**

> "monta minha avaliação de desempenho"

**Slash command**

```text
/career-memory:career-review
/career-memory:career-review this-year
```

Padrão: o período de avaliação corrente, ou os últimos seis meses.

**O que muda em relação ao brag:** o `profile.md` é lido primeiro. Se ele nomeia
a régua ou os valores da empresa, o documento é organizado **contra esses**.
Toda afirmação rastreia até uma entrada registrada. Seção sem evidência de apoio é
dita como tal, em vez de ser enchida de linguiça.

**Onde vai parar:** `outputs/performance-review.md`.

---

### 14. Caso de promoção

**Slash command**

```text
/career-memory:career-promotion Staff Engineer
```

Se você não passar o alvo, ele é lido do `profile.md`; se não estiver lá, a skill
pergunta.

**Como é montado:** começa por `promotion --role "<alvo>" --window 12m`. Os três
baldes daquele comando (registrado repetidamente / fino no registro / nada
menciona) são o esqueleto do documento, mais as entradas que não casam com
critério nenhum.

O documento cita as entradas por trás de cada critério, mostra com que frequência
cada padrão aparece e em quantos períodos, e é **específico sobre o que está
fino** — um critério com duas entradas do mesmo projeto é exatamente o tipo de
coisa que um comitê pergunta, e nomear isso primeiro vale mais que qualquer
adjetivo.

Se o `profile.md` não tem `## Promotion criteria`, a skill diz isso e oferece
escrever a régua da empresa lá. A análise é tão boa quanto os critérios que
recebe.

**Onde vai parar:** `outputs/promotion-case.md`.

**Veredito de prontidão só sai se você pedir a opinião explicitamente.**

---

### 15. Bullets de currículo

**Slash command**

```text
/career-memory:career-resume
/career-memory:career-resume backend platform engineer
```

**O que sai:** uma linha cada — verbo forte, o que foi feito, resultado
mensurável. Mas **só com números que você realmente registrou**, ou aritmética
derivada deles.

**Onde vai parar:** `outputs/resume.md`.

---

### 16. Histórias de entrevista (STAR)

**Slash command**

```text
/career-memory:career-interview
/career-memory:career-interview liderança técnica
```

**O que sai:** uma história por agrupamento de entradas — Situation, Task,
Action, Result, Evidence. O **Action** é específico sobre o que **você**
pessoalmente fez. Onde um resultado nunca foi medido, sai "not measured", não uma
estimativa.

**Onde vai parar:** `outputs/interview-stories.md`.

---

### 17. Manutenção do store

```bash
python3 $CM validate    # confere todos os arquivos contra o schema
python3 $CM where       # imprime o caminho do store resolvido
python3 $CM status      # cria o que faltar e relata configurações e perfil
```

`validate` é o que rodar depois de editar arquivos na mão — e você **deve** poder
editar na mão; é Markdown seu.

**Histórico em git**

```bash
cd ~/career-memory && git init && git add . && git commit -m "career memory"
```

---

## Referência

### Janelas de tempo

Todo comando com `--window` aceita o mesmo vocabulário:

| Valor                      | Significa                                      |
| -------------------------- | ---------------------------------------------- |
| `today` / `hoje`           | Hoje                                           |
| `yesterday` / `ontem`      | Ontem                                          |
| `this-week` / `week`       | Segunda desta semana até hoje                  |
| `last-week`                | A semana anterior inteira (segunda a domingo)  |
| `this-month` / `month`     | Dia 1 deste mês até hoje                       |
| `last-month`               | O mês anterior inteiro                         |
| `this-quarter` / `quarter` | Início do trimestre até hoje                   |
| `last-quarter`             | O trimestre anterior inteiro                   |
| `this-year` / `year`       | 1º de janeiro até hoje                         |
| `last-year`                | O ano anterior inteiro                         |
| `7d`, `3w`, `6m`, `2y`     | N dias / semanas / meses / anos atrás até hoje |

Para um intervalo exato, use `--from YYYY-MM-DD --to YYYY-MM-DD`.

Em `--date` (no `add`), o vocabulário é menor: `YYYY-MM-DD`, `today`,
`yesterday`, ou `3d` para três dias atrás.

---

### Schema de uma entrada

Uma entrada é um arquivo Markdown: front matter YAML para a estrutura, corpo para
a história humana.

```yaml
---
id: 2026-08-20-payment-race-condition # único; gerado como <data>-<slug>
date: 2026-08-20 # YYYY-MM-DD, quando o trabalho aconteceu
type: problem-solving
project: payments # opcional
status: confirmed # confirmed | candidate | dismissed
tags:
  - debugging
  - reliability
skills: # interpretação, não fato
  - technical problem solving
people:
  - João
evidence:
  - type: github_pr
    reference: "acme/payments#1234"
    url: https://github.com/acme/payments/pull/1234 # opcional
    title: Serialise payment capture # opcional
  - type: metric
    reference: "API latency dashboard"
    value: "800ms → 300ms"
impact:
  statement: Addressed intermittent payment-processing failures
  confidence: factual # factual | inferred | uncertain
context: The issue was intermittent and hard to reproduce
source: slack # onde você contou, opcional
---
```

Só `id` e `date` são estruturalmente obrigatórios. O resto é omitido quando
desconhecido — um campo ausente é honesto, um chute vazio não é.

**Tipos de entrada**

| Tipo              | Use quando                                     |
| ----------------- | ---------------------------------------------- |
| `achievement`     | Uma realização concreta                        |
| `delivery`        | Algo entregue, lançado, colocado no ar         |
| `impact`          | Um resultado medido ou reportado               |
| `problem-solving` | Um problema difícil diagnosticado ou corrigido |
| `feedback`        | Feedback recebido (vai para `feedback/`)       |
| `learning`        | Algo aprendido; ainda não é conquista          |
| `leadership`      | Direção, decisões, mentoria, ownership         |
| `collaboration`   | Trabalho com ou para outras pessoas            |

O tipo é inferido — você não precisa escolher. Quando um evento é genuinamente
dois tipos (liderou a migração **e** entregou), o dominante vira `type` e o outro
vira tag.

**Tipos de evidência**

`github_pr`, `github_issue`, `github_review`, `github_commit`, `document`,
`metric`, `dashboard`, `feedback`, `email`, `slack_message`, `meeting`, `ticket`,
`external_link`

Forma na CLI: `type:reference[:value]`

```bash
--evidence 'github_pr:#1234'
--evidence 'github_pr:https://github.com/acme/payments/pull/1234'
--evidence 'metric:API latency dashboard:800ms → 300ms'
--evidence 'meeting:Q3 planning review'
```

Uma URL é mantida inteira; qualquer outra coisa quebra no próximo dois-pontos
para virar `value`.

**Confiança do impacto**

| Valor       | Significa                                               |
| ----------- | ------------------------------------------------------- |
| `factual`   | Você afirmou, ou decorre aritmeticamente do que afirmou |
| `inferred`  | Uma leitura razoável do que você afirmou                |
| `uncertain` | Precisa de confirmação antes de alguém depender disso   |

`inferred` nunca vira `factual` silenciosamente. Se uma conversa posterior
confirma, isso é um `update` — uma mudança real com um gatilho real.

Detalhes completos: [`skills/career-memory/references/entry-schema.md`](../skills/career-memory/references/entry-schema.md).

---

### Referência completa da CLI

```bash
CM=~/.claude/skills/career-memory/scripts/career_memory.py
```

Flags globais: `--version`, `--dir <caminho>` (sobrepõe a resolução do store).

| Comando                                                                                  | O que faz                                                    |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `init`                                                                                   | Cria o store                                                 |
| `status [--format text\|json]`                                                           | Cria o que faltar e relata configurações, perfil e `blocked` |
| `config [--get KEY] [--set KEY=VALUE]…`                                                  | Lê ou muda configurações                                     |
| `where`                                                                                  | Imprime o caminho do store resolvido                         |
| `add "<título>" [flags]`                                                                 | Escreve uma entrada nova                                     |
| `update <id> [flags]`                                                                    | Emenda uma entrada existente                                 |
| `show <id>`                                                                              | Imprime uma entrada                                          |
| `list [filtros]`                                                                         | Lista entradas                                               |
| `search "<consulta>" [filtros]`                                                          | Busca em texto, tags, competências e pessoas                 |
| `promote <id>`                                                                           | Candidato → entrada confirmada                               |
| `dismiss <id>`                                                                           | Apaga um candidato                                           |
| `stats [filtros]`                                                                        | Contagens e temas recorrentes                                |
| `summary [--period week\|month] [--window] [--project] [--format table\|markdown\|json]` | O que uma semana ou um mês contém                            |
| `gaps [--window] [--kind]… [--stale-days] [--quiet-weeks] [--project]`                   | O que o registro ainda não prova                             |
| `checkup [--weeks] [--months] [--window] [--github] [--github-days]`                     | Pendências e lacunas em uma olhada                           |
| `trends [--window] [--bucket] [--project] [--top] [--format]`                            | Como o registro evoluiu                                      |
| `promotion [--role] [--criterion]… [--window] [--min-entries] [--recent-days]`           | Cobertura dos critérios de um nível                          |
| `graph [--window] [--nodes] [--min-weight] [--top] [--format table\|mermaid\|json]`      | O que as entradas mencionam junto                            |
| `validate`                                                                               | Confere todos os arquivos contra o schema                    |
| `github check`                                                                           | Verifica acesso e identidade                                 |
| `github discover [flags]`                                                                | Lista atividade e o que já está registrado                   |
| `github import [flags]`                                                                  | Escreve os sinais novos em `candidates/`                     |
| `github link <id> <ref>…`                                                                | Anexa PR/issue/review/commit a uma entrada                   |

Qualquer comando aceita `--help` para a lista completa de flags:

```bash
python3 $CM add --help
python3 $CM github discover --help
```

Python 3.9+, apenas biblioteca padrão. PyYAML é usado se estiver disponível, mas
não é necessário.

---

### Estrutura do store

```text
~/career-memory/
├── README.md           explica o próprio diretório
├── profile.md          seu cargo, foco, objetivos e (opcionalmente) a régua da empresa
├── config.json         idioma e comportamento da skill
├── entries/            evidências confirmadas, um arquivo por evento
├── candidates/         possíveis evidências aguardando sua confirmação (inclusive as do GitHub)
├── feedback/           feedbacks recebidos
├── projects/           contexto por projeto
└── outputs/            documentos gerados
    ├── summaries/      resumos semanais e mensais, um arquivo por período
    └── trends/         visões longitudinais de como o registro evoluiu
```

Local por padrão. Sem banco de dados, sem conta, sem servidor. Legível e editável
sem nenhum agente.

**Onde cada documento é salvo**

| Documento               | Caminho                             |
| ----------------------- | ----------------------------------- |
| Brag document           | `outputs/brag.md`                   |
| Avaliação de desempenho | `outputs/performance-review.md`     |
| Caso de promoção        | `outputs/promotion-case.md`         |
| Bullets de currículo    | `outputs/resume.md`                 |
| Histórias de entrevista | `outputs/interview-stories.md`      |
| Resumo semanal          | `outputs/summaries/2026-W33.md`     |
| Resumo mensal           | `outputs/summaries/2026-08.md`      |
| Documento de tendências | `outputs/trends/<since>_<until>.md` |

---

## Receitas

**Primeiro dia**

```text
/career-memory:career-init
```

Responda cargo, foco e objetivos. Depois é só trabalhar e mencionar o que você
fez.

**Semana típica**

1. Durante a semana: mencione o que fez, a captura acontece sozinha.
2. Sexta: `/career-memory:career-github last-week` — importe o que importou.
3. Sexta: `/career-memory:career-weekly` — feche a semana.

**Antes da avaliação de desempenho**

```text
/career-memory:career-checkup
/career-memory:career-gaps last-quarter
/career-memory:career-trends 12m
/career-memory:career-review this-year
```

Nessa ordem: primeiro descubra o que está pendente, responda as perguntas de
lacuna, veja a leitura longitudinal, e só então gere o documento.

**Preparando um caso de promoção**

1. Escreva a régua da sua empresa no `profile.md`, sob
   `## Promotion criteria — <Nível>`.
2. `python3 $CM promotion --role "Staff Engineer" --window 12m` — veja os baldes.
3. Ataque os critérios "fino no registro" e "nada menciona": eles são perguntas
   antes de serem lacunas.
4. `/career-memory:career-promotion Staff Engineer`.

**Preparando entrevistas**

```text
/career-memory:career-trends 2y
/career-memory:career-interview liderança técnica
/career-memory:career-resume
```

**Recuperando um período que você não registrou**

```bash
python3 $CM github discover --window last-quarter
python3 $CM github import --window last-quarter --dry-run
```

Depois confirme um a um, respondendo a pergunta que o GitHub não responde: o que
aquilo mudou para alguém.

---

## Solução de problemas

| Sintoma                                          | O que é                                      | O que fazer                                                                           |
| ------------------------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------------- |
| `add` recusa escrever e lista entradas parecidas | A checagem de duplicata funcionando          | Leia as candidatas: normalmente o certo é `update` na existente, não `add --force`    |
| `blocked: documents` no `status`                 | `profile.md` incompleto                      | Preencha cargo, foco e objetivos — três respostas. Ou mude para `profile_gate=remind` |
| Exit code 3 em qualquer `github …`               | Sem acesso ao GitHub (não "nada encontrado") | `gh auth login`, ou exporte `GITHUB_TOKEN`. Nada mais na skill depende disso          |
| O store não é o que eu esperava                  | Ordem de resolução                           | `python3 $CM where`; fixe com `export CAREER_MEMORY_HOME=…`                           |
| Respostas no idioma errado                       | `language=auto` está seguindo sua mensagem   | `python3 $CM config --set language=pt`                                                |
| Documento em idioma diferente das respostas      | É o desenho                                  | `documents_language` é separado de `language`. Ajuste ou use `ask`                    |
| Editei arquivos na mão e quero conferir          | —                                            | `python3 $CM validate`                                                                |
| `unrecognised window`                            | Vocabulário de janela                        | Veja [Janelas de tempo](#janelas-de-tempo), ou use `--from` / `--to`                  |
| Importei demais do GitHub                        | `candidates/` cheio                          | `dismiss` os que não interessam. Da próxima vez, `discover` antes de `import`         |

---

## O que a skill nunca faz

Estes não são bugs a corrigir — são o produto.

- **Não inventa.** Nenhuma métrica, percentual, resultado, data, nome ou feedback
  que você não tenha dito. Quando falta informação, o registro diz que falta.
- **Não preenche lacuna por você.** Cada lacuna vira uma pergunta; sem resposta,
  `Impact: not documented` continua sendo o estado correto.
- **Não confunde o registro com o trabalho.** Duas entradas significam duas
  entradas _registradas_. Uma queda em relação ao mês passado é um fato sobre a
  captura, não sobre você.
- **Não transforma sumiço em declínio.** Um tema que some do registro pode ter
  continuado sem ser anotado. A saída oferece recuperar o período.
- **Não dá veredito de prontidão.** `promotion` relata cobertura. Se você está
  pronto para o nível é julgamento sobre uma pessoa, feito por gente que conhece
  o contexto.
- **Não promove sinal do GitHub sozinha.** Import escreve candidatos e só isso.
- **Não manda seus dados para lugar nenhum.** Tudo é Markdown local que você pode
  ler, mudar, commitar ou apagar sem nenhum agente.

---

## Para ir mais fundo

| Documento                                                                          | Conteúdo                                                 |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------- |
| [`skills/career-memory/SKILL.md`](../skills/career-memory/SKILL.md)                | O contrato de comportamento do agente                    |
| [`references/entry-schema.md`](../skills/career-memory/references/entry-schema.md) | Schema, tipos, evidências, confiança                     |
| [`references/capture.md`](../skills/career-memory/references/capture.md)           | Heurísticas de captura, candidatos, duplicatas, exemplos |
| [`references/daily.md`](../skills/career-memory/references/daily.md)               | Modo standup em detalhe                                  |
| [`references/github.md`](../skills/career-memory/references/github.md)             | Descoberta, import, linkagem de evidência                |
| [`references/proactive.md`](../skills/career-memory/references/proactive.md)       | Resumos, evidência faltante, quando _não_ interromper    |
| [`references/intelligence.md`](../skills/career-memory/references/intelligence.md) | Trends, análise de lacuna para promoção, grafo           |
| [`references/outputs.md`](../skills/career-memory/references/outputs.md)           | Regras de cada documento gerado                          |
| [`docs/SPEC.md`](SPEC.md)                                                          | Especificação completa                                   |
