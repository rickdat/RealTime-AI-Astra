from abc import ABC, abstractmethod


class ThreatIntelligenceSystem(ABC):
    @abstractmethod
    def check_entity(self, entity_type, entity_value):
        pass
