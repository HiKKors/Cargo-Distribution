from abc import ABC, abstractmethod
from typing import List
from .models import Cargo

class CargoDataSource(ABC):
    """
    Базовый интерфейс для поставки данных о грузах.
    
    Позволяет расчётному модулю и UI не зависеть от того, откуда физически
    пришли данные (ручной ввод в форму на MVP или API ATI.SU в будущем).
    Любой новый источник должен наследоваться от этого класса и реализовывать 
    метод get_cargos.
    """
    
    @abstractmethod
    def get_cargos(self) -> List[Cargo]:
        pass