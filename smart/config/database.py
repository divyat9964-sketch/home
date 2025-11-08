# database.py
import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        self.host = 'localhost'
        self.database = 'SmartHomeDB'   # match SQL file
        self.user = 'root'              # change as needed
        self.password = 'divyat9731'    # change as needed

    def get_connection(self, user=None, password=None):
        """Get database connection with specified user or default"""
        try:
            conn_user = user if user else self.user
            conn_password = password if password else self.password
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=conn_user,
                password=conn_password,
                autocommit=False
            )
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    def execute_query(self, query, params=None, user=None, password=None):
        """
        Execute a query and return results.
        - For SELECT: returns list of dict rows.
        - For INSERT/UPDATE/DELETE: returns lastrowid or number of affected rows.
        - For CALL (stored proc): returns list of rows from first result set if any.
        """
        connection = self.get_connection(user=user, password=password)
        if connection is None:
            return None

        try:
            cursor = connection.cursor(dictionary=True)
            q = query.strip()
            # If it's a CALL to stored procedure, use callproc
            if q.upper().startswith("CALL") or "CALL " in q.upper():
                # extract proc name and rely on cursor.callproc if possible
                # For simplicity: if CALL ... we use execute and then fetchall from cursor
                cursor.execute(query, params) if params else cursor.execute(query)
                # fetch all result sets (for stored procs)
                results = []
                try:
                    # some drivers return result sets via stored_results
                    for res in cursor.stored_results():
                        results.extend(res.fetchall())
                except Exception:
                    # fallback to cursor.fetchall if single result set
                    try:
                        results = cursor.fetchall()
                    except Exception:
                        results = []
                connection.commit()
                cursor.close()
                connection.close()
                return results

            # Normal SELECT
            if q.upper().startswith("SELECT"):
                cursor.execute(query, params) if params else cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()
                connection.close()
                return rows

            # INSERT / UPDATE / DELETE
            cursor.execute(query, params) if params else cursor.execute(query)
            connection.commit()
            lastrowid = cursor.lastrowid
            affected = cursor.rowcount
            cursor.close()
            connection.close()
            # prefer returning lastrowid for inserts, else affected rows
            return lastrowid if lastrowid else affected
        except Error as e:
            print(f"Error executing query: {e}")
            try:
                connection.rollback()
            except Exception:
                pass
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
                try:
                    connection.close()
                except Exception:
                    pass
            return None

# single instance
db = Database()
