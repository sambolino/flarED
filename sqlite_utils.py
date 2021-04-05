#!/usr/bin/env python3

import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

def populate_table(conn, sql, rows):
    """ insert multiple rows of data into a table
    :param conn: Connection object
    :param sql: INSERT INTO statement
    :param rows: the data as a list of rows
    :return: lastrowid
    """
    cur = conn.cursor()
    cur.executemany(sql, rows)
    conn.commit()
    return cur.lastrowid

def truncate_table(conn, table_name):
    """ delete data inside the table table from the create_table_sql statement
    :param conn: Connection object
    :param table_name: a CREATE TABLE statement
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM %s;" %(table_name))
    conn.commit()

def custom_query(conn, sql):
    """ execute a custom query
    :param conn: Connection object
    :param sql: a custom SELECT statement
    :return: query
    """
    cur = conn.cursor()
    cur.execute(sql)
    query = cur.fetchall()

    if query == None:
        raise ValueError("Something went wrong")

    return query
