import logging
import time
import json
from threading import Thread

from opensearchpy.exceptions import NotFoundError

from SocAI.models.chatgpt.chatgpt import ChatGPT, ChatGPTResponseParsingError
from SocAI.utils.formatter import summarize
from SocAI.models.database.cassandradboperations import CassandraDBOperations

from SocAI.models.threat_intelligence.threat_intelligence_checker import ThreatIntelligenceChecker
from SocAI.utils.embedings import create_vector
from SocAI.utils.redactron import extract_sensitive_information


class QueueWorker(Thread):
    """Thread for processing items from the queue."""

    def __init__(self, queue, database: CassandraDBOperations, threatintelligencechecker: ThreatIntelligenceChecker,
                 chatgpt_instance:ChatGPT):
        super().__init__(daemon=True)
        self.queue = queue
        self.database = database
        self.threatintelligencechecker = threatintelligencechecker
        self.chatgpt_instance = chatgpt_instance

    def run(self):
        """Start processing items from the queue."""
        while True:
            try:
                items = self.queue.dequeue(20)
                if items:
                    for item in items:
                        self._process_item(item, self.chatgpt_instance)
                else:
                    time.sleep(10)
            except Exception as e:
                logging.error(f"Error: {str(e)}")

    def _process_item(self, item, chatgpt_instance):
        """Process an item from the queue."""
        try:
            logging.info(f"Processing item: {item[0]}")

            sensitive_information = self._extract_sensitive_information(item[1])

            results_threat_intelligence_search = self._check_threat_intelligence(sensitive_information)

            vector = self._create_vector(item[1])
            vector_count = len(self.database.query_vector(vector))

            prompt, replaces = self._create_prompt(item[1], results_threat_intelligence_search, sensitive_information,
                                                   vector_count)

            chatgpt_dict_format_response = chatgpt_instance.ask(prompt)

            if replaces:
                chatgpt_dict_format_response = self._replace_fake_values(chatgpt_dict_format_response, replaces)

            self._store_data(item, sensitive_information, chatgpt_dict_format_response, vector)

            self.queue.delete_processed([item[0]])
        except (NotFoundError, IndexError, ChatGPTResponseParsingError) as e:
            self.queue.delete_processed([item[0]])
            logging.error(f"Error: The alert cannot be processed. Deleting from the queue.{str(e)}")
        except Exception as e:
            logging.error(f"Error: {str(e)}")

    def _extract_sensitive_information(self, item):
        logging.info(f"Extracting sensitive information")
        return extract_sensitive_information(item)

    def _check_threat_intelligence(self, sensitive_information):
        logging.info(f"Searching for the sensitive information in the Threat Intelligence")
        results = self.threatintelligencechecker.check_in_threat_intelligence(sensitive_information)
        logging.info(f"Was found {len(results)} elements in the ThreatIntelligence Platform")
        return results

    def _create_vector(self, item):
        logging.info('Creating a vector to find similarities')
        return create_vector(item)

    def _create_prompt(self, item, results, sensitive_information, vector_count):
        logging.info(f"Creating the prompt")
        return summarize({'data': item, 'ti_result': results}, sensitive_information, vector_count)

    def _replace_fake_values(self, chatgpt_dict_format_response, replaces):
        logging.info(f"Replacement of fake values by the original ones.")
        chatgpt_string_format_response = json.dumps(chatgpt_dict_format_response)
        for original, fake in replaces.items():
            chatgpt_string_format_response = chatgpt_string_format_response.replace(fake, original)
        return json.loads(chatgpt_string_format_response)

    def _store_data(self, item, sensitive_information, chatgpt_dict_format_response, vector):
        fields = ('id', 'alert_body', 'domain_list', 'ip_list', 'email_list', 'evaluation', 'reasoning', 'next_steps',
                  'alert_body_vector')

        values = (item[0], item[1], sensitive_information['domain'], sensitive_information['ip'],
                  sensitive_information['email'],
                  chatgpt_dict_format_response['classification'],
                  json.dumps(chatgpt_dict_format_response['reasoning']),
                  json.dumps(chatgpt_dict_format_response['next_steps']), vector)

        self.database.insert_data(fields, values)
