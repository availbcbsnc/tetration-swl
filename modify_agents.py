#!/usr/bin/env python

'''
   This script will decom tetration agents

    File name: modify_agents.py
    Version: 1
    Author: Nicholas Bogdajewicz
    Date created: 7/14/2022
    Date last modified: 7/20/2022
    Python Version: 3.8.2
    requests version: 2.27.0
'''

import cluster_login
import logging
from logging.handlers import RotatingFileHandler
from tetpyclient import RestClient
import json
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():

    login = cluster_login.cluster_login()
    host = login[0]
    TET_API_KEY = login[1]
    TET_SEC = login[2]
    agent = login[3]

    while True:
        mode = input("\nWould you like to verify or decom agent(s)? (verify or decom): ")
        if mode != "decom" and mode != "verify":
            print("Please select verify or decom.")
            continue
        else:
            break

    if agent == None:
        while True:
            agent = input("\nExample: agent1,agent2,agent3\nPlease enter the agent(s) hostname: ")
            if " " in agent:
                continue
            while True:
                ans = input("You entered " + agent + " is this correct? (y or n): ")
                ans_low = ans.lower()
                if ans_low != "y" and ans_low != "n":
                    print("Please enter y or n.")
                    continue
                else:
                    break
            if ans_low == "n":
                continue
            else:
                break

    agent2 =  agent.split(",")
    final_agent = agent.split(",")

    offset = ""

    if mode == "decom":
        f = open("decom_agent.txt", "w")
        f.write("User selected agents:\n" + agent + "\n")
        f.write("\nDecommisioned agents:\n")
        select=input("Are you sure you want to decommision the selected agents? (y or n): ")
        if select.lower() != "y":
            sys.exit()
        else:
            while True:

                #gets all of the sensors
                restclient = RestClient(host,
                                        api_key=TET_API_KEY,
                                        api_secret=TET_SEC,
                                        verify=False)

                response = restclient.get("/sensors?limit=1000&offset=" + offset)

                response_json = json.loads(response.text)
                if "offset" in response_json:
                    offset = response_json["offset"]

                #loops through sensors to find the uuid of your hostname
                for item in response_json["results"]:
                    if item["host_name"] in agent2:
                        UUID = item["uuid"]

                        #Removes the agent based on the UUID
                        restclient = RestClient(host,
                                                api_key=TET_API_KEY,
                                                api_secret=TET_SEC,
                                                verify=False)

                        response = restclient.delete("/sensors/" + UUID)
                        if response.status_code == 204 or response.status_code == 200:
                            print("Successfully decommissioned host " + item["host_name"] + ".")
                            f.write(item["host_name"] + ",")
                            if item["host_name"] in final_agent:
                                final_agent.remove(item["host_name"])
                            continue
                        else:
                            print("Error " + str(response) + "! Could not delete agent " + item["host_name"])
                            continue

                if "offset" not in response_json:
                    f.write("\nAgents not found:\n")
                    for item in final_agent:
                        print("Agent " + item + " not found.")
                        f.write(item + ",")
                    break

    if mode == "verify":
        f = open("verify_agent.txt", "w")
        f.write("User selected agents:\n" + agent + "\n")
        f.write("\nFound agents:\n")
        while True:

            #gets all of the sensors
            restclient = RestClient(host,
                                    api_key=TET_API_KEY,
                                    api_secret=TET_SEC,
                                    verify=False)

            response = restclient.get("/sensors?limit=1000&offset=" + offset)

            response_json = json.loads(response.text)
            if "offset" in response_json:
                offset = response_json["offset"]

            #loops through sensors to find the uuid of your hostname
            for item in response_json["results"]:
                if item["host_name"] in agent2:

                    #print(item)
                    if "deleted_at" in item:
                        continue

                    print("Successfully verified host " + item["host_name"] + ".")
                    f.write(item["host_name"] + ",")
                    if item["host_name"] in final_agent:
                        final_agent.remove(item["host_name"])
                    continue


            if "offset" not in response_json:
                f.write("\nAgents not found:\n")
                for item in final_agent:
                    print("Agent " + item + " not found.")
                    f.write(item + ",")
                break


    f.close()

if __name__ == '__main__':
    main()