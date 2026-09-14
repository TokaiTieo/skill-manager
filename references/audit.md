# Audit rules

## Scope and deterministic checks
The scanner inventories immediate skill folders and .system children, or a root that is itself a skill. It does not recurse into tests/fixtures or discover nested fixture skills. Supply each plugin skill root separately. No registry completeness claim is possible from local roots alone.
Each entry records file paths, sizes, hashes, description and findings. Symlinks/junctions are skipped; unreadable files and roots are findings. Files over 2 MB are inventoried but not text-parsed.
The official validator is optional: when absent or unavailable, report UNKNOWN, never fabricate a pass. It executes only the explicitly selected trusted validator with timeout; target scripts are not executed.
Additional checks: nonempty name/description, folder-name match, UI YAML types, short-description length, default-prompt skill name, missing linked local resources, Python syntax, missing tests/evals and mtime age. Other executable languages require a reviewed runtime check.

## Human semantic review
Inspect descriptions and relevant entrypoints for shared user intents, exclusions, outputs and authorization behavior. Compare positive, negative and borderline user requests. Same keywords alone are not a conflict. Lexical Jaccard candidates and identical descriptions are leads, not final semantic diagnoses; Chinese uses character bigrams. Check body-level capabilities even when names/descriptions differ. Quote the conflicting clauses and explain the routing consequence. Report coexistence when boundaries are complementary.
Compare openai.yaml display intent with SKILL.md. Do not require optional metadata files or policy flags. Preserve unknown supported fields for forward compatibility.

## Resources and freshness
Resolve Markdown inline links relative to their containing document, strip anchors, check files inside the skill; external/escaping paths require manual review. Inline code paths, reference-style links, dynamic imports and dependency availability require manual review.
Old file mtime is a review candidate only. For suspected obsolescence record source/version, verified date and authoritative replacement evidence. A 401/403/timeout does not prove a dead URL. Do not automatically visit URLs or run scripts while scanning. Unlinked resources may be invoked dynamically: inspect callers before recommending removal.

## Report
JSON schema version 1 includes roots, entries, findings and overlaps. Findings contain status/code/path/detail; statuses: Broken (confirmed static defect), Warning, Untested, Stale (review candidate), Unknown. Overlaps are ConflictCandidate. Healthy means no static findings within the stated scope only.
Add an agent-written health narrative: counts, highest impact issues, evidence paths, recommended action, confidence and skipped checks. Missing tests/evals are coverage prompts, not invalid skill structure. Record real validation logs separately.
