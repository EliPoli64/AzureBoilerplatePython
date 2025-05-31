import os
import pyodbc
from typing import Any, List, Tuple

class DbConnector:
    """Handles Azure SQL connections using environment configuration."""

    def __init__(self, connectionStringKey: str = "SqlConnectionString") -> None:
        self._connectionStringKey = connectionStringKey
        self._connectionString: str | None = os.getenv(self._connectionStringKey)
        if not self._connectionString:
            raise ValueError(f"Environment variable '{self._connectionStringKey}' is not set.")

    def _getConnection(self) -> pyodbc.Connection:
        return pyodbc.connect(self._connectionString)

    def executeQuery(self, query: str, parameters: Tuple | None = None):
        with self._getConnection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters or ())
                if cursor.description:
                    return cursor.fetchall()
                connection.commit()
                return []