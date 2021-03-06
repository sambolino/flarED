#!/usr/bin/env python3

import sqlite3
from sqlite3 import Error
from sqlite_utils import *
import csv
import datetime

def main():

    table_name = "flares"
    sql_create_flares_table = """CREATE TABLE IF NOT EXISTS flares (
                                    transmiter text,
                                    date text NOT NULL, -- 01 Jan 1971
                                    time_ut text NOT NULL, -- 00:00
                                    class text NOT NULL,
                                    ix real NOT NULL, -- W/m2
                                    delta_amp real NOT NULL, -- dB
                                    delta_phase real NOT NULL, -- deg
                                    beta real NOT NULL,
                                    reflection_height real NOT NULL,
                                    ed_control_value real NOT NULL -- for height 74
                                    ); """

    sql_insert_into_flares = """INSERT INTO flares \
            VALUES(?,?,?,?,?,?,?,?,?,?); """

    database = r"data/flare_vlf.db"
    conn = create_connection(database)

    if conn is not None:
        create_table(conn, sql_create_flares_table)
        truncate_table(conn, table_name)

    a_file = open("data/flare_vlf.csv")
    rows = csv.reader(a_file)
    header = next(rows, None)

    with conn:
        populate_table(conn, sql_insert_into_flares, rows)

if __name__ == '__main__':
    main()
