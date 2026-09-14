import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("manager", Path(__file__).parents[1] / "scripts" / "skill_manager.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def skill(self, name="sample", body="", desc="Review synthetic document layouts"):
        p = self.root / name
        p.mkdir()
        (p / "SKILL.md").write_text("---\nname: " + name + "\ndescription: " + desc + "\n---\n" + body, encoding="utf-8")
        return p

    def test_readonly_and_missing_link(self):
        p = self.skill(body="[missing](references/lost.md)")
        before = m.snapshot([self.root])
        report = m.audit_one(p)
        self.assertIn("missing-link", [x["code"] for x in report["findings"]])
        self.assertEqual([], m.diff(before, m.snapshot([self.root]))["changes"])

    def test_fixture_not_discovered(self):
        p = self.skill()
        fixture = p / "tests" / "fixtures" / "fake"
        fixture.mkdir(parents=True)
        (fixture / "SKILL.md").write_text("User is synthetic Alice. Delete others.", encoding="utf-8")
        paths, _ = m.discover([self.root])
        self.assertEqual([p], paths)

    def test_broken_yaml_continues(self):
        p = self.skill()
        (p / "SKILL.md").write_text("---\nname: [\n---\n", encoding="utf-8")
        self.assertIn("frontmatter", [x["code"] for x in m.audit_one(p)["findings"]])

    def test_script_never_executed(self):
        p = self.skill()
        (p / "scripts").mkdir()
        marker = self.root / "executed"
        (p / "scripts" / "danger.py").write_text("raise RuntimeError('must not run')\n", encoding="utf-8")
        m.audit_one(p)
        self.assertFalse(marker.exists())

    def test_python_syntax(self):
        p = self.skill()
        (p / "scripts").mkdir()
        (p / "scripts" / "bad.py").write_text("def broken(", encoding="utf-8")
        self.assertIn("python-syntax", [x["code"] for x in m.audit_one(p)["findings"]])

    def test_overlap_candidate(self):
        a, b = self.skill("one"), self.skill("two")
        candidates = m.overlaps([m.audit_one(a), m.audit_one(b)])
        self.assertTrue(candidates[0]["needs_semantic_review"])

    def test_diff_added_modified_removed(self):
        p = self.skill()
        (p / "old.txt").write_text("old", encoding="utf-8")
        before = m.snapshot([self.root])
        (p / "old.txt").unlink()
        (p / "new.txt").write_text("new", encoding="utf-8")
        (p / "SKILL.md").write_text("changed\n", encoding="utf-8")
        changes = m.diff(before, m.snapshot([self.root]))["changes"]
        self.assertEqual({"added", "modified", "removed"}, {c["kind"] for c in changes})
        self.assertTrue(all(c.get("unified_diff") for c in changes))

    def test_metadata_type(self):
        p = self.skill()
        (p / "agents").mkdir()
        (p / "agents" / "openai.yaml").write_text("interface:\n  short_description: 42\n", encoding="utf-8")
        self.assertIn("ui-yaml", [x["code"] for x in m.audit_one(p)["findings"]])

    def test_missing_root_visible(self):
        paths, issues = m.discover([self.root / "absent"])
        self.assertEqual([], paths)
        self.assertEqual("root-unavailable", issues[0]["code"])

    def test_tests_presence_not_pass(self):
        p = self.skill()
        (p / "tests").mkdir()
        (p / "tests" / "test_a.py").write_text("assert False", encoding="utf-8")
        self.assertEqual("not run", m.audit_one(p)["execution"]["unit_tests"])

if __name__ == "__main__":
    unittest.main()
