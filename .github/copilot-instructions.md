# Repository instructions

## Shared instructions

Before starting a task, read the shared instructions index at
`../../dev_doc/agent-instructions/README.md` and the topic files relevant to
the task. Follow `../../dev_doc/.github/copilot-instructions.md` as well.

Read this repository's `AGENTS.md` and `docs/AGENTS.md` if present before
editing. Preserve project-specific instructions and unrelated worktree changes.

## Shared skills

The versioned `.github/skills` symlink points to the central `dev_doc/skills`
collection. Before starting a task, review the skill descriptions in
`.github/skills/*/*/SKILL.md` and load every relevant skill. For documentation
work, review all descriptions in `.github/skills/documentation/*/SKILL.md`,
then apply every relevant documentation skill.

If the client does not discover the category-nested skills or cannot load a
skill, read its `SKILL.md` directly before editing. If the link is broken,
report the missing central checkout; do not silently skip the standards or
copy skill definitions into this repository.

## Project-specific guidance

Keep implementation details and product documentation in this repository.
Use the shared `../../dev_doc/` instructions for cross-project practices.

Read `doc/requirements/TODO-INDEX.md` when starting work. Simple, clearly
scoped items are standing implementation tasks: complete fitting independent
items alongside the main task without waiting for another request. Preserve
the main task and concurrent edits. Plain bullet points are direct tasks;
complex or unclear topics have their own heading and a clickable concept
link first. Move completed items to the corresponding DONE subsection.
This mini TODO sheet is exempt from per-block YAML metadata; keep that
metadata in architecture and feature documentation.
