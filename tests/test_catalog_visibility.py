from __future__ import annotations

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
        internal = [d for _, d, _ in all_manifests if d.get("publicVisible", True) is False]

        self.assertEqual([d["package"] for d in internal], ["com.jay.studyroom"])
        expected_public = [d["package"] for _, d, _ in all_manifests if d.get("publicVisible", True)]
        self.assertEqual([app["package"] for app in published["apps"]], expected_public)
        self.assertEqual(len(published["apps"]), len(all_manifests) - len(internal))
        self.assertEqual(
            published["updatedAt"],
            max(
                all_manifests,
                key=lambda item: catalog.parse_time(str(item[1]["catalogUpdatedAt"]), item[0].name),
            )[1]["catalogUpdatedAt"],
        )
        self.assertEqual(published, catalog.read_json(ROOT / "versions.json"))

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
