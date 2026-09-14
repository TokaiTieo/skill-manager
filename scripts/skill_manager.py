"""Read-only skill inventory/audit/snapshot/diff. Python 3.10+, PyYAML."""
import argparse
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import unquote

import yaml

LIMIT = 2 * 1024 * 1024

def linked(p):
    return p.is_symlink() or bool(getattr(p, "is_junction", lambda: False)())

def finding(status, code, path, detail):
    return dict(status=status, code=code, path=str(path), detail=str(detail))

def walk(root):
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "__pycache__", ".venv"))
        for d in list(dirs):
            p = Path(base) / d
            if linked(p):
                dirs.remove(d)
                yield p
        for name in sorted(names):
            yield Path(base) / name

def discover(roots):
    result, issues = [], []
    for value in roots:
        root = Path(value).absolute()
        if not root.is_dir() or linked(root):
            issues.append(finding("Unknown", "root-unavailable", root, "Missing, non-directory or linked root"))
            continue
        if (root / "SKILL.md").is_file():
            result.append(root)
            continue
        try:
            children = list(root.iterdir())
            system = root / ".system"
            if system.is_dir() and not linked(system):
                children += list(system.iterdir())
            for p in children:
                if linked(p):
                    issues.append(finding("Unknown", "link-skipped", p, "Not followed"))
                elif p.is_dir() and not p.name.startswith("."):
                    result.append(p)
        except OSError as e:
            issues.append(finding("Unknown", "root-read", root, e))
    return sorted(set(result)), issues

def capture(root):
    records, issues = {}, []
    for p in walk(root):
        rel = p.relative_to(root).as_posix()
        if linked(p):
            issues.append(finding("Unknown", "link-skipped", p, "Not followed"))
            continue
        try:
            data = p.read_bytes()
            record = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            if len(data) <= LIMIT:
                try:
                    record["text"] = data.decode("utf-8-sig")
                except UnicodeDecodeError:
                    pass
            records[rel] = record
        except OSError as e:
            issues.append(finding("Unknown", "file-read", p, e))
    return records, issues

def audit_one(root, validator=None, stale_days=365):
    records, issues = capture(root)
    def add(status, code, path, detail):
        issues.append(finding(status, code, path, detail))
    content = records.get("SKILL.md", {}).get("text", "")
    metadata = {}
    try:
        match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.S)
        metadata = yaml.safe_load(match[1]) if match else None
        if not isinstance(metadata, dict):
            raise ValueError("Missing or invalid mapping frontmatter")
        for key in ("name", "description"):
            if not isinstance(metadata.get(key), str) or not metadata[key].strip():
                add("Broken", "frontmatter-field", root / "SKILL.md", key + " must be a nonempty string")
        if metadata.get("name") != root.name:
            add("Warning", "folder-name", root, "Folder and frontmatter name differ")
    except (ValueError, yaml.YAMLError) as e:
        metadata = {}
        add("Broken", "frontmatter", root / "SKILL.md", e)
    validation = {"status": "Unknown", "detail": "Official validator not supplied"}
    if validator:
        try:
            run = subprocess.run([sys.executable, "-X", "utf8", "-B", str(validator), str(root)],
                                 capture_output=True, text=True, encoding="utf-8", timeout=30)
            detail = (run.stdout + run.stderr).strip()
            validation = {"status": "Pass" if run.returncode == 0 else "Fail",
                          "exit_code": run.returncode, "detail": detail, "validator": str(validator)}
            if run.returncode:
                add("Warning", "quick-validate-failed", root, detail)
        except (OSError, subprocess.TimeoutExpired) as e:
            validation = {"status": "Unknown", "detail": str(e)}
    if validation["status"] == "Unknown":
        add("Unknown", "quick-validate-unavailable", root, validation["detail"])
    ui = records.get("agents/openai.yaml")
    if ui:
        try:
            data = yaml.safe_load(ui.get("text", ""))
            if not isinstance(data, dict):
                raise ValueError("Metadata must be a mapping")
            interface = data.get("interface", {})
            if not isinstance(interface, dict):
                raise ValueError("interface must be a mapping")
            for key in ("display_name", "short_description", "default_prompt", "icon_small", "icon_large", "brand_color"):
                if key in interface and not isinstance(interface[key], str):
                    raise ValueError(key + " must be a string")
            short = interface.get("short_description")
            if short is not None and not 25 <= len(short) <= 64:
                add("Warning", "ui-length", root / "agents/openai.yaml", "short_description should be 25-64 characters")
            prompt = interface.get("default_prompt")
            if prompt is not None and "$" + str(metadata.get("name", root.name)) not in prompt:
                add("Warning", "ui-prompt", root / "agents/openai.yaml", "default_prompt lacks skill invocation")
            policy = data.get("policy", {})
            if not isinstance(policy, dict) or ("allow_implicit_invocation" in policy and not isinstance(policy["allow_implicit_invocation"], bool)):
                raise ValueError("Invalid invocation policy type")
            for key in ("icon_small", "icon_large"):
                if key in interface and not (root / interface[key]).is_file():
                    add("Warning", "missing-icon", root / "agents/openai.yaml", interface[key])
        except (ValueError, yaml.YAMLError) as e:
            add("Broken", "ui-yaml", root / "agents/openai.yaml", e)
    for rel, record in records.items():
        p, text = root / rel, record.get("text")
        if rel.startswith(("references/", "scripts/")):
            try:
                if time.time() - p.stat().st_mtime > stale_days * 86400:
                    add("Stale", "age-review", p, "Age threshold exceeded; obsolescence not established")
            except OSError as e:
                add("Unknown", "mtime", p, e)
        if text is None:
            continue
        if rel.startswith("scripts/") and p.suffix == ".py":
            try:
                ast.parse(text, filename=str(p))
            except SyntaxError as e:
                add("Broken", "python-syntax", p, e)
        if p.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^)\n]+)\)", text):
                target = unquote(target.strip().strip("<>").split("#")[0])
                if not target or re.match(r"^[a-zA-Z][\w+.-]*:", target):
                    continue
                dest = (p.parent / target).resolve()
                if not dest.is_relative_to(root.resolve()):
                    add("Unknown", "external-local-link", p, target)
                elif not dest.exists():
                    add("Broken", "missing-link", p, target)
    for directory in ("tests", "evals"):
        if not any(k.startswith(directory + "/") for k in records):
            add("Untested", "missing-" + directory, root, "Coverage not supplied; not a structural error")
    return dict(path=str(root), name=metadata.get("name"), description=metadata.get("description"),
                files=records, findings=issues, quick_validate=validation,
                execution={"target_scripts": "not run", "unit_tests": "not run", "behavioral_evals": "not run"})

def tokens(value):
    value = str(value or "").lower()
    words = set(re.findall(r"[a-z0-9]{3,}", value))
    for segment in re.findall(r"[\u3400-\u9fff]+", value):
        words.update(segment[i:i+2] for i in range(len(segment)-1))
    return words - {"the", "and", "for", "with", "when", "skill", "skills", "use"}

def overlaps(entries):
    result = []
    for i, a in enumerate(entries):
        for b in entries[i+1:]:
            x, y = tokens(a["description"]), tokens(b["description"])
            score = len(x & y) / len(x | y) if x | y else 0
            identical = bool(a["description"]) and a["description"] == b["description"]
            same_name = bool(a["name"]) and a["name"] == b["name"]
            if identical or same_name or score >= .5:
                result.append(dict(status="ConflictCandidate", paths=[a["path"], b["path"]],
                                   score=round(score, 3), identical_description=identical,
                                   duplicate_name=same_name, needs_semantic_review=True))
    return result

def snapshot(roots):
    paths, issues = discover(roots)
    entries = {}
    for p in paths:
        files, errors = capture(p)
        entries[str(p)] = files
        issues += errors
    return dict(schema_version=1, roots=list(map(str, roots)), entries=entries, findings=issues)

def diff(before, after):
    changes = []
    for root in sorted(set(before["entries"]) | set(after["entries"])):
        a, b = before["entries"].get(root, {}), after["entries"].get(root, {})
        for rel in sorted(set(a) | set(b)):
            old, new = a.get(rel), b.get(rel)
            if old and new and old["sha256"] == new["sha256"]:
                continue
            change = dict(root=root, file=rel, kind="added" if old is None else "removed" if new is None else "modified",
                          before_sha256=old["sha256"] if old else None, after_sha256=new["sha256"] if new else None)
            if (old is None or "text" in old) and (new is None or "text" in new):
                change["unified_diff"] = "".join(difflib.unified_diff(
                    (old or {}).get("text", "").splitlines(True),
                    (new or {}).get("text", "").splitlines(True), fromfile="before/" + rel, tofile="after/" + rel))
            changes.append(change)
    return dict(schema_version=1, changes=changes, complete=not(before.get("findings") or after.get("findings")),
                findings=before.get("findings", []) + after.get("findings", []))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inventory", "audit", "snapshot"):
        p = sub.add_parser(name)
        p.add_argument("--root", action="append", required=True)
        if name == "audit":
            p.add_argument("--validator", type=Path)
            p.add_argument("--stale-days", type=int, default=365)
    p = sub.add_parser("diff")
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "diff":
        result = diff(json.loads(args.before.read_text(encoding="utf-8-sig")),
                      json.loads(args.after.read_text(encoding="utf-8-sig")))
    elif args.command in ("snapshot", "inventory"):
        result = snapshot(args.root)
        if args.command == "inventory":
            for files in result["entries"].values():
                for record in files.values():
                    record.pop("text", None)
    else:
        paths, issues = discover(args.root)
        entries = [audit_one(p, args.validator, args.stale_days) for p in paths]
        for entry in entries:
            for record in entry["files"].values():
                record.pop("text", None)
        result = dict(schema_version=1, roots=args.root, entries=entries, findings=issues, overlaps=overlaps(entries))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Completion is not a health pass: consumers must inspect findings.
    return 0

if __name__ == "__main__":
    sys.exit(main())
