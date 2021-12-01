import logging

import sqlalchemy as sa

class MySqlConnector():
    """
    Class to connect and write statistics to mysql table.
    """

    def __init__(self, host, user, password, database):
        engine = sa.create_engine("mysql://{}:{}@{}/{}".format(
            user, password, host, database
        ))
        self.con = engine.connect()
        self.row_count = 0
        self._logger = logging.getLogger(__name__)

