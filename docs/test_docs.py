import re
import unittest
import subprocess
import os
import pytest


@pytest.mark.skip(reason="Skipping Sphinx build test.")
class TestDocs(unittest.TestCase):
    def setUp(self):
        os.chdir(os.path.join(os.getcwd(), "docs"))

    def test_sphinx_build(self):
        cmd = [
            "make",
            "linkcheck",
        ]

        # Run the build, and print any results.
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)

        # Check that no links are broken.
        assert result.returncode == 0, "Broken links found in Sphinx documentation!"

        # Check that all images are found.
        missing_image_pattern = re.compile(
            r"WARNING: image file not readable", re.IGNORECASE
        )
        match = missing_image_pattern.search(result.stderr)
        self.assertIsNone(
            match,
            "There are missing images in the documentation! "
            "Check Sphinx warnings above.",
        )


if __name__ == "__main__":
    unittest.main()
