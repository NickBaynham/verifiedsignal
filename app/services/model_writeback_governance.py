"""Verification state transitions for model write-back artifacts."""

from __future__ import annotations

from app.domain.model_writeback_constants import VERIFICATION_STATES

_ALLOWED: dict[str, frozenset[str]] = {
    "proposed": frozenset({"accepted", "rejected", "superseded"}),
    "accepted": frozenset({"superseded"}),
    "rejected": frozenset(),
    "auto_ingested": frozenset({"accepted", "superseded"}),
    "superseded": frozenset(),
}


def assert_valid_verification_state(state: str) -> None:
    if state not in VERIFICATION_STATES:
        msg = f"invalid verification_state: {state!r}"
        raise ValueError(msg)


def can_transition(from_state: str, to_state: str) -> bool:
    assert_valid_verification_state(from_state)
    assert_valid_verification_state(to_state)
    if from_state == to_state:
        return True
    return to_state in _ALLOWED.get(from_state, frozenset())


def assert_transition_allowed(from_state: str, to_state: str) -> None:
    if can_transition(from_state, to_state):
        return
    msg = f"transition not allowed: {from_state!r} -> {to_state!r}"
    raise ValueError(msg)
