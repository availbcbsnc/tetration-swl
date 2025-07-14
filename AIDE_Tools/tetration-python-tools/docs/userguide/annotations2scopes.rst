
Annotations to Scopes
#####################

Overview
--------

The tool connects to Tetration cluster to download the annotations as csv file, then goes through the csv file to get the information about scopes created vs scopes to be created

.. Note::
    Before executing this module, the annotations must be imported into Tetration


How to Use
----------

.. code:: bash

    $ annotations2scopes --help                                                                                   
    usage: annotations2scopes [-h] -p PARENT -s SCOPES [-d DESCRIPTIONS] [-c CONFIG] [-e EXCLUDE] -P PROJECTID [-l LOG_LEVEL]
    
    pull annotations, derive scopes and keep in sync (add/delete scopes based on current annotations and scopes)
    
    optional arguments:
      -h, --help            show this help message and exit
      -p PARENT             parent scope (create in UI first)
      -s SCOPES             heirarchy of 40 char scope annotations (class:application:environment)
      -d DESCRIPTIONS       (optional) heirarchy of 255 char scope descriptions (class_description:application_description:environment_decription
      -c CONFIG             (optional) true/false column to trigger config
      -e EXCLUDE            (optional) do not add/delete children for specified scope(s), comma delimited
      -P PROJECTID, --pid PROJECTID
                            Project ID
      -l LOG_LEVEL, --log_level LOG_LEVEL
                            The log level to be used. (default: logging.CRITICAL)


.. sectionauthor:: First Last <cec@cisco.com>


.. spelling::

   Tetration