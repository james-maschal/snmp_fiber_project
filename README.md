# SNMP_fiber_project
This project is designed to collect SFP Rx levels
for storage and querying for bad interfaces. It references a list
of interfaces for each switch deemed "critical", updated every 30
days. All data gets exported to a database for later retrieval.

NOTE - You will need to update the .ini file directory with your own directory.

## Stage 1 - Index Report
- The first thing this program does is check a file named "last_ran.ini" for the date of last index_report creation. If it has been more than 30 days, or if the file doesn't exist, It runs the index_report creation script.
- This script gathers an snmp inventory table for every switch in the "crit_buildings" function from cisco_devices.py. It then filters for interfaces labeled "Receive", and filters out "FortyGig"/"Fo" interfaces. It also cleans up "TenGigabit" and "Gigabit" interfaces to make everything conformative. The last section of the OID returned is used as the reference index for each interface moving forward.(**See [entPhysicalDescr](https://snmp.cloudapps.cisco.com/Support/SNMP/do/BrowseOID.do?objectInput=1.3.6.1.2.1.47.1.1.1.1.2&translate=Translate&submitValue=SUBMIT&submitClicked=true)**)
- A secondary snmp variable get (same as inventory, but with ".1" appended to the end.) for the Chassis type is sent out for each of the switches to be appended to the index report. (This is used later.)
- Everything is exported into index_report.json file for importing later.

## Stage 2 - Data Scraping
- This stage imports the index_report.json file and for each interface it sends an snmp variable get for the receive sensor value. (**See [entSensorValue](https://snmp.cloudapps.cisco.com/Support/SNMP/do/BrowseOID.do?objectInput=1.3.6.1.4.1.9.9.91.1.1.1.1.4&translate=Translate&submitValue=SUBMIT&submitClicked=true)**)
- Each variable gets filtered through several stages of formatting to convert it into decimal format, and to account for data type variance. (i.e. Cisco 9400 and 9600 series Chassis give different variable formats for sensor data.)
- All data is compiled and exported into the rx_levels.json file.

## Stage 3 - Database Export
- At this stage, the program connects to the database, and creates an index table for each switch, if it doesn't already exist. This contains the interface index, and name (i.e Te1/0/4, Twe6/0/45) for reference. It then fills the table with data collected from index_report.json
- It then creates a secondary rx_table for each switch, containing the switch, index (referenced against the index table), rx_level, and date (autogenerated on INSERT).
- Finally, a final table is compiled from each switch's index/rx_level tables, containing switch, interface name, rx_level, and date. an "id" column is autogenerated on INSERT, for use with Django's Web Framework. This table is created to make querying easier.


