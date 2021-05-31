import pytest
import os
import sys
import time
import datetime
from prettytable import PrettyTable
# add path to bff_api. Need this because the below doesn't work
# from ..bff_api.utils.k8s import create_job
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

import mysql.connector
from mysql.connector import errorcode
mysql_host = "10.244.0.149"
config = {
    'user': 'root',
    'password': 'password',
    'host': mysql_host,
}
DB_NAME = 'jobs'
TABLES={}
# we want the timestamp to default to null if not set
TABLES['jobs'] = (
    "CREATE TABLE `jobs` ("
    "  `job_name` varchar(16) NOT NULL,"
    "  `start_time` TIMESTAMP NULL DEFAULT NULL,"
    "  `completion_time` TIMESTAMP NULL DEFAULT NULL,"
    "  `success` BOOLEAN,"
    "  PRIMARY KEY (`job_name`)"
    ") ENGINE=InnoDB")

add_job = ("INSERT INTO jobs "
               "(job_name, start_time, completion_time, success) "
               "VALUES (%s, %s, %s, %s)")

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        raise err


def delete_table(cursor, TABLES):
    for table_name in TABLES:
        table_description = "DROP TABLE IF EXISTS {0}".format(table_name)
        try:
            print("Deleting table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
                print("Error deleting table {0}".format(err.msg))

def create_table(cursor, TABLES):
    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
                cursor.close()
                raise err


def connect(config):
    try:
        cnx = mysql.connector.connect(**config)
        return cnx
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
            raise err

cnx = connect(config)
cursor = cnx.cursor()

try:
    cursor.execute("USE {}".format(DB_NAME))
except mysql.connector.Error as err:
    print("Database {} does not exists.".format(DB_NAME))
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        print("Database {} created successfully.".format(DB_NAME))
        cnx.database = DB_NAME
    else: # log other unhandled exception and reraise
        print(err)
        raise err

delete_table(cursor, TABLES)
create_table(cursor, TABLES)
# dummy insert
ts = time.time()
start_time = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
end_time = None
job_data = ('job1', start_time, end_time, False)
try:
    cursor.execute(add_job, job_data)
    cnx.commit()
except mysql.connector.Error as err:
    print("Error inserting row: {}".format(err))
    cnx.rollback()

# update end_time and status
ts = time.time()
end_time = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
update_job = ("UPDATE jobs SET completion_time = %s, success = %s "
               "WHERE job_name LIKE %s")
updated_job_data = (end_time, True, 'job1')
try:
    cursor.execute(update_job, updated_job_data)
    cnx.commit()
except mysql.connector.Error as err:
    print("Error inserting row: {}".format(err))
    cnx.rollback()

# dummy read
query = ("SELECT job_name, start_time, completion_time, success FROM jobs "
         "WHERE job_name LIKE %s")
try:
    cursor.execute(query, ("job1",))
    for (job_name, start_time, completion_time, success) in cursor:
        print("{} job started on {:%d %b %Y}".format(
            job_name, start_time))
except mysql.connector.Error as err:
    print("Error querying: {}".format(err))

# delete row
query = ("DELETE FROM jobs WHERE job_name LIKE %s")
try:
    cursor.execute(query, ("job1",))
    cnx.commit()
except mysql.connector.Error as err:
    print("Error querying: {}".format(err))
# lets create the table




