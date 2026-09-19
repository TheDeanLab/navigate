# PR #1240 Feature Editor Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Repair drag ordering, feature-list persistence ownership, and advanced-function default handling in PR #1240.

**Architecture:** Preserve the existing feature payload and token-stream model, but compute reorder changes from stable old identities and commit the remapped representations together. Resolve feature-list persistence through the existing sequence records, restrict the editor to YAML-owned records, and derive the default advanced-function option directly from the saved mapping.

**Tech Stack:** Python 3.9, Tkinter controllers, pytest, unittest.mock, Black 22.10.0, Ruff 0.0.191.

## Global Constraints

- Base all work on PR #1240 head ``5ec7a2ecfe121960e01f2617c72fef64f552081d``.
- Do not modify or push the contributor's remote branch without separate authorization.
- Use ``PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts=''`` and verify imports resolve to this worktree.
- Do not open Navigate GUI windows on the active macOS desktop.
- Keep imported and plugin feature-list source files immutable.
- Add no new public API; all new helpers are private controller implementation details.

---

### Task 1: Make feature reordering atomic

**Files:**
- Modify: `src/navigate/controller/sub_controllers/features_popup.py:1372-1395`
- Test: `test/controller/sub_controllers/test_features_popup.py`

**Interfaces:**
- Consumes: ``FeatureListGraphController.features``, ``feature_structure``, and insertion-slot indexes returned by ``index_at``.
- Produces: ``move_feature(old_index: int, new_index: int) -> None`` with synchronized visual and serialized order.

- [x] **Step 1: Add failing tests for interior rightward moves and group boundaries**

Add feature-name helpers and tests equivalent to:

```python
def test_move_feature_right_to_interior_slot_changes_serialized_order(graph_controller):
    graph_controller.features = [
        {"name": feature_related_functions.Snap},
        {"name": feature_related_functions.StackPause},
        {"name": feature_related_functions.WaitToContinue},
    ]
    graph_controller.feature_structure = [0, 1, 2]

    graph_controller.move_feature(0, 2)

    assert feature_names(graph_controller) == ["StackPause", "Snap", "WaitToContinue"]
    assert graph_controller.feature_structure == [0, 1, 2]
    assert serialized_feature_names(graph_controller) == ["StackPause", "Snap", "WaitToContinue"]


def test_move_feature_out_of_group_preserves_other_membership(graph_controller):
    graph_controller.features = make_three_features()
    graph_controller.feature_structure = ["(", 0, 1, ")", 2]

    graph_controller.move_feature(1, 3)

    assert feature_names(graph_controller) == ["Snap", "WaitToContinue", "StackPause"]
    assert graph_controller.feature_structure == ["(", 0, ")", 1, 2]
```

- [x] **Step 2: Run the new tests and verify RED**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/controller/sub_controllers/test_features_popup.py -v
```

Expected: the interior-rightward test fails because serialization retains the original order; the grouped move exposes incorrect membership or indexes.

- [x] **Step 3: Implement stable-identity reorder logic**

Replace the coupled mutation with logic equivalent to:

```python
old_order = list(range(len(self.features)))
moved_identity = old_order.pop(old_index)
destination = new_index - 1 if new_index > old_index else new_index
if destination == old_index:
    return
old_order.insert(destination, moved_identity)

new_structure = list(self.feature_structure)
new_structure.remove(moved_identity)
successor = old_order[destination + 1] if destination + 1 < len(old_order) else None
if successor is None:
    new_structure.append(moved_identity)
else:
    new_structure.insert(new_structure.index(successor), moved_identity)

new_features = [self.features[identity] for identity in old_order]
new_index_by_identity = {
    identity: index for index, identity in enumerate(old_order)
}
new_structure = [
    new_index_by_identity[token] if type(token) is int else token
    for token in new_structure
]
self.features = new_features
self.feature_structure = new_structure
```

Clamp invalid insertion slots only if existing callers can supply them; do not broaden behavior otherwise.

- [x] **Step 4: Run reorder and conversion tests and verify GREEN**

Run the controller test file and `test/model/features/test_feature_related_functions.py`. Confirm every feature index appears once and grouping remains balanced in the new cases.

### Task 2: Enforce feature-list persistence ownership

**Files:**
- Modify: `src/navigate/controller/sub_controllers/menus.py:1252-1273`
- Modify: `src/navigate/controller/sub_controllers/features_popup.py:150-180`
- Test: `test/controller/sub_controllers/test_menus_additional.py`
- Test: `test/controller/sub_controllers/test_features_popup.py`

**Interfaces:**
- Produces: ``MenuController._get_custom_feature_list_record(feature_id: int) -> tuple[dict, str] | tuple[None, None]`` returning the loaded record and its exact YAML path.
- Produces: an internal ``persist_feature_list_edits: bool = False`` popup-controller mode selected only by the Edit menu.
- Consumes: the resolver from both menu-entry validation and persistent Confirm-time validation; acquisition configuration keeps the runtime-only default.

- [x] **Step 1: Add failing menu tests for internal and imported records**

Test that an internal record opens the editor, while a record with non-null ``module_name`` shows an error and creates no popup/controller. Mock ``load_yaml_file`` by path and return a sequence entry containing an intentionally non-name-derived ``yaml_file_name``.

- [x] **Step 2: Add failing Confirm-time tests**

Construct ``FeaturePopupController`` without Tk. Assert that an imported record and a missing record call neither ``save_yaml_file`` nor ``parent_controller.execute`` and leave the popup open. Assert that an internal record saves to the exact sequence filename before executing ``("load_feature", feature_id, content)``.

- [x] **Step 3: Run the new persistence tests and verify RED**

Run the two controller test files. Expected: imported records currently open and perform runtime-only mutation; exact sequence filenames are not honored.

- [x] **Step 4: Implement one private record resolver and fail-closed entry validation**

Load ``__sequence.yml``, calculate ``record_index = feature_id - system_feature_list_count``, validate bounds and required ``yaml_file_name``, and load the record from that exact filename. In ``edit_feature_list``, reject non-null ``module_name`` with a clear source-ownership message before closing any existing editor.

- [x] **Step 5: Revalidate before saving and persist before runtime mutation**

In ``update_feature_list``, call the resolver again. Return with an error for missing or non-editable records. Save the internal YAML using the record's exact filename, then execute the runtime update, set the acquisition flag, close child popups, and dismiss the window.

- [x] **Step 6: Run menu, popup, and model tests and verify GREEN**

Run both controller test files plus `test/model/test_model.py -k feature_list`.

### Task 3: Normalize the advanced-function default

**Files:**
- Modify: `src/navigate/controller/sub_controllers/feature_advanced_setting.py:180-200`
- Test: `test/controller/sub_controllers/test_feature_advanced_setting.py`

**Interfaces:**
- Produces: YAML argument mappings that always contain ``"None": None`` when at least one valid row exists.

- [x] **Step 1: Add failing tests for a custom function with a None value and an explicit None row**

Assert that ``{"custom_function": None, "None": None}`` is saved for a custom name whose value is ``"None"``. Assert that an explicit ``("None", "None")`` row normalizes to ``{"None": None}``.

- [x] **Step 2: Run the test file and verify RED**

Expected: the custom-None test fails because the separate default key is absent.

- [x] **Step 3: Replace the boolean flag with mapping normalization**

Collect valid rows as before. After each argument's rows, if its mapping is non-empty, assign ``feature_parameter_config[arg_name]["None"] = None``. Preserve invalid-function warning behavior and omit empty mappings.

- [x] **Step 4: Run the advanced-setting tests and verify GREEN**

Run `test/controller/sub_controllers/test_feature_advanced_setting.py -v`.

### Task 4: Format and verify the integrated change

**Files:**
- Modify mechanically: all changed Python files from Tasks 1-3.

**Interfaces:**
- Consumes: completed behavior changes and tests.
- Produces: repository-formatted, locally validated patch.

- [x] **Step 1: Run pinned formatters**

Run Black 22.10.0 on changed Python files, followed by Ruff 0.0.191 with ``--fix`` only for safe lint fixes. Review the resulting diff to ensure formatting does not alter unrelated files.

Final-diff note: whole-file Black and Ruff exposed pre-existing formatting plus
``E501``/``F841`` violations in the PR files. Formatter-only and unrelated cleanup
was removed from the patch. The final check uses Black on newly added clean files,
Ruff on every changed file while ignoring only those known baseline categories, and
``git diff --check`` on the complete patch.

- [x] **Step 2: Run the focused integrated suite**

Run the three controller test files, feature conversion tests, and model feature-list tests with ``PYTHONPATH=src``.

- [x] **Step 3: Run nearby controller tests**

Run the complete `test/controller/sub_controllers` scope. If a failure is unrelated, reproduce it at the untouched PR head before classification.

- [x] **Step 4: Run repository checks**

Run pinned Black ``--check``, pinned Ruff, and ``git diff --check`` on the changed files. Run the broader pytest suite if the environment remains suitable; otherwise rely on the focused local suite and disclose that full CI is pending.

The fresh non-hardware suite passed with only the Java-dependent OME XML validator
deselected after an otherwise complete run proved that this host has no Java runtime.

- [x] **Step 5: Review the final diff and commit locally**

Confirm only the approved files and planning artifacts changed. Commit with a body summarizing the three defects, the stable-identity reuse decision, the source-ownership boundary, and the validation performed. Do not push.
