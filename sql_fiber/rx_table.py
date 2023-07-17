"""Module for creating and filling the Rx level table.
Loads the rx_level JSON file and creates an rx_level
table for each switch.
"""

import json
from mysql.connector import errors


def json_load(file, please):
    """Loads the JSON file and deletes/creates the rx table
    for each switch if not already created. It then iterates
    over each switch's interface, adding it to the table.
    """

    with open(f"{file}", 'r', encoding="UTF-8") as draft:

        interfaces = json.load(draft)

        for switch in interfaces:

            switch_name = switch["Switch"]

            if "-" in switch_name:
                switch_name = switch_name.replace("-", "_")

            rx_table_init(switch_name, please)

            for index, data in switch.items():

                if index.isnumeric():

                    rx_table_fill(
                            please,
                            switch_name,
                            index,
                            data
                            )



def rx_table_init(switch, please):
    """SQL command executor for creating the rx_level
    table for each switch. Deletes table first if it already
    exists. Date column is auto-generated on insert.
    """

    del_statement = f"""
    DROP TABLE IF EXISTS rxlevel_{switch};"""

    statement = f"""
    CREATE TABLE rxlevel_{switch}
    (id SERIAL,
    int_index int,
    switch varchar(80),
    rxlevel numeric,
    date date,
    PRIMARY KEY (id),
    CONSTRAINT rxlevel_{switch}_fk
        FOREIGN KEY (int_index)
        REFERENCES index_{switch}(int_index)
        ON DELETE CASCADE)"""

    try:
        please.execute(del_statement)
        please.execute(statement)

    except errors.ProgrammingError:
        print("Something went wrong during rx table creation")



def rx_table_fill(please, switch, index, data):
    """SQL command executor for filling in the rx_level
    table with each switch's interface.
    """

    statement = f"""
    INSERT INTO rxlevel_{switch} (int_index, switch, rxlevel, date)
    VALUES ({index}, '{switch}', {data}, CURDATE())"""

    try:
        please.execute(statement)

    except errors.ProgrammingError:
        print("Something went wrong during rx table filling.")
