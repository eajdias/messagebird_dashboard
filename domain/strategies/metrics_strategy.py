from abc import ABC, abstractmethod

from domain.entities.report_data import RawConversationData


class MetricStrategy(ABC):
    @abstractmethod
    def calculate(self, data: RawConversationData) -> float:
        pass
