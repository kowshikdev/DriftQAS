"""A strict sampled-shot ledger; preparation and CPU are recorded separately."""

from dataclasses import dataclass, field


@dataclass
class Budget:
    limit: int
    confirmation_reserve: int
    spent: int = 0
    by_phase: dict[str, int] = field(default_factory=dict)

    @property
    def search_remaining(self) -> int:
        return self.limit - self.confirmation_reserve - self.spent

    def charge(self, requested: int, phase: str) -> None:
        if requested <= 0:
            raise ValueError("Shot charge must be positive")
        maximum = self.limit if phase == "confirmation" else self.limit - self.confirmation_reserve
        if self.spent + requested > maximum:
            raise ValueError("Shot allocation would exceed the budget or confirmation reserve")
        self.spent += requested
        self.by_phase[phase] = self.by_phase.get(phase, 0) + requested
