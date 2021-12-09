"""
This is the test module with test functions to test the functions in main.py

Each function is tested with some test cases and the return type is tested as well.
"""

from main import *

def test_remove_update_toast() -> None:
    """
    This function is used to test the function remove_update_toast.
    """
    data = remove_update_toast("test_update", "18.45")
    assert data is None, "Test for return type of remove_update_toast: failed"
    assert len(updates) == 0, "Test for proper removal of updates: failed"
