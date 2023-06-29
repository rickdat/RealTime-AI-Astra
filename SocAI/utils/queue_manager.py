import hashlib
import logging
import sqlite3


class QueueSystem:
    def __init__(self, path):
        """
        Initialize the QueueSystem with the specified SQLite database file.

        Parameters:
        - db_file (str): The path to the SQLite database file.
        """
        self.db_file = path

        self.create_table()

    def create_table(self):
        """
        Create the 'queue' table in the database if it doesn't exist.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Create the 'queue' table if it doesn't exist
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS queue (
                        id TEXT PRIMARY KEY,
                        data TEXT
                    )
                ''')
        except sqlite3.Error as e:
            raise ValueError(f"Error creating table") from e

    def enqueue(self, data):
        """
        Enqueue data into the 'queue' table.

        Parameters:
        - data: The data to be enqueued.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Insert data into the 'queue' table
                conn.execute("INSERT INTO queue (id, data) VALUES (?, ?)",
                             (hashlib.sha256(data.encode()).hexdigest(), data,))

        except sqlite3.IntegrityError:
            logging.info(f"The element already exists in the queue")
        except sqlite3.Error as e:
            logging.info(f"Error enqueuing data:{str(e)}")

    def dequeue(self, limit=1):
        """
        Dequeue data from the 'queue' table.

        Parameters:
        - limit (int): The maximum number of items to dequeue. Defaults to 1.

        Returns:
        - rows (list): The dequeued rows from the 'queue' table.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                # Select the specified number of rows from the 'queue' table
                cursor.execute("SELECT id, data FROM queue LIMIT ?", (limit,))
                rows = cursor.fetchall()
                # Get the IDs from the selected rows
                ids = [row[0] for row in rows]
                conn.commit()
                return rows
        except sqlite3.Error as e:
            raise ValueError("Error dequeuing data") from e

    def delete_processed(self, id_list):
        """
        Delete processed data from the 'queue' table.

        Parameters:
        - id_list (list): A list of IDs to be deleted from the 'queue' table.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                placeholders = ', '.join('?' * len(id_list))
                query = f"DELETE FROM queue WHERE id IN ({placeholders})"
                # Delete the rows with the specified IDs
                cursor.execute(query, id_list)
                conn.commit()
        except sqlite3.Error as e:
            logging.info(f"Error deleting processed data: {str(e)}")
