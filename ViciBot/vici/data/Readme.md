vici.db
=======

The database file *vici.db* consists of public data from [Vici.org](http://vici.org). Therefore *vici.db* is published under the Creative Commons Attribution-ShareAlike 3.0 ([CC BY-SA 3.0](http://creativecommons.org/licenses/by-sa/3.0/)) license. Also see https://vici.org/dataservices.php for more information.


This SQLITE file is generated using the two scripts *vici_data_fetcher.py* and *pickle_to_sqlite.py*   



vici_data_fetcher.py
--------------------

The script downloads the complete JSON dataset from http://vici.org/data.php   
It then tries to correct some errors in the raw JSON data. The JSON will be decoded and the data is saved in a *.pickle* file.



pickle_to_sqlite.py
-------------------

The script takes the *.pickle* file from the previous script and commits it to a fresh SQLITE database file *vici.db*.  
Optionally it creates indexes and a gzipped version of the database file


