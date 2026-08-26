---
description: Set up your Career Memory store, profile and settings
argument-hint: "[optional path]"
---

Use the `career-memory` skill.

Set up Career Memory. If the user passed a path in `$ARGUMENTS`, use it as the
store location and tell them to export `CAREER_MEMORY_HOME` to that path so it
is found next time; otherwise use the default resolution order.

Run `status` — it creates everything that is missing — then show the resulting
layout and the current settings.

Then complete `profile.md` in one short exchange, not a questionnaire: role,
focus, current goals. This is setup time, so it is the right moment to ask; do
not let it turn into an interrogation. Write the answers into the file and
confirm with `status` that the profile now reads as complete.

Finally, confirm the language settings out loud, since they govern everything
the skill writes from here on: `language` (auto/pt/en) and `documents_language`
(same/pt/en/ask). Change them with `config --set` if the user wants something
other than the current values.
