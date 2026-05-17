# ClaudeLens

A **skill-collision linter** for [Claude Code](https://claude.com/claude-code). Scans a `.claude/skills/` directory and flags:

- **Naming clashes** — duplicate or near-duplicate slugs that confuse routing.
- **Overlapping descriptions** — two skills whose "when to use this" text is semantically too close, so the wrong one fires.
- **Ambiguous triggers** — shared trigger keywords / regex patterns across skills.

> If two skills have overlapping descriptions you can get the wrong one. ClaudeLens tells you which pairs are at risk *before* a user hits the collision in production.

## Install

```bash
# Minimal install (string-similarity checks only)
pip install claudelens

# With semantic similarity (pulls sentence-transformers + torch)
pip install "claudelens[semantic]"
```

Or from source:

```bash
git clone https://github.com/ahyaanlakhani/claudelens
cd claudelens
poetry install --extras semantic
```

## Quick start

```bash
# Lint the skills in the current repo
claudelens lint .claude/skills

# Strict mode: non-zero exit on warnings too
claudelens lint .claude/skills --strict

# Show all skill pairs sorted by similarity, not just collisions
claudelens lint .claude/skills --show-all
```

## GitHub Action

```yaml
# .github/workflows/claudelens.yml
name: ClaudeLens
on: [pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ahyaanlakhani/claudelens@v0
        with:
          path: .claude/skills
          strict: "true"
```

## Skill file format

ClaudeLens reads YAML frontmatter from either:

- `<skills_dir>/<skill-name>/SKILL.md`, or
- `<skills_dir>/<skill-name>.md`

Required frontmatter:

```yaml
---
name: my-skill
description: When to use this skill — be specific about triggers.
---
```

Optional fields ClaudeLens understands:

- `triggers:` — list of strings or regex patterns this skill responds to.
- `aliases:` — alternate slugs the skill is also known by.

## Configuration

Project-level config lives in `.claudelens.toml`:

```toml
[thresholds]
# Cosine similarity above which two descriptions are flagged as colliding.
description_similarity = 0.82

# Levenshtein-ratio above which two slugs are flagged as too close.
name_similarity = 0.85

[ignore]
# Pairs that are intentionally similar (e.g. "review" and "security-review").
pairs = [["review", "security-review"]]
```

## License

MIT
