#!/usr/bin/env python

'''
   This script will contain login info for each secure workload cluster

    File name: cluster_login.py
    Version: 1
    Author: Nicholas Bogdajewicz
    Date created: 7/15/2022
    Date last modified: 7/15/2022
    Python Version: 3.8.2
    requests version: 2.27.0
'''

import sys
import argparse

def cluster_login():

    #takes fabric argument and store the corresponding url
    parser = argparse.ArgumentParser(description='Example: python3 port_config.py --fabric qic --user admin --pass \'cisco!23\' --chg CHG12345')
    parser.add_argument("--fabric", dest="fabric", metavar='', type=str, help='Choose Fabric: ATL, BRM, CLT')
    parser.add_argument("--host", dest="host", metavar='', type=str, help='Enter hostname')
    args = parser.parse_args()
    site = args.fabric
    hostname = args.host

    if site == None:
        while True:
            site = input("Input secure workload cluster (atl, brm or clt): ")
            if site.lower() == "atl" or site.lower() == "brm" or site.lower() == "clt":
                answer = input("Are you sure you want to select " + site + "? (y or n): ")
                if answer.lower() == "y":
                    break
                else:
                    continue
            else:
                print("\nPlease input a valid fabric (atl, brm or clt): ")
                continue

    while True:
        if site.lower() == "atl":
            url = "https://nden01adxqup001.atl.tiaa-cref.org"
            TET_API_KEY = "d5a851cfb2814211b6c2404edb2d9b64"
            TET_SEC = "7576edb80c419c7c75530d6465a5f9f0c9e28b8b"
            break
        elif site.lower() == "brm":
            url = "https://nden01pdxqup001.lan.tiaa-cref.org"
            TET_API_KEY = "49aa1d64f7784412bde966e455db1e7d"
            TET_SEC = "aa565d5e22517f1f321c6b3aae4e7d18b39fc10a"
            break
        elif site.lower() == "clt":
            url = "https://nclt01pdxqup001.lan.tiaa-cref.org"
            TET_API_KEY = "080c989eece8470db5f78f4980437b42"
            TET_SEC = "b6b4f7c4034fac695b1c7b2bac214a7e3394e804"
            break
        else:
            print("Could not determine the fabric.")
            sys.exit()

    return(url, TET_API_KEY, TET_SEC, hostname)
