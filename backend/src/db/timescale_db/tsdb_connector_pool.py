from psycopg2.pool import ThreadedConnectionPool

from src.config.settings import get_settings


class TimescaleDBConnectorPool(object):
    pool = None
    connected = False

    """
    Initializes a connection to the TimescaleDB
    """

    def __init__(self):
        self.connect()

    def disconnect(self):
        """
        Closes a db connection
        """
        self.pool.closeall()
        self.connected = False

    def connect(self):
        """
        Reconnects to a database, if it has been closed by @disconnect before
        """
        config = get_settings()
        if not self.connected:
            self.pool = ThreadedConnectionPool(2, 20, user=config.db_user, password=config.db_pw, host=config.db_url, port=config.db_port, database=config.db_database)
            self.connected = True

    def get_conn(self):
        return self.pool.getconn()
