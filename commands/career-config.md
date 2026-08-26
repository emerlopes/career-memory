---
description: Show or change Career Memory settings (language, profile gate)
argument-hint: "[e.g. language=pt]"
---

Use the `career-memory` skill.

Show or change Career Memory settings: $ARGUMENTS

With no arguments, run `python3 "$CM" config` and explain what each setting
does in plain terms — what changes for the user, not what the field is called.

With arguments, translate the request into `config --set key=value` and apply
it. Accept natural phrasing: "responde sempre em português" is
`language=pt`; "documentos em inglês" is `documents_language=en`; "não me
bloqueie" is `profile_gate=remind`. Confirm the new value, and say what will
behave differently from now on.

Settings live in `config.json` in the store, so they persist across sessions.
