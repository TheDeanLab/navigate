Bio-Formats test download reliability
====================================

Goal and design
---------------
Keep OME-XML validation enabled while making its pinned Bio-Formats 8.1.0
archive resilient to transient download failures. Cache only checksum-verified
archives; extract each test into pytest's temporary directory. Retry acquisition
three times with a 30-second socket timeout and 1/2-second backoff. Preserve a
hard failure when acquisition is exhausted or XML validation fails.

Reuse analysis
--------------
Searched source, tests, workflows, download/retry/cache names and synonyms.
The only archive downloader is the direct urlretrieve call in
``test/model/metadata_sources/test_ome_tiff_metadata.py``.
Reuse pytest's cache directory and GitHub Actions cache; use standard-library
urllib, hashlib, tempfile and pathlib in a private test helper. No application
API, dependencies, or microscope behavior changes. Avoid a general downloader.

Plan
----
1. Add focused tests against a local HTTP server for truncation, HTTP failure,
   corrupt cache, warm cache without network, checksum mismatch, exhaustion,
   and cleanup of partial files. Verify they fail before implementing.
2. Implement the private cached downloader and wire it into the existing
   metadata test. Use temporary extraction and checked subprocess execution.
3. Persist only the Bio-Formats pytest cache directory in all three CI jobs,
   with a key derived from the helper (including version and checksum).
4. Run focused regressions, real archive/XML validation on cold and warm cache,
   the broadest practical suite with PYTHONPATH=src, Black, Ruff, pinned hooks,
   and git diff --check. Independently review the final diff.
5. Commit with reuse analysis, push the new branch, open a PR against develop,
   assign annie-xd-wang, attach it to this chat, and verify the published state.

Review focus
------------
- Failed downloads never become valid cache entries.
- Warm caches require digest verification before avoiding network.
- Permanent network/digest failures stay visible after three attempts.
- Extraction and validator errors remain hard failures.
- Linux/macOS and Windows launchers retain existing validation behavior.

Verification record
-------------------
- Nine download regressions failed before implementation and passed afterward.
- Real Bio-Formats 8.1.0 archive retrieved from its official HTTPS URL, SHA-256
  pinned, and ZIP integrity checked.
- Cold-cache download plus real XML validation passed; the complete metadata
  suite then passed with the warm cache (35 tests).
- Black, Ruff, repository-pinned pre-commit hooks, workflow cache wiring checks,
  Python 3.9 syntax checks, and git diff --check passed.
- Focused type checking reported zero errors (four advisory warnings).
- Independent review found no actionable defects; native Windows execution
  remains for the PR CI jobs.
