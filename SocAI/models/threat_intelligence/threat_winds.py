import logging
import requests
from SocAI.models.threat_intelligence.threat_intelligence_system import ThreatIntelligenceSystem


class ThreatWinds(ThreatIntelligenceSystem):
    def __init__(self, api_key, api_secret):
        super().__init__()
        self.base_url = "https://intelligence.threatwinds.com/api/search/v1/entity"
        self.api_key = api_key
        self.api_secret = api_secret
        self.scale_reputation = {-3: 'Critical',
                                 -2: 'Bad',
                                 -1: 'Poor',
                                 0: 'Neutral',
                                 1: 'Fair',
                                 2: 'Good',
                                 3: 'Great'}

    def check_entity(self, entity_type, entity_value):
        url = self.base_url
        headers = {
            'API-Key': self.api_key,
            'API-Secret': self.api_secret,
            'Content-Type': 'application/json',
            'accept': 'application/json'
        }
        data = {"type": entity_type, "value": entity_value}
        try:
            with requests.Session() as session:
                response = session.post(url, json=data, headers=headers)

                if response.status_code == 200:
                    entity_information = response.json()
                    data = {entity_type: entity_value,
                            'reputation': self.scale_reputation[entity_information['reputation']],
                            'last_report': entity_information['@timestamp'],
                            }
                    if 'tags' in entity_information:
                        data['tags'] = entity_information['tags']

                    return data
                elif response.status_code == 404:
                    return
                else:
                    logging.error(f"Request failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while making a POST request: {e}")
