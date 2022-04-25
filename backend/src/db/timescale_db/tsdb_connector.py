from psycopg2 import connect

from src.config.settings import get_settings


class TimescaleDBConnector(object):
    conn = None
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
        self.conn.close()
        self.connected = False

    def connect(self):
        """
        Reconnects to a database, if it has been closed by @disconnect before
        """
        config = get_settings()
        if not self.connected:
            self.conn = connect(f"dbname={config.db_database} user={config.db_user} password={config.db_pw} host={config.db_url} port={config.db_port}")
            self.connected = True
