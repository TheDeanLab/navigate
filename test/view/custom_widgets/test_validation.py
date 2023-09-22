import random
import tkinter as tk

import pytest

from aslm.view.custom_widgets.validation import ValidatedEntry


@pytest.fixture
def entry():
    root = tk.Tk()

    var = tk.DoubleVar()
    entry = ValidatedEntry(root, textvariable=var)
    root.update()

    yield entry
    root.destroy()


def test_add_history(entry):
    # TODO: Why does this not work with textvariable=tk.StringVar()??
    entry.set(42.0)
    entry.add_history(0)
    assert entry.undo_history.pop() == "42.0"


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


def test_validate_undo(entry):
    entry.set(42.0)
    entry.add_history(0)
    entry.set("")
    entry._validate("", "", "", "focusout", "-1", "-1")
    assert entry.get() == "42.0"
