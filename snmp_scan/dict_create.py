"""Module for formatting/filtering all SNMP data."""

import json
import os

def var_table(vartable):
    """This takes the output SNMP table for each switch and checks for
    "Receive" Sensors (SFPs) and formats it to be consistent across
    devices. 40GB interfaces are ignored, as their RX level data is
    incompatible with this script. Data is returned to be JSON'd.
    """

    snmp_info = {}

    try:
        for varbinds in vartable:

            for oid, val in varbinds:

                oid_old = oid.prettyPrint()
                val_old = val.prettyPrint()

                if "Receive" in val_old:

                    a_side, b_side  = stage_1(
                                            val_old,
                                            oid_old,
                                            )

                    if a_side != 0:
                        snmp_info[a_side] = b_side

        return snmp_info, True

    except TypeError:
        print("TypeError")
        return "", False



def stage_1(val_old, oid_old):
    """Filters out unwanted interfaces, such as
    FortyGig. Cleans up interface types as well,
    and conforms them for easy reading.
    """

    a_side = oid_old.split("1.3.6.1.2.1.47.1.1.1.1.2.")[-1]
    b_side = val_old.split(" Receive Power Sensor")[0]

    int_ignore = ["Forty", "Fo"]
    int_discard = [i for i in int_ignore if i in val_old]

    if int_discard:
        pass

    else:
        int_longname = ["TenGigabitEthernet", "GigabitEthernet"]
        int_clean = [i for i in int_longname if i in b_side]

        if int_clean and len(int_clean)==2:
            b_split = b_side.split("TenGigabitEthernet")[-1]
            b_side = ("Te" + b_split)


        if int_clean and len(int_clean)==1:
            b_split = b_side.split("GigabitEthernet")[-1]
            b_side = ("Gi" + b_split)

        return a_side, b_side

    return 0, " "



def var_binds(varbinds, chassis, switch):
    """Takes data gathered from SNMP poll on each interface, and
    runs it through several filters to get rid of bad data (including
    non existant data, "0", and random integers that don't make sense).
    It then formats it to correct decimal notation for easy reading and
    later querying.
    """

    for oid, val in varbinds:

        val_old = val.prettyPrint()

    if "No" not in val_old:

        if 0 <= float(val_old):
            val_old = "000"

        if float(val_old) < -400:
            val_old = "000"

        sophisticated = ["9400", "9600"]
        sophistication_check = [i for i in sophisticated if i in chassis]

        if sophistication_check:
            if "HUB" not in switch:
                if "MCR" not in switch:
                    val_old = f"{val_old}.0"
                    return float(val_old), True

        if len(val_old) < 3:
            val_old = f"-0.{val_old[1:]}"

        else:
            a_half, b_half = val_old[:-1], val_old[-1]
            val_old = f"{a_half}.{b_half}"

        return float(val_old), True

    return None, False



def rx_json(rx_report, config):
    """Takes final RX report list and dumps it into a JSON
    file for uploading to a database later. Checks to see if
    "rx_levels.json" exists, and deletes it if so.
    """

    path_name = config["rx_path"]
    path_state = os.path.exists(path_name)

    if path_state:
        os.remove(path_name)

    json_obj = json.dumps(rx_report, indent=4)

    with open(config["rx_path"], 'a', encoding="UTF-8") as draft:

        print(json_obj, file=draft)
