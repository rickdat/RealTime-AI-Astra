import logging

from cassandra.query import SimpleStatement


class CassandraDBOperations:
    def __init__(self, db_engine, table):
        self.session = db_engine.session
        self.keyspace = db_engine.keyspace
        self.table = table

    def create_table(self):
        try:
            table_creation_query = SimpleStatement(f"""
                    CREATE TABLE IF NOT EXISTS {self.keyspace}.{self.table} (
                        id TEXT PRIMARY KEY,
                        alert_body TEXT,
                        domain_list LIST<text>,
                        ip_list LIST<text>,
                        email_list LIST<text>,
                        evaluation TEXT,
                        reasoning TEXT,
                        next_steps TEXT,
                        alert_body_vector VECTOR<FLOAT, 1536>
                    );
                    """)

            self.session.execute(table_creation_query)

            index_creation_query = SimpleStatement(f"""
                    CREATE CUSTOM INDEX IF NOT EXISTS ann_index ON {self.keyspace}.{self.table}(alert_body_vector) USING 'StorageAttachedIndex';""")

            self.session.execute(index_creation_query)

        except Exception as e:
            logging.error(f"An error occurred while creating the table: {str(e)}")

    def insert_data(self, fields, values):
        try:
            placeholders = ', '.join(['%s' for _ in values])
            query = SimpleStatement(f"INSERT INTO {self.keyspace}.{self.table} ({', '.join(fields)}) VALUES ({placeholders});")
            self.session.execute(query, values)
        except Exception as e:
            logging.error(f"An error occurred while inserting data: {str(e)}")

    def query_vector(self, value):
        try:
            statement = f'SELECT * FROM {self.keyspace}.{self.table} ORDER BY alert_body_vector ANN OF %s LIMIT 1000;'
            result_set = self.session.execute(statement, (value,))
            return result_set.all()
        except Exception as e:
            logging.error(f"An error occurred while querying data: {str(e)}")
            return None
