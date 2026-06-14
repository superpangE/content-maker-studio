# Content Studio -- Content Creation Agent Architecture

Content creation managed through coordinated Claude Code subagents. Each agent
owns a specific stage, enforcing separation of concerns and quality. The first
content type is **blog posts** (Naver, Tistory/WordPress); shorts and other
formats extend the same pattern.

> This studio borrows its structure from a game-studio template. The
> game-development agents, skills, and templates still exist in `.claude/` and
> `design/`/`src/`/`production/` but are **not used** by the content workflow.
> Use the content agents and skills described in the Content Studio doc below.

## Content Studio

@.claude/docs/content-studio.md

## Collaboration Protocol

**User-driven collaboration, not autonomous execution.**
Every task follows: **Question -> Options -> Decision -> Draft -> Approval**

- Agents MUST ask "May I write this to [filepath]?" before using Write/Edit tools
- Agents MUST show drafts or summaries before requesting approval
- Multi-file changes require explicit approval for the full changeset
- No commits without user instruction

See `docs/COLLABORATIVE-DESIGN-PRINCIPLE.md` for full protocol and examples.

> **First session?** If the project has no engine configured and no game concept,
> run `/start` to begin the guided onboarding flow.

## Coding Standards

@.claude/docs/coding-standards.md

## Context Management

@.claude/docs/context-management.md
