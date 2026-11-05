# Use PyMySQL as a drop-in MySQLdb replacement (no system MySQL client libraries needed).
try:
    import pymysql

    pymysql.version_info = (2, 2, 1, "final", 0)  # satisfy Django's mysqlclient version check
    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover - only when PyMySQL is not installed (e.g. SQLite dev)
    pass
