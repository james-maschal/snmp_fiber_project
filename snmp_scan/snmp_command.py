"""Module for reading index report and gathering RX levels
for each interface."""

import json
from jns_snmp_connect import snmp_connect
from snmp_scan import dict_create


def snmp_init(config):
    """The index report is loaded and each
    interface is sent to stage 1, for further
    snmp data collection. This is then combined
    and sent to be output to a JSON file.
    """

    with open(config["ini"][4], 'r', encoding="UTF-8") as draft:

        index_dict = json.load(draft)
        rx_report = []
        err_report = ["Description report errors:"]

        for switch_set in index_dict:

            switch_key = switch_set.keys()
            switch = switch_set["Switch"]
            chassis = switch_set["Chassis"]
            rx_dict = {"Switch" : switch}

            for index in switch_key:

                if index.isnumeric():
                    oid = config["ini"][2] + index

                    rx_level_pretty = stage_1(
                                            config,
                                            switch,
                                            chassis,
                                            err_report,
                                            oid
                                            )

                    if isinstance(rx_level_pretty, float):
                        updict = {index : rx_level_pretty}
                        rx_dict.update(updict)

            rx_report.append(rx_dict)

        dict_create.rx_json(rx_report, config)

    return err_report



def stage_1(config, switch, chassis, err_report, oid):
    """The sfp rx level for each interface
    is gathered via SNMP, then passed through
    a filter, then returned."""

    rx_level, status_1 = snmp_connect.snmp_binds(
                                            switch,
                                            config,
                                            oid
                                            )

    if status_1 and len(rx_level) > 0:
        rx_level_pretty, status_2 = dict_create.var_binds(
                                                    rx_level,
                                                    chassis,
                                                    switch
                                                    )

        if status_2:
            return rx_level_pretty

        return " "

    log_text = f"{switch} - Bad SNMP connection"
    err_report.append(log_text)
    return " "
