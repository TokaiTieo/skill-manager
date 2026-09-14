# Maintenance operations

The agent performs these workflows; the CLI deliberately provides no destructive apply command.

1. Capture a snapshot and read affected resources/callers. Record source hashes, owner (user/system/plugin), approved scope and intended outcome.
2. Prepare a staging copy outside discoverable roots. Do not initialize an existing skill again.
3. Use the current installed skill-creator to implement the proposed change. Produce a reviewable diff and capability map; get authorization only if the actual mutation is not already authorized.
4. Run validation and relevant isolated tests. Recheck installed hashes before applying; if they changed, rebase the plan instead of overwriting concurrent edits.
5. Retain an external backup and apply only scoped changes. Validate installed result; on failure restore only files changed by this operation when their hashes still match, otherwise stop for reconciliation. Report any partial state.

## Operation-specific requirements
- update: preserve unrelated instructions/resources and supported metadata.
- merge: map every source capability to the target, resolve trigger boundaries and relative links; keep sources until explicit retirement authorization.
- split: map each capability to a destination, update links and routing, verify there are no dropped capabilities or duplicate ambiguous triggers.
- rename: check destination collision, change folder/frontmatter/default prompt and all discovered callers; report external callers that cannot be searched. Retire the old path only within explicit authorization.
- regenerate metadata: read skill-creator/references/openai_yaml.md. Its generator replaces the whole file; use it only for new metadata or interface-only files. If policy/dependencies/other fields exist, patch intended interface fields in place and verify preservation.
For any destination collision, show the existing content and reconcile explicitly; never force overwrite. System and plugin caches receive recommendations, not automatic edits.

## Diff report
Use snapshot before/after JSON with the CLI diff command for added/removed/modified files and unified text diffs. Snapshots contain source text and may be sensitive; store locally outside skills, never upload automatically. Include old/new hashes, test evidence and rollback location in the narrative. Binary/large files use hashes. A rename appears as removal/addition and must be explained.
