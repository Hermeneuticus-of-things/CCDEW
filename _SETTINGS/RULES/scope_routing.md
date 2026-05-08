# Scope routing project/root

## Purpose

This rule establishes where to work physically in `<WORKSPACE_DIR>` for any future request.

## Main rule

Work in project or in workspace root depending on the scope of the request.

## When to work in a project

If the request is about a specific project, work in:

`<WORKSPACE_DIR>/PROJECTS/<ProjectName>/`

Examples:
- MyProject → `<WORKSPACE_DIR>/PROJECTS/MyProject/`
- AnotherProject → `<WORKSPACE_DIR>/PROJECTS/AnotherProject/`

In the project, update project memory as needed:
- `CHANGELOG.md`
- `TODO.md`
- `BUG_LOG.md`
- `SESSION_STATUS.md`
- `CLAUDE.md`
- `BEST_PRACTICES.md`
- `doc/`

## When to work at root

Work at root `<WORKSPACE_DIR>` only for requests that affect the workspace as a whole:

- general rules
- workspace structure
- templates
- global or type-specific best practices
- folder organization
- indexes
- rules for future sessions
- cross-project meta-tasks

Allowed places for meta-workspace work:
- `<WORKSPACE_DIR>/CLAUDE.md`
- `<WORKSPACE_DIR>/BEST_PRACTICES.md`
- `<WORKSPACE_DIR>/CHANGELOG.md`
- `<WORKSPACE_DIR>/TODO.md`
- `<WORKSPACE_DIR>/_SETTINGS/`
- `<WORKSPACE_DIR>/_BEST_PRACTICES/`
- `<WORKSPACE_DIR>/_TEMPLATES/`

## What NOT to do

- Do not mix files from one project into another project.
- Do not put working files of a project directly in root.
- Do not modify `_ARCHIVE` without explicit request.
- Do not modify root for tasks that clearly belong to a project.

## Memory for the future

When the user says something must be remembered for the future, write the rule in physical `.md` files:
- project rule → in the relevant project
- global rule → in root / `_SETTINGS`
- recurring lesson → in `BEST_PRACTICES.md` at the appropriate level

Principle: if it is not written on disk, it can be lost after the session.
