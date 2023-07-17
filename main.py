#!/home/netmaschal/python/bin/python3
"""This series of scripts is designed to collect SFP Rx levels
for storage and querying for bad interfaces. It references a list
of interfaces for each switch deemed "critical", updated every 30
days. All data gets exported to a database for later retrieval."""

import configparser
import datetime
import mysql.connector
from snmp_scan import snmp_command
from snmp_scan import index_report
from sql_fiber import rx_table
from sql_fiber import index_table
from sql_fiber import final_table
from jns_cisco_devices import cisco_devices


def main():
    """Main logic."""

    config = configparser.ConfigParser()
    config.read("/[YOUR DIRECTORY HERE]/snmp_fiber_project/info.ini")
    config_v = {
        'ini' : [
            str(config["oid"]["c_string"]),
            str(config["oid"]["sys_inv"]),
            str(config["oid"]["sfp_int_2"]),
            str(config["file_path"]["last_ran_path"]),
            str(config["file_path"]["index_path"]),
            str(config["file_path"]["rx_path"]),
            str(config["oid"]["chassis"]),
            str(config["user"]["name"]),
            str(config["user"]["pass"]),
            str(config["file_path"]["log_path"])
            ]
        }

    log_path = config_v["ini"][9]
    ini_path = config_v["ini"][3]

    datecheck = date_check(config, config_v)

    if datecheck:

        print("Index list out of date, refreshing index....")
        index_get = index_report.index(cisco_devices.crit_buildings(),
                                       config_v)

    else:
        index_get = True

    if index_get:

        print("Index check complete. Gathering data...")
        err_text = snmp_command.snmp_init(config_v)

        print("Data gathering complete. Beginning database export...")

        try:

            cnx = mysql.connector.connect(
                    user=config_v["ini"][7],
                    password=config_v["ini"][8],
                    host='YOUR MYSQL SERVER IP HERE',
                    database='fibercritical',
                    port = 3306
                    )

            please = cnx.cursor()

            print("Verifying/Creating index tables....")
            index_table.json_load(config_v["ini"][4], please)

            print("Creating/Filling rx tables....")
            rx_table.json_load(config_v["ini"][5], please)

            print("Creating/Compiling final table....")
            final_table.json_load(config_v["ini"][4], please)

            cnx.commit()
            cnx.close()

            date = datetime.datetime.now()

            with open(f"{log_path}", 'w', encoding="UTF-8") as log:

                with open(f"{ini_path}", 'r', encoding="UTF-8") as ini:

                    print(f"{date} - FIBER CRITICAL - "
                          "DATABASE CONNECTION SUCCESS \n Index Report:\n", file=log)
                    print(ini.read(), file=log)

                    try:
                        print(err_text, file=log)
                    except:
                        #only for debug/re-adding to databse
                        pass


        except mysql.connector.Error as err:
            err_num = err.errno
            err_check(err_num, log_path, ini_path, err_text)


    print("Complete!")



def err_check(err, log_path, ini_path, err_text):
    """Checks error message number against list of
    known database connection error numbers. If it
    matches, the connection failure is logged. If it
    is not a connection issue, the error message is
    printed to console output."""

    conn_err_list = [1045, 1049, 2003, 2005]
    err_check = [i for i in conn_err_list if i == err]

    if err_check:
        date = datetime.datetime.now()

        with open(f"{log_path}", 'w', encoding="UTF-8") as log:

            with open(f"{ini_path}", 'r', encoding="UTF-8") as ini:

                print(f"{date} - FIBER CRITICAL - "
                    "DATABASE CONNECTION FAILURE", file=log)
                print(err, file=log)
                print(ini.read(), file=log)
                print(err_text, file=log)



def date_check(config, config_v):
    """Checks to see when the last index report
    was ran. If it was within 30 days, a report
    is not run."""

    config.read(config_v["ini"][3])

    try:
        date = {
            'last_ran' : [
                config["run_date"]["date"]
                ]
            }

        date_report = index_report.file_check(date, config_v)

    except KeyError:
        date_report = True

    return date_report



if __name__ == "__main__":
    main()
