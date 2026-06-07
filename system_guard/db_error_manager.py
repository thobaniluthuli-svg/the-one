"""DB Error Manager - MySQL-based Error Persistence with Full Traceability

Stores execution errors in MySQL database with full class/method/input tracking.
"""

from typing import Dict, Any, List, Optional
import json

try:
    import mysql.connector
except ImportError:
    mysql = None


class DBErrorManager:
    """MySQL-based error persistence with full class/method traceability."""

    def __init__(
        self,
        host: str = "localhost",
        database: str = "system_guard",
        user: str = "root",
        password: str = "",
    ):
        """Initialize DBErrorManager with MySQL connection parameters.

        Args:
            host: MySQL server host
            database: Database name
            user: MySQL user
            password: MySQL password
        """
        if mysql is None:
            raise ImportError(
                "mysql-connector-python is required. Install with: pip install mysql-connector-python"
            )

        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self._errors: List[Dict[str, Any]] = []  # Fallback in-memory storage

        try:
            self._connect()
        except Exception as e:
            print(f"Warning: Could not connect to MySQL: {e}. Using in-memory storage.")

    def _connect(self) -> None:
        """Establish MySQL connection."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            self._create_tables()
        except Exception as e:
            print(f"MySQL connection failed: {e}")
            self.connection = None

    def _create_tables(self) -> None:
        """Create error table if not exists."""
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS errors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ts FLOAT,
                    class_name VARCHAR(255),
                    method_name VARCHAR(255),
                    status VARCHAR(50),
                    error_type VARCHAR(255),
                    error_message TEXT,
                    stack TEXT,
                    args TEXT,
                    kwargs TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Failed to create error table: {e}")

    def ingest_error(self, packet: Dict[str, Any]) -> bool:
        """Store execution packet as error in MySQL.

        Args:
            packet: Execution packet from TraceInterceptor

        Returns:
            True if successful, False otherwise
        """
        # Store in memory regardless
        self._errors.append(packet)

        # Try to store in MySQL
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()

            meta = packet.get("meta", {})
            error = packet.get("error", {})
            trace = packet.get("trace", {})

            query = """
                INSERT INTO errors
                (ts, class_name, method_name, status, error_type, error_message, stack, args, kwargs)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                meta.get("ts"),
                meta.get("class"),
                meta.get("method"),
                meta.get("status"),
                error.get("type"),
                error.get("message"),
                error.get("trace"),
                trace.get("args"),
                trace.get("kwargs"),
            )

            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Failed to ingest error to MySQL: {e}")
            return False

    def query_by_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Retrieve all errors for a class.

        Args:
            class_name: Name of the class

        Returns:
            List of error records
        """
        # Try MySQL first
        if self.connection:
            try:
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM errors WHERE class_name = %s ORDER BY created_at DESC",
                    (class_name,),
                )
                results = cursor.fetchall()
                cursor.close()
                return results
            except Exception as e:
                print(f"Failed to query by class from MySQL: {e}")

        # Fallback to memory
        return [
            err
            for err in self._errors
            if err.get("meta", {}).get("class") == class_name
        ]

    def query_by_method(self, method_name: str) -> List[Dict[str, Any]]:
        """Retrieve all errors for a method.

        Args:
            method_name: Name of the method

        Returns:
            List of error records
        """
        # Try MySQL first
        if self.connection:
            try:
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM errors WHERE method_name = %s ORDER BY created_at DESC",
                    (method_name,),
                )
                results = cursor.fetchall()
                cursor.close()
                return results
            except Exception as e:
                print(f"Failed to query by method from MySQL: {e}")

        # Fallback to memory
        return [
            err
            for err in self._errors
            if err.get("meta", {}).get("method") == method_name
        ]

    def link_trace(self, class_name: str, method_name: str) -> List[Dict[str, Any]]:
        """Retrieve error history for class/method combination.

        Args:
            class_name: Name of the class
            method_name: Name of the method

        Returns:
            List of error records for the combination
        """
        # Try MySQL first
        if self.connection:
            try:
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM errors WHERE class_name = %s AND method_name = %s ORDER BY created_at DESC",
                    (class_name, method_name),
                )
                results = cursor.fetchall()
                cursor.close()
                return results
            except Exception as e:
                print(f"Failed to link trace from MySQL: {e}")

        # Fallback to memory
        return [
            err
            for err in self._errors
            if err.get("meta", {}).get("class") == class_name
            and err.get("meta", {}).get("method") == method_name
        ]

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                print(f"Failed to close connection: {e}")
            finally:
                self.connection = None

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()
