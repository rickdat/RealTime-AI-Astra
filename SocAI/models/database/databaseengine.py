import logging

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


class CassandraDBEngine:
    def __init__(self, secure_connect_bundle, token, keyspace):
        self.secure_connect_bundle_path = secure_connect_bundle
        self.username = 'token'
        self.password = token
        self.keyspace = keyspace
        self.session = self.get_cql_session()

    def get_cql_session(self):
        try:
            cluster = Cluster(
                cloud={"secure_connect_bundle": self.secure_connect_bundle_path},
                auth_provider=PlainTextAuthProvider(
                    self.username,
                    self.password,
                ),
            )
            session = cluster.connect()
            return session
        except Exception as e:
            logging.error(f"An error occurred while connecting to the database: {str(e)}")
            return None

    def disconnect(self):
        try:
            self.session.shutdown()
        except Exception as e:
            logging.error(f"An error occurred while disconnecting: {str(e)}")