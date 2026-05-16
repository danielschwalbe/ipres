"""Simple data class for specifying super majority margin."""
from dataclasses import dataclass
from enum import Enum


class MarginUnit(Enum):
    """Unit for specifying the super majority margin."""
    PERCENT = 1  # pragma: no mutate
    SEATS = 2  # pragma: no mutate


@dataclass(frozen=True)
class SuperMajorityMargin:
    """Specifies the margin for a super majority, either in percent or seats.

    The super majority is calculated as 50% + margin.

    Examples:
        SuperMajorityMargin(5, MarginUnit.PERCENT)  # 55% majority
        SuperMajorityMargin(10, MarginUnit.SEATS)   # 50% + 10 seats
    """
    value: float
    unit: MarginUnit

    def __post_init__(self):
        if self.unit == MarginUnit.PERCENT:
            if not (0 <= self.value <= 100):
                raise ValueError(f"Percent margin must be in [0, 100], got {self.value}")  # pragma: no mutate
        else:  # SEATS
            if self.value < 0:
                raise ValueError(f"Seat margin must be non-negative, got {self.value}")  # pragma: no mutate
            if not isinstance(self.value, int) and not self.value.is_integer():
                raise ValueError(f"Seat margin must be an integer, got {self.value}")  # pragma: no mutate
