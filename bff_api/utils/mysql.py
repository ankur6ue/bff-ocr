import mysql.connector
from mysql.connector import errorcode


DB_NAME = 'jobs'
TABLES={}
TABLES['jobs'] = (
    "CREATE TABLE `jobs` ("
    "  `job_name` varchar(21) NOT NULL,"
    "  `start_time` TIMESTAMP NULL DEFAULT NULL,"
    "  `completion_time` TIMESTAMP NULL DEFAULT NULL,"
    "  `success` BOOLEAN,"
    "  PRIMARY KEY (`job_name`)"
    ") ENGINE=InnoDB")


def update_row(config, job_name, status, logger):
    cnx = connect(config, logger)
    cursor = cnx.cursor()
    update_job = ("UPDATE jobs SET completion_time = %s, success = %s "
                  "WHERE job_name LIKE %s")
    end_time = status["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
    status = status["success"]
    updated_job_data = (end_time, status, job_name)
    try:
        cursor.execute(update_job, updated_job_data)
        cnx.commit()
    except mysql.connector.Error as err:
        logger.warn("Error updating row: {}".format(err.msg))
        cnx.rollback()
    else:
        logger.info("mysql: successfully updated row")
    finally:
        cnx.close()
    #    cursor.close()


def add_row(config, job_name, status, logger):
    cnx = connect(config, logger)
    cursor = cnx.cursor()
    add_job = ("INSERT INTO jobs "
               "(job_name, start_time, completion_time, success) "
               "VALUES (%s, %s, %s, %s)")
    start_time = status["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
    job_data = (job_name, start_time, None, False)
    try:
        cursor.execute(add_job, job_data)
        cnx.commit()
    except mysql.connector.Error as err:
        logger.warn("Error inserting row: {}".format(err.msg))
        cnx.rollback()
    else:
        logger.info("mysql: successfully updated row")
    finally:
        cnx.close()


def get_row(config, job_name, logger):
    # See https://stackoverflow.com/questions/29772337/python-mysql-connector-unread-result-found-when-using-fetchone
    # for why buffered=True is needed
    cnx = connect(config, logger)
    cursor = cnx.cursor(buffered=True)

    # To get all rows
    # cursor.execute("SELECT * FROM jobs")
    # result = cursor.fetchall()
    # loop through the rows
    # for row in result:
    #    print(row)
    #    print("\n")
    job_name_length = len(job_name)
    query = ("SELECT job_name, start_time, completion_time, success FROM jobs "
             "WHERE LEFT(job_name, %s)  LIKE %s")
    try:
        cursor.execute(query, (job_name_length, job_name))
        if cursor.rowcount == 0:
            return None
        return cursor.fetchone()

    except mysql.connector.Error as err:
        logger.warn("Error inserting row: {}".format(err.msg))
    finally:
        cnx.close()


# Reads the credentials corresponding to the IAMRole passed as parameter
def get_creds(config, iamrole, logger):
    # See https://stackoverflow.com/questions/29772337/python-mysql-connector-unread-result-found-when-using-fetchone
    # for why buffered=True is needed
    cnx = connect(config, logger)
    cursor = cnx.cursor(buffered=True)

    # To get all rows
    # cursor.execute("SELECT * FROM jobs")
    # result = cursor.fetchall()
    # loop through the rows
    # for row in result:
    #    print(row)
    #    print("\n")

    query = ("SELECT * FROM creds.creds "
             "WHERE iamrole  LIKE %s")
    try:
        cursor.execute(query, (iamrole, ))
        if cursor.rowcount == 0:
            return None
        return cursor.fetchone()

    except mysql.connector.Error as err:
        logger.warn("Error inserting row: {}".format(err.msg))
    finally:
        cnx.close()


def connect(config, logger=None):
    try:
        cnx = mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        logger.warn("mysql: {}".format(err.msg))
        raise err
    else:
        # create database
        cursor = cnx.cursor()
        try:
            cursor.execute("USE {}".format(DB_NAME))
        except mysql.connector.Error as err:
            logger.info("mysql: Database {} does not exists.".format(DB_NAME))
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                create_database(cursor)
                logger.info("mysql: Database {} created successfully.".format(DB_NAME))
                cnx.database = DB_NAME
            else:  # log other unhandled exception and reraise
                logger.warn("mysql: Error creating database {}.".format(DB_NAME))
                raise err
        else:
            return cnx


def create_database(cursor, logger=None):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        logger.warn("mysql: Failed creating database: {}".format(err.msg))
        cursor.close()
        raise err


def delete_table(cursor, logger=None):
    for table_name in TABLES:
        table_description = "DROP TABLE IF EXISTS {0}".format(table_name)
        try:
            logger.info("Deleting table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            logger.warn("Error deleting table {0}".format(err.msg))
            raise err


def create_table(cursor, logger=None):
    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            logger.info("mysql: Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                logger.info("mysql: table {} already exists.".format(table_name))
            else:
                logger.warn("mysql: Failed creating table: {}".format(err.msg))
                cursor.close()
                raise err
