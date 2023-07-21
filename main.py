#!/home/netmaschal/python/bin/python3
"""This series of scripts is designed to collect SFP Rx levels
for storage and querying for bad interfaces. It references a list
of interfaces for each switch deemed "critical", updated every 30
days. All data gets exported to a database for later retrieval."""

import configparser
import datetime
import mysql.connector
from jns_cisco_devices import cisco_devices
from snmp_scan import snmp_command
from snmp_scan import index_report
from sql_fiber import rx_table
from sql_fiber import index_table
from sql_fiber import final_table



def main():
    """Main logic."""

    config = configparser.ConfigParser()
    config.read("/home/netmaschal/python/snmp_fiber_project/info.ini")
    config_v = {
            "log_path"      : str(config["file_path"]["log_path"]),
            "rx_path"       : str(config["file_path"]["rx_path"]),
            "index_path"    : str(config["file_path"]["index_path"]),
            "last_ran_path" : str(config["file_path"]["last_ran_path"]),
            "server_passwd" : str(config["sql_user"]["pass"]),
            "server_user"   : str(config["sql_user"]["name"]),
            "server_IP"     : str(config["sql_user"]["server"]),
            "server_port"   : str(config["sql_user"]["port"]),
            "server_db"     : str(config["sql_user"]["db_name"]),
            "oid_chassis"   : str(config["oid"]["chassis"]),
            "oid_sfp"       : str(config["oid"]["sfp_int_2"]),
            "oid_sys_inv"   : str(config["oid"]["sys_inv"]),
            "comm_string"   : str(config["oid"]["c_string"]),
            }

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
                    user        = config_v["server_user"],
                    password    = config_v["server_passwd"],
                    host        = config_v["server_IP"],
                    database    = config_v["server_db"],
                    port        = config_v["server_port"]
                    )

            please = cnx.cursor()

            print("Verifying/Creating index tables....")
            index_table.json_load(config_v["index_path"], please)

            print("Creating/Filling rx tables....")
            rx_table.json_load(config_v["rx_path"], please)

            print("Creating/Compiling final table....")
            final_table.json_load(config_v["index_path"], please)

            cnx.commit()
            cnx.close()

            date = datetime.datetime.now()

            with open(f"{config_v['log_path']}", 'w', encoding="UTF-8") as log:

                with open(f"{config_v['last_ran_path']}", 'r', encoding="UTF-8") as ini:

                    print(f"{date} - FIBER CRITICAL - "
                          "DATABASE CONNECTION SUCCESS \n Index Report:\n", file=log)

                    print(ini.read(), file=log)

                    print(err_text, file=log)

        except mysql.connector.Error as err:
            err_num = err.errno
            err_check(err_num, config_v["log_path"], config_v['last_ran_path'], err_text)


    print("Complete!")



def err_check(err, log_path, ini_path, err_text):
    """Checks error message number against list of
    known database connection error numbers. If it
    matches, the connection failure is logged. If it
    is not a connection issue, the error message is
    printed to console output."""

    conn_err_list = [1045, 1049, 2003, 2005]
    err_checklist = [i for i in conn_err_list if i == err]

    if err_checklist:
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

    config.read(config_v["last_ran_path"])

    try:
        date = {
            "last_ran" : config["run_date"]["date"]
            }

        date_report = index_report.file_check(date, config_v)

    except KeyError:
        date_report = True

    return date_report



if __name__ == "__main__":
    main()
