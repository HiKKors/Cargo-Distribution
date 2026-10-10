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
            raise ValueError(
                f"Количество осей в группе должно быть >= 1. Получено: {self.axles_in_group}"
            )


@dataclass
class Truck:
    name: str
    max_total_weight: float
    axle_groups: List[AxleGroup]
    body_length: float = 6.0
    body_width: float = 2.4     # внутренняя ширина кузова, м
    body_height: float = 2.0    # внутренняя высота кузова, м
    body_start_offset: float = 1.0  # отступ передней стенки кузова от передней оси

    @property
    def empty_total_weight(self) -> float:
        return sum(group.empty_weight for group in self.axle_groups)


@dataclass
class Cargo:
    name: str
    weight: float
    length: float = 0.0           # длина груза, м (вдоль оси X)
    width: float = 0.0            # ширина груза, м (поперёк, ось Y)
    height: float = 0.0           # высота груза, м (вертикаль, ось Z)
    order_id: int = 0             # очередность груза
    position: Optional[float] = None           # центр по длине кузова (X), м
    lateral_position: Optional[float] = None   # центр по ширине кузова (Y), м

    def __post_init__(self):
        if self.weight <= 0:
            raise ValueError("Вес груза должен быть больше нуля.")
        if self.length <= 0:
            raise ValueError("Длина груза должна быть больше нуля.")
        if self.width <= 0:
            raise ValueError("Ширина груза должна быть больше нуля.")
        if self.height <= 0:
            raise ValueError("Высота груза должна быть больше нуля.")


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