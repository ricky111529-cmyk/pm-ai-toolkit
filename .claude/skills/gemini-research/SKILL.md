---
name: gemini-research
description: Uses Gemini CLI for web search, code analysis, and real-time information. Use when the user needs current information, web search, code review, or a second opinion.
---

# Research Assistant with Gemini CLI

Use Gemini CLI as a complementary research and analysis tool.

## When to use

Use Gemini CLI when:

- **Web search or real-time info needed**
  - Current events, latest versions, releases, recent changes
  - Keywords: "latest", "current", "newest", "2025", "recent", "today"
  - Up-to-date best practices, standards, comparisons

- **Second AI perspective valuable**
  - Code analysis, security reviews, architecture decisions
  - Cross-checking assumptions or implementation approaches

- **Research needed**
  - Unfamiliar libraries, frameworks, APIs
  - Best practices, patterns, trade-offs

## Basic usage

```bash
# Always use JSON output for parsing
gemini "PROMPT" --output-format json

# Extract response safely
result=$(gemini -p "Your prompt" --output-format json)
echo "$result" | jq -r '.response'

# Or use the helper script
./scripts/run-gemini.sh "Your prompt"
```

## Model selection

- `gemini-3-flash-preview` - **Default for web search and current info**
- `gemini-3-pro-preview` - Deep code analysis, complex reasoning
- `gemini-2.5-pro` - Stable fallback
- `gemini-2.5-flash` - Quick, simple queries

## File inclusion

```bash
# Single file
gemini "@src/main.ts Review this file"

# Directory
gemini "@src/components/ Find code smells"

# Multiple paths
gemini "@src/ @tests/ Analyze coverage"
```

> Paths are relative to current directory.

## Common patterns

### Web search

```bash
gemini "What are the latest features in React 19?" \
  --model gemini-3-flash-preview --output-format json | jq -r '.response'
```

### Code analysis

```bash
gemini "@src/auth.ts Review for security issues" \
  --model gemini-3-pro-preview --output-format json | jq -r '.response'
```

### Second opinion

```bash
gemini "@src/cache.ts Is this appropriate for high-traffic?" \
  --model gemini-3-pro-preview --output-format json | jq -r '.response'
```

## Workflow

1. **Decide if web search needed**
   - Keywords: "latest", "current", "2025", "recent"
   - Version/release questions
   - Current best practices

2. **Execute search**

   ```bash
   gemini "User's question" --model gemini-3-flash-preview --output-format json
   ```

3. **Present results**
   - Cite Gemini CLI + web search
   - Include relevant URLs
   - Apply findings to user's context

## Key points

- Always use `--output-format json` for automation
- Check `.error` before using `.response`
- Gemini is a complement to Claude, not a replacement
- Keep `@` scopes focused to avoid context overload
- For details see: [reference.md](reference.md), [examples.md](examples.md)

## Quick reference

```bash
# Web search
gemini "query" --model gemini-3-flash-preview --output-format json | jq -r '.response'

# Code analysis
gemini "@path/to/code prompt" --model gemini-3-pro-preview --output-format json | jq -r '.response'

# Multiple paths
gemini "@src/ @tests/ prompt" --output-format json | jq -r '.response'
```

See [scripts](scripts/run-gemini.sh) for a helper script.
