iOS Reader
==============

Python3 module for examining iOS message databases, using the contact database
to provide names.

iOS Analyzer
============

Python3 script that generates graphs of messages over time, and message
velocity using matplotlib. Change the constants at the top of iOSAnalyzer.py to match your
situation.

Constant Explanations:  
```
prefix: The Name folder where the database file structure is.
numlines: The number of people to show on the graph, sorted by total number of
messages, descending.
numdays: Number of days since the most recent message to show.
pollingnum: The interval at which the texting velocity is measured at, in days.
```


Folder Structure
------

SMS Database: ```Name/sms/sms.db```  

Contacts Database: ```Name/AddressBook/AddressBook.sqlitedb```
