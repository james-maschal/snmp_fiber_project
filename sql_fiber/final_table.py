"""Module for combining each rx_level and index table
into a single main table for ease of querying and
tracking.
"""

import json
from mysql.connector import errors


def json_load(file, please):
    """Loads the JSON file and creates the rx table if it
    got deleted for some reason. It then iterates over
    each switch's tables, adding it to the table.
    """

    with open(f"{file}", 'r', encoding="UTF-8") as draft:

        interfaces = json.load(draft)
        final_table_init(please)

        for switch in interfaces:

            switch_name = switch["Switch"]

            if "-" in switch_name:
                switch_name = switch_name.replace("-", "_")

            final_table_fill(please, switch_name)



def final_table_init(please):
    """SQL command executor for creating the critical_final
    table. This is only used in the case where the table was
    deleted or moved.
    """

    statement = """
    CREATE TABLE IF NOT EXISTS jns_fiber
    (id SERIAL,
    switch varchar(80),
    int_name varchar(80),
    rxlevel numeric,
    date date,
    PRIMARY KEY (id))"""

    try:
        please.execute(statement)

    except errors.ProgrammingError:
        print("Somthing went wrong during final table creation.")



def final_table_fill(please, switch):
    """SQL command executor for creating the critical_final
    table. Combines the rx_level and index table by linking the
    index number between them.
    """

    statement = f"""
    INSERT INTO jns_fiber (switch, int_name, rxlevel, date)
    SELECT switch, int_name, rxlevel, date
    FROM rxlevel_{switch} a, index_{switch} b
    WHERE a.int_index = b.index_num;"""

    statement_cleanup = f"""
    DROP TABLE IF EXISTS
    rxlevel_{switch}, index_{switch}"""

    try:
        please.execute(statement)

    except errors.ProgrammingError:
        print("Somthing went wrong during final table compilation.")

    try:
        please.execute(statement_cleanup)

    except errors.ProgrammingError:
        print("Somthing went wrong during table cleanup.")
