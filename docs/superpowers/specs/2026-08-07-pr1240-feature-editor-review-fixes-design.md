# PR #1240 Feature Editor Review Fixes Design

## Goal

Correct the three review defects in PR #1240 without redesigning the feature-list
editor: make drag reordering deterministic, prevent unsupported imported/plugin lists
from appearing editable, and always preserve the default ``None`` advanced-function
choice.

## Feature graph model

``FeatureListGraphController`` keeps feature payloads in ``features`` and grouping
syntax in ``feature_structure``. Reordering must update both representations as one
operation. Existing integer indexes are treated as stable identities while computing
the move. The moved identity is removed from the structure and inserted before its
new successor, or appended after all closing group delimiters when it has no
successor. The feature payload list is then reordered once and every integer token is
remapped to its new payload index.

The resulting structure must contain every feature index exactly once, preserve
balanced grouping delimiters, and serialize features in visual order. Releasing a
node inside a group joins that group; releasing it after the group moves it outside.

## Persistence ownership

The visual editor owns only feature lists saved directly in Navigate YAML, identified
by ``module_name: null``. Python-imported and plugin-provided feature lists remain
owned by their source modules because the editor cannot safely round-trip arbitrary
external feature classes or write Python source.

``MenuController`` will resolve a custom feature ID through ``__sequence.yml`` and
the record's exact ``yaml_file_name``. The Edit action will reject missing, malformed,
imported, and plugin records before opening a popup. The update path will repeat the
same validation before writing, save the authoritative YAML first, and only then
update the runtime model and close the popup. This prevents runtime-only edits from
appearing persistent.

The popup controller will receive an internal ``persist_feature_list_edits`` flag
only from the Edit menu. Its default remains false so the existing pre-acquisition
configuration popup can continue applying temporary runtime changes to built-in
feature lists without requiring a custom YAML record.

An editable-copy workflow is intentionally excluded. It can be added later as an
explicit action without weakening the ownership boundary.

## Advanced-function default

The saved mapping itself is the source of truth. After valid rows are collected, any
non-empty argument mapping will be normalized with ``mapping["None"] = None``. A
custom function whose value is ``None`` therefore does not suppress the separate
default option. Empty or wholly invalid argument mappings remain absent.

## Error handling

- System feature lists remain non-editable.
- Missing or invalid sequence records show a feature-list error and perform no write
  or runtime mutation.
- Imported/plugin records show that they are source-controlled and cannot be edited
  in the visual editor.
- Save validation occurs again on Confirm so external changes between opening and
  saving fail closed.

## Validation

Regression tests will cover interior and boundary moves in both directions, group
entry/exit, editable and imported persistence paths, exact sequence filenames,
missing records, and all relevant ``None`` mappings. Validation uses the Navigate
Python environment with ``PYTHONPATH=src``, pinned Black 22.10.0, pinned Ruff
0.0.191, ``git diff --check``, focused tests, nearby consumer tests, and the broader
test suite justified by the GUI/model scope.
