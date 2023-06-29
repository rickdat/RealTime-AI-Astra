# main.py
import os

from threading import Thread
import logging

import uvicorn
from fastapi import FastAPI

from SocAI.models.threat_intelligence.threat_intelligence_checker import ThreatIntelligenceChecker
from SocAI.models.threat_intelligence.threat_winds import ThreatWinds
from SocAI.models.database.databaseengine import CassandraDBEngine
from SocAI.models.database.cassandradboperations import CassandraDBOperations

from utils.queue_manager import QueueSystem
from SocAI.models.chatgpt.chatgpt import ChatGPT
from SocAI.controllers.queue_worker import QueueWorker

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NoAPIKeyFoundError(Exception):
    pass


fastapi_instance = FastAPI()
queue = QueueSystem(path="queue.db")


@fastapi_instance.post("/process")
async def process(data: str):
    try:
        queue.enqueue(data)
        return {"message": "Items added to queue."}
    except Exception as e:
        logging.error(f"Error occurred during queue insertion: {str(e)}")


@fastapi_instance.get("/ping")
def ping():
    return "OK"


# Main application class
class Application:
    """Main application class."""

    def __init__(self, db_engine: CassandraDBEngine, chatgpt: ChatGPT, threat_checker: ThreatIntelligenceChecker):
        self.server_thread = None
        self.queue_worker = None
        self.cassandra_db = db_engine
        self.cassandra_operations = CassandraDBOperations(db_engine, os.getenv("TABLE_NAME"))
        self.chatgpt_instance = chatgpt
        self.threat_intelligence_system = threat_checker

    def start(self,):
        logger.info("Starting application...")
        try:
            self.cassandra_operations.create_table()
            self.queue_worker = QueueWorker(queue, self.cassandra_operations, self.threat_intelligence_system,
                                            self.chatgpt_instance)
            self.queue_worker.start()

            self.server_thread = Thread(target=uvicorn.run, args=(fastapi_instance,), kwargs={"host": "0.0.0.0", "port": 8080})
            self.server_thread.start()

        except Exception as e:
            logging.error(f"Error: {str(e)}")


# Instantiate and run the application with the required dependencies
if __name__ == "__main__":
    try:
        db = CassandraDBEngine(secure_connect_bundle=os.getenv('SECURE_CONNECT_BUNDLE_PATH'),
                               token=os.getenv("CASSANDRA_DATABASE_TOKEN"),
                               keyspace=os.getenv('CASSANDRA_DATABASE_KEYSPACE'))

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise NoAPIKeyFoundError

        chatgpt = ChatGPT(openai_api_key)

        threat_intelligence_system = ThreatWinds(os.getenv('THREATWINDS_API_KEY'), os.getenv('THREATWINDS_API_SECRET'))
        threat_checker = ThreatIntelligenceChecker(threat_intelligence_system)

        app = Application(db, chatgpt, threat_checker)
        app.start()

    except NoAPIKeyFoundError:
        logging.error("No API key found in the database.")

    except Exception as e:
        logging.error(f"Error: {str(e)}")