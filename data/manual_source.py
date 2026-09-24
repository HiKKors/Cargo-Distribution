from typing import List
from core.interfaces import CargoDataSource
from core.models import Cargo


class ManualCargoDataSource(CargoDataSource):
    """
    Хранит список грузов в оперативной памяти.
    Позже рядом ляжет AtiSuCargoDataSource, который будет делать HTTP-запросы.
    """
    def __init__(self):
        self._cargos: List[Cargo] = []

    def get_cargos(self) -> List[Cargo]:
        return self._cargos

    def add_cargo(self, cargo: Cargo):
        self._cargos.append(cargo)

    def remove_cargo(self, index: int):
        if 0 <= index < len(self._cargos):
            self._cargos.pop(index)

    def clear(self):
        self._cargos.clear()

    def replace_all(self, cargos: List[Cargo]):
        """Полностью заменяет список грузов (используется после авто-расстановки)."""
        self._cargos = list(cargos)