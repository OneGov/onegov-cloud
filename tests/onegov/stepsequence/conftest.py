from __future__ import annotations

import pytest
import onegov.stepsequence
from onegov.stepsequence.core import StepSequenceRegistry


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope='function')
def sequences(
    monkeypatch: pytest.MonkeyPatch
) -> Iterator[StepSequenceRegistry]:
    sequences = StepSequenceRegistry()
    monkeypatch.setattr(onegov.stepsequence, 'step_sequences', sequences)
    monkeypatch.setattr(
        'onegov.stepsequence.extension.step_sequences',
        sequences
    )
    yield sequences
