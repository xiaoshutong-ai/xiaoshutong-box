from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog  # noqa: E402


class CatalogVisibilityTest(unittest.TestCase):
    def test_internal_studyroom_is_excluded_from_public_catalog_only(self):
        all_manifests = catalog.load_manifests()
        published = catalog.build_catalog()
        self.assertEqual(len(all_manifests), 9)
        self.assertEqual(len(published["apps"]), 8)
        self.assertEqual(sum(d["package"] == "com.jay.studyroom" for _, d, _ in all_manifests), 1)
        self.assertFalse(any(a["package"] == "com.jay.studyroom" for a in published["apps"]))
        self.assertEqual(
            published["updatedAt"],
            next(d["catalogUpdatedAt"] for _, d, _ in all_manifests if d["package"] == "com.jay.studyroom"),
        )

        previous = json.loads(subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "HEAD:versions.json"], text=True, encoding="utf-8"
        ))
        visible_before = [a for a in previous["apps"] if a["package"] != "com.jay.studyroom"]
        self.assertEqual(published["apps"], visible_before)
        self.assertEqual(len(previous["apps"]) - len(published["apps"]), 1)

    def test_non_boolean_visibility_is_rejected(self):
        actual_reader = catalog.read_json

        def invalid_reader(path):
            data = actual_reader(path)
            if data.get("package") == "com.jay.studyroom":
                return {**data, "publicVisible": "false"}
            return data

        with patch.object(catalog, "read_json", side_effect=invalid_reader):
            with self.assertRaisesRegex(catalog.CatalogError, "publicVisible must be a boolean"):
                catalog.load_manifests()


if __name__ == "__main__":
    unittest.main()
