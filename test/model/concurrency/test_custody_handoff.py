"""Regression coverage for serialized resource-custody handoff."""

import threading

from navigate.model.concurrency.concurrency_tools import _Custody, _WaitingList


def test_waiter_does_not_unlock_during_owner_handoff() -> None:
    """Keep a waiter from releasing a lock its predecessor is handing over."""
    resource = _WaitingList()
    owner = _Custody()
    owner.switch_from(None, resource)
    waiter = _Custody()
    waiter.switch_from(None, resource, wait=False)

    owner_removed = threading.Event()
    waiter_checked = threading.Event()
    handoff_done = threading.Event()
    permission_slip = waiter.permission_slip
    errors: list[BaseException] = []

    class PausedQueue(list):
        def pop(self, index: int = -1) -> _Custody:
            value = super().pop(index)
            if value is owner:
                owner_removed.set()
                # Expose the interval between removing the previous owner and
                # releasing the next waiter's permission slip. A synchronized
                # waiter cannot inspect the slip until this handoff finishes.
                waiter_checked.wait(0.5)
            return value

    class ObservedSlip:
        def locked(self) -> bool:
            locked = permission_slip.locked()
            if locked:
                waiter_checked.set()
                if not handoff_done.wait(2):
                    raise TimeoutError("Owner did not finish the handoff")
            return locked

        def release(self) -> None:
            permission_slip.release()

        def acquire(self) -> bool:
            if not permission_slip.acquire(timeout=2):
                raise TimeoutError("Waiter did not receive custody")
            return True

    resource.waiting_list = PausedQueue(resource.waiting_list)
    waiter.permission_slip = ObservedSlip()

    def handoff() -> None:
        try:
            owner.switch_from(resource, None)
        except BaseException as error:
            errors.append(error)
        finally:
            handoff_done.set()

    def wait_for_custody() -> None:
        try:
            waiter._wait_in_line()
        except BaseException as error:
            errors.append(error)

    previous_owner = threading.Thread(target=handoff, daemon=True)
    next_owner = threading.Thread(target=wait_for_custody, daemon=True)
    previous_owner.start()
    assert owner_removed.wait(2)
    next_owner.start()
    previous_owner.join(3)
    next_owner.join(3)

    assert not previous_owner.is_alive()
    assert not next_owner.is_alive()
    assert errors == []
    assert waiter.has_custody
    assert permission_slip.locked()
    assert resource.waiting_list == [waiter]
    waiter.release()
