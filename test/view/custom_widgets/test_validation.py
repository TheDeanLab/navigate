import os
import random
import tkinter as tk

import pytest

from aslm.view.custom_widgets.validation import ValidatedEntry

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


# @pytest.fixture
# def tk_root():
#     root = tk.Tk()
#     yield root
#     root.destroy()


@pytest.fixture
def entry(tk_root):
    entry = ValidatedEntry(tk_root, textvariable=tk.DoubleVar())

    return entry


# TODO: Figure out why this doesn't work in GitHub Actions.
#       entry.undo_history.pop() returns an empty list and entry.get() returns ''
#       in GitHub Actions, but not locally.
@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_add_history(entry):
    # TODO: Why does this not work with textvariable=tk.StringVar()??
    entry.set(42.0)
    entry.add_history(0)
    assert entry.undo_history.pop() == "42.0"


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_undo(entry):
    # base case
    entry.set(42.0)
    entry.add_history(0)
    entry.undo(0)
    assert entry.get() == "42.0"

    # regular undo
    entry.set(42.0)
    entry.add_history(0)
    entry.set(43.0)
    entry.add_history(0)
    entry.undo(0)
    assert entry.get() == "42.0"
    assert entry.redo_history.pop() == "43.0"


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_redo(entry):
    entry.set(42.0)
    entry.add_history(0)
    entry.set(43.0)
    entry.add_history(0)
    entry.undo(0)
    assert entry.get() == "42.0"
    entry.redo(0)
    assert entry.get() == "43.0"
    assert entry.undo_history == ["42.0", "43.0"]


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_undo_redo(entry):
    # Random number of entries
    vals = [random.randint(1, 100) for _ in range(random.randint(3, 5))]
    for val in vals:
        entry.set(val)
        entry.add_history(0)

    n_tries = random.randint(1, 10)
    for _ in range(n_tries):
        entry.undo(0)
        assert entry.redo_history == [str(vals[-1])]
        assert entry.get() == str(vals[-2])
        assert entry.undo_history == [str(vals[-3])]
        entry.redo(0)
        assert entry.get() == str(vals[-1])
        assert entry.undo_history == [str(x) for x in vals[-3:]]
        assert entry.redo_history == []


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_validate_undo(entry):
    entry.set(42.0)
    entry.add_history(0)
    entry.set("")
    entry._validate("", "", "", "focusout", "-1", "-1")
    assert entry.get() == "42.0"
