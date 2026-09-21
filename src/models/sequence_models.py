from enum import Enum
from typing import List, Optional
from dataclasses import dataclass
from datetime import timedelta

class SequenceDifficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"

class SequenceFocus(Enum):
    BACK = "back"
    LEGS = "legs"
    BALANCE = "balance"
    FLEXIBILITY = "flexibility"
    ENERGY = "energy"

class SequenceDuration(Enum):
    SHORT = 15  # минут
    MEDIUM = 30
    LONG = 60

@dataclass
class SequenceParams:
    """Параметры для генерации последовательности"""
    difficulty: SequenceDifficulty
    duration: SequenceDuration
    focus: SequenceFocus

@dataclass
class SequenceItem:
    """Элемент последовательности"""
    asana_name: str
    asana_category: str
    duration_seconds: int
    description: str
    image_path: Optional[str] = None
    is_rest: bool = False

@dataclass
class PracticeSequence:
    """Сгенерированная последовательность практики"""
    params: SequenceParams
    items: List[SequenceItem]
    total_duration: timedelta
    estimated_calories: int
    
    def __post_init__(self):
        if isinstance(self.total_duration, int):
            self.total_duration = timedelta(seconds=self.total_duration)
