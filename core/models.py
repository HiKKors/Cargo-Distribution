from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AxleGroup:
    name: str
    position: float
    empty_weight: float
    max_load_per_axle: float
    axles_in_group: int = 1

    def __post_init__(self):
        if self.axles_in_group < 1:
            raise ValueError(f"Количество осей в группе должно быть >= 1. Получено: {self.axles_in_group}")

@dataclass
class Truck:
    name: str
    max_total_weight: float
    axle_groups: List[AxleGroup]
    body_length: float = 6.0
    body_start_offset: float = 1.0  # Отступ кузова от передней оси (0.0)

    @property
    def empty_total_weight(self) -> float:
        return sum(group.empty_weight for group in self.axle_groups)

@dataclass
class Cargo:
    name: str
    weight: float
    length: float = 0.0
    position: Optional[float] = None

    def __post_init__(self):
        if self.weight <= 0:
            raise ValueError("Вес груза должен быть больше нуля.")
        if self.length <= 0:
            raise ValueError("Длина груза должна быть больше нуля.")

@dataclass
class AxleGroupResult:
    group: AxleGroup
    total_load: float
    load_per_axle: float
    is_overloaded: bool
    is_lifted: bool

@dataclass
class CalculateResult:
    axle_results: List[AxleGroupResult]
    total_weight: float
    is_total_overloaded: bool
    critical_error: Optional[str] = None