import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "changelog.py"


class ChangelogSafetyTests(unittest.TestCase):
    def test_existing_file_is_not_replaced_without_force(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            output = repo / "CHANGELOG.md"
            original = "# Historical releases\n\n## v1.0\nAlready published\n"
            output.write_text(original, encoding="utf-8")
            command = ["python3", str(SCRIPT), "--repo", str(repo)]

            refused = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0, refused.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), original)
            self.assertIn("--force", refused.stderr)

            preview = subprocess.run(command + ["--stdout"], capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), original)

            forced = subprocess.run(command + ["--force"], capture_output=True, text=True)
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertNotEqual(output.read_text(encoding="utf-8"), original)
            self.assertTrue(output.read_text(encoding="utf-8").startswith("# Changelog"))

    def test_breaking_conventional_prefix_is_classified_and_marked(self):
        import sys
        sys.path.insert(0, str(SCRIPT.parent))
        from changelog import categorize

        self.assertEqual(categorize("feat!: replace old API"), ("Added", "**BREAKING:** replace old API"))
        self.assertEqual(categorize("fix!: require a fresh token"), ("Fixed", "**BREAKING:** require a fresh token"))
        self.assertEqual(categorize("feat(ui)!: change layout"), ("Added", "**BREAKING:** change layout"))
        self.assertEqual(categorize("feat: add filter"), ("Added", "add filter"))

    def test_new_changelog_is_created_without_force(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            result = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((repo / "CHANGELOG.md").exists())


if __name__ == "__main__":
    unittest.main()
