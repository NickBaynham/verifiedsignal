"""Unit tests: write-back verification transitions."""

from __future__ import annotations

import pytest
from app.services.model_writeback_governance import (
    assert_transition_allowed,
    assert_valid_verification_state,
    can_transition,
)


def test_valid_states() -> None:
    assert_valid_verification_state("proposed")


def test_invalid_state() -> None:
    with pytest.raises(ValueError, match="invalid verification_state"):
        assert_valid_verification_state("draft")


def test_same_state_allowed() -> None:
    assert can_transition("proposed", "proposed") is True


def test_proposed_to_accepted() -> None:
    assert_transition_allowed("proposed", "accepted")


def test_rejected_is_terminal() -> None:
    with pytest.raises(ValueError, match="transition not allowed"):
        assert_transition_allowed("rejected", "accepted")


def test_auto_ingested_to_accepted() -> None:
    assert_transition_allowed("auto_ingested", "accepted")
