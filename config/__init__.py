# Install PyMySQL as MySQLdb driver if available
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
