import logging
from SocAI.models.threat_intelligence.threat_intelligence_system import ThreatIntelligenceSystem


class ThreatIntelligenceChecker:
    def __init__(self, threat_intelligence_system: ThreatIntelligenceSystem):
        self.threat_intelligence_system = threat_intelligence_system

    def check_in_threat_intelligence(self, entities):
        blacklist = []
        for entity_type, entity_values in entities.items():
            for entity in entity_values:
                result = self.threat_intelligence_system.check_entity(entity_type, entity)
                if result:
                    blacklist.append(result)
        return blacklist
