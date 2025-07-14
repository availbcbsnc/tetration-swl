Anything to Annotations
#######################

Overview
--------


How to Use
----------

.. code:: bash

    $ anything2annotations --help 
    usage: anything2annotations [-h] -f FILE -i IP [-m MASK] -n NEW -s SHORT [-l LONG] [-p PARENT] [-d DELIMITED] [-a ADD] [-k KEEP] [-e EXCLUDE] [-c CASE]
                                [-R REGEX] [-S SEARCH] [-V VLOOKUP] [-C COMBINE] -P PROJECTID

    Parse csv with ip and/or network for annotations. Multiple ips per row transposed. Duplicate ip context concatenated.

    optional arguments:
      -h, --help            show this help message and exit
      -f FILE               csv file REQUIRED
      -i IP                 ip, network or cidr REQUIRED
      -m MASK               subnet mask or mask length (24 or 255.255.255.0) discarded OPTIONAL
      -n NEW                new field combines short and long (if present 40 chars) multiple SHARED REQUIRED
      -s SHORT              short field (in:out 255 chars) multiple delimited REQUIRED
      -l LONG               long field (in:out 255 chars) multiple delimited OPTIONAL
      -p PARENT             parent field (in:out 40 chars) multiple SHARED OPTIONAL
      -d DELIMITED          delimited fields (in:out 255 chars) multiple delimited OPTIONAL
      -a ADD                add new field and value (field1=value,field2=value 255 chars) OPTIONAL
      -k KEEP               keep fields (in:out 255 chars) retained OPTIONAL
      -e EXCLUDE            values to exclude (field1=value1,value2;field2=value1,value2) discarded OPTIONAL
      -c CASE               upper/lower/title OPTIONAL
      -R REGEX              replace regex with sub (field=regex:sub,regex:sub;field=regex:sub,regex:sub) OPTIONAL special chars [comma] [colon] [equals] [semicolon]
      -S SEARCH             search source for regex and assign value to dest (source=regex:dest=value,source=regex:dest=value) OPTIONAL special chars [comma]
                            [colon] [equals]
      -V VLOOKUP            lookup key in external file, replace dest with column index (filename:key;index1=dest1,index2=dest2) OPTIONAL
      -C COMBINE            assign space delimitted fields to dest (dest1=field1,field2,field3;dest2=field4,field5) OPTIONAL
      -P PROJECTID, --pid PROJECTID
                            Project ID



.. sectionauthor:: First Last <cec@cisco.com>