#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Greg Jost"
__email__ = "grjost@cisco.com"
__copyright__ = """
Copyright 2020, Cisco Systems, Inc. 
All Rights Reserved. 
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
OTHER DEALINGS IN THE SOFTWARE. 
"""

import json
import csv
import argparse
from tetpyclient import RestClient
from treelib import Node, Tree
import datetime
import ipaddress
import urllib3
import aide
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
LOGGER = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(
        description="pull annotations, derive scopes and keep in sync (add/delete scopes based on current annotations and scopes)"
    )
    parser.add_argument(
        "-p", dest="parent", help="parent scope (create in UI first)", required=True
    )
    parser.add_argument(
        "-s",
        dest="scopes",
        help="heirarchy of 40 char scope annotations (class:application:environment)",
        required=True,
    )
    parser.add_argument(
        "-d",
        dest="descriptions",
        help="(optional) heirarchy of 255 char scope descriptions (class_description:application_description:environment_decription",
        required=False,
    )
    parser.add_argument(
        "-c",
        dest="config",
        help="(optional) true/false column to trigger config",
        required=False,
    )
    parser.add_argument(
        "-e",
        dest="exclude",
        help="(optional) do not add/delete children for specified scope(s), comma delimited",
        required=False,
    )
    parser.add_argument(
        "-P", "--pid", dest="projectid", help="Project ID", required=True
    )
    parser.add_argument(
        "-l",
        "--log_level",
        type=int,
        default=logging.CRITICAL,
        help="The log level to be used. (default: logging.CRITICAL)",
    )

    # parser.add_argument('-f', dest='filter', help='column containing filters on parent scope (vlan, epg, zone, site, etc.)', required=False)
    # parser.add_argument('-e', dest='email', help='column containing email of scope owner', required=False)
    # parser.add_argument('-r', dest='rbac,', help='column to assign rbac', required=False)
    # parser.add_argument('-w', dest='workspace', help='column containing workspaces', required=False)

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    return args


# def get_prefix_length(row):
#     return ipaddress.ip_network(row[0]).prefixlen


# def get_scope_length(scope):
#     return len(scope.split(':'))


def main():
    commit = False

    rc = RestClient(
        json.loads(open("endpoint.json", "r").read())["api_endpoint"],
        credentials_file="./credentials.json",
        verify=False,
    )
    args = get_args()

    # get annotations
    filename = "annotations.csv"
    rc.download(filename, "/assets/cmdb/download/" + args.parent.split(":")[0])
    with open(filename, encoding="utf8", errors="ignore") as file:
        annotations = list(csv.reader(file, delimiter=","))

    headers = annotations.pop(0)
    # annotations.sort(key=get_prefix_length)
    annotations = sorted(
        annotations, key=lambda x: ipaddress.ip_network(x[0]).prefixlen
    )

    if len(annotations) == 0:
        print("upload annotations first")
        quit()

    # get scope indeces
    scope_indeces = []

    for column in args.scopes.split(":"):
        if column in headers:
            scope_indeces.append(headers.index(column))
        else:
            print(headers)
            print(column + " not found in headers")
            exit()

    # get description indeces
    description_indeces = []
    if args.descriptions is not None:
        for column in args.descriptions.split(":"):
            if column in headers:
                description_indeces.append(headers.index(column))
            else:
                print(headers)
                print(column + " not found in headers")
                exit()

    # get config index
    if args.config is not None:
        if args.config in headers:
            config_index = headers.index(args.config)
        else:
            print(headers)
            print(args.config + " not found in headers")
            exit()

    # get scopes from annotations
    print("\nbuilding scope tree per annotations\n")
    unique_scopes = set()
    unique_descriptions = set()
    networks = []
    ip_count = 0
    orphans = set()

    # get excludes
    excludes = []
    if args.exclude is not None:
        excludes = args.exclude.split(",")

    for row in annotations:
        scope = ""

        # apply inheritance
        if "/" in row[0]:
            networks.append(row)
        else:
            ip_count += 1

        for i in range(len(scope_indeces)):
            if row[scope_indeces[i]] == "":
                for network in networks:
                    if "/" in row[0] and row[0] != network[0]:
                        if (
                            next(ipaddress.ip_network(row[0]).hosts())
                            in ipaddress.ip_network(network[0])
                            and network[scope_indeces[i]] != ""
                        ):
                            row[scope_indeces[i]] = network[scope_indeces[i]]
                    elif "/" not in row[0] and ipaddress.ip_address(
                        row[0]
                    ) in ipaddress.ip_network(network[0]):
                        if network[scope_indeces[i]] != "":
                            row[scope_indeces[i]] = network[scope_indeces[i]]

            # config trigger
            config = False
            if args.config is None:
                config = True
            elif row[config_index] != "":
                config = json.loads(row[config_index].lower())

            if config:
                include = True
                for exclude in excludes:
                    if exclude in scope.split(":"):
                        include = False

                if i == 0:
                    scope = args.parent + ":" + row[scope_indeces[i]].replace(":", " ")
                elif include:
                    scope += ":" + row[scope_indeces[i]].replace(":", " ")

                # clean up orphans
                if "::" not in scope and not scope.endswith(":"):
                    unique_scopes.add(scope.replace(",", ""))
                    if args.descriptions is not None:
                        unique_descriptions.add(
                            scope
                            + "\t"
                            + row[description_indeces[i]].replace("\t", " ")
                        )
                elif "/" not in row[0] and not scope.endswith(":"):
                    print("warning: orphaned " + row[0] + " " + scope)
                    orphans.add(row[0])

    print("\ncomparing to configured scope tree\n")
    # scopes = sorted(unique_scopes)
    # scopes.sort(key=get_scope_length)
    scopes = sorted(unique_scopes, key=lambda x: len(x.split(":")))
    descriptions = sorted(unique_descriptions)

    # get current scopes and parent scope id
    resp = rc.get("/app_scopes/", timeout=30.0)
    app_scopes = json.loads(resp.content)

    scope_ids = []
    current_scopes = []

    for app_scope in app_scopes:
        if app_scope["name"].split(":")[0] == args.parent.split(":")[0]:
            if (
                app_scope["name"][0 : len(args.parent)] == args.parent
                or args.parent[0 : len(app_scope["name"])] == app_scope["name"]
            ):
                # if app_scope['name'].split(':')[0] == args.parent.split(':')[0]:
                scope_ids.append([app_scope["name"], app_scope["id"]])
                current_scopes.append(app_scope["name"])

    if len(current_scopes) < len(args.parent.split(":")):
        print("parent " + args.parent + " not in scopes")
        quit()

    # get add and delete count
    count = 0

    add_scopes = []
    delete_scopes = []

    for scope in scopes:
        if scope not in current_scopes:
            add_scopes.append(scope)
    for current_scope in current_scopes:
        include = True
        for exclude in excludes:
            if exclude in current_scope.split(":"):
                include = False
        if current_scope not in scopes and current_scope not in args.parent and include:
            delete_scopes.append(current_scope)

    print(
        "\nips (total/orphaned/scoped): "
        + str(ip_count)
        + "/"
        + str(len(orphans))
        + "/"
        + str(ip_count - len(orphans))
    )

    print(
        "\nscopes (current/add/delete/future): "
        + str(len(current_scopes))
        + "/"
        + str(len(add_scopes))
        + "/"
        + str(len(delete_scopes))
        + "/"
        + str(len(current_scopes) - len(delete_scopes) + len(add_scopes))
    )

    response = input("\nshow scope tree (yes/no)? ")
    if response == "yes":
        current_scopes = sorted(current_scopes, key=lambda x: len(x.split(":")))
        tree = Tree()

        for current_scope in current_scopes:
            current_scope = current_scope.replace("\n", " ")
            L = current_scope.split(":")
            if len(L) == 1:
                tree.create_node(current_scope, current_scope)
            else:
                short = L.pop()
                parent = ":".join(L)
                tree.create_node(short, current_scope, parent)
        print("=============================== CURRENT ===============================")
        tree.show()

        if len(add_scopes) > 0 or len(delete_scopes) > 0:
            final_scopes = list(
                set(current_scopes).union(set(add_scopes)) - set(delete_scopes)
            )
            final_scopes = sorted(final_scopes, key=lambda x: len(x.split(":")))
            tree = Tree()

            for final_scope in final_scopes:
                final_scope = final_scope.replace("\n", " ")
                L = final_scope.split(":")
                if len(L) == 1:
                    tree.create_node(final_scope, final_scope)
                else:
                    short = L.pop()
                    parent = ":".join(L)
                    tree.create_node(short, final_scope, parent)
            print(
                "================================= NEW ================================="
            )
            tree.show()

    else:
        print("\nskipped!\n")

    if len(add_scopes) > 0 or len(delete_scopes) > 0:
        response = input("\nconfigure scopes (yes/no)? ")
        if response == "yes":

            keystrokes = 0

            # delete scopes
            if len(delete_scopes) > 0:
                for scope in delete_scopes:
                    print("delete " + scope)

                response = input("\ndelete " + str(len(delete_scopes)) + " (yes/no)? ")
                if response == "yes":

                    for scope_id in scope_ids:
                        if (
                            scope_id[0] in delete_scopes
                            and scope_id[0] not in args.parent
                        ):
                            # if scope_id[0] not in scopes and scope_id[0] not in args.parent:
                            commit = True
                            count += 1
                            keystrokes += 2
                            print(
                                str(count)
                                + "/"
                                + str(len(delete_scopes))
                                + " delete "
                                + scope_id[0].replace("\n", " ")
                            )
                            resp = rc.delete("/app_scopes/" + scope_id[1])
                            if resp.status_code == 200:
                                print(
                                    "    "
                                    + datetime.datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    )
                                    + " "
                                    + str(resp.status_code)
                                    + " "
                                    + resp.reason
                                )
                            elif resp.status_code == 422:
                                delete_dependents(rc, resp, scope_id)
                            else:
                                print("    " + str(resp.status_code) + " " + resp.text)
                else:
                    print("\nskipped!\n")
            # add scopes
            count = 0

            if len(add_scopes) > 0:
                for scope in add_scopes:
                    print("add " + scope)

                response = input("\nadd " + str(len(add_scopes)) + " (yes/no)? ")
                if response == "yes":

                    # add scopes
                    for scope in scopes:
                        if scope not in current_scopes:
                            commit = True

                            L = scope.split(":")
                            short_name = L.pop()
                            parent_name = ":".join(L)
                            header = headers[
                                scope_indeces[
                                    len(scope.replace(args.parent + ":", "").split(":"))
                                    - 1
                                ]
                            ]
                            description = ""

                            for scope_id in scope_ids:
                                if scope_id[0] == parent_name:
                                    parent_id = scope_id[1]
                                    break

                            for pair in descriptions:
                                if pair.split("\t")[0] == scope:
                                    description = pair.split("\t")[1]

                            req_payload = {
                                "short_name": short_name,
                                "short_query": {
                                    "type": "eq",
                                    "field": "user_" + header,
                                    "value": short_name,
                                },
                                "parent_app_scope_id": parent_id,
                                "description": description,
                            }
                            count += 1
                            keystrokes += (
                                2 * len(short_name) + len(description) + len(header) + 4
                            )

                            print(
                                str(count)
                                + "/"
                                + str(len(add_scopes))
                                + " create "
                                + scope.replace("\n", " ")
                            )

                            resp = rc.post(
                                "/app_scopes", json_body=json.dumps(req_payload)
                            )
                            print(
                                "    "
                                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                + " "
                                + str(resp.status_code)
                                + " "
                                + resp.reason
                            )

                            if resp.status_code == 200:
                                scope_ids.append(
                                    [
                                        json.loads(resp.content)["name"],
                                        json.loads(resp.content)["id"],
                                    ]
                                )
                                scope_ids.sort(reverse=True)
                            else:
                                print("    " + str(resp.status_code) + " " + resp.text)
                else:
                    print("\nskipped!\n")

            # commit scope changes
            if commit:
                for scope_id in scope_ids:
                    if scope_id[0] == args.parent.split(":")[0]:
                        parent_id = scope_id[1]
                        break

                req_payload = {"root_app_scope_id": parent_id, "sync": True}

                print("commit scope changes")
                resp = rc.post(
                    "/app_scopes/commit_dirty",
                    json_body=json.dumps(req_payload),
                    timeout=30.0,
                )
                if resp.status_code == 200:
                    print(
                        "    "
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        + " "
                        + str(resp.status_code)
                        + " "
                        + resp.reason
                    )
                else:
                    print(resp.text)

            # show tree
            print(
                "\nips (total/orphaned/scoped): "
                + str(ip_count)
                + "/"
                + str(len(orphans))
                + "/"
                + str(ip_count - len(orphans))
            )
            print(
                "\nscopes (previous/add/delete/current): "
                + str(len(current_scopes))
                + "/"
                + str(len(add_scopes))
                + "/"
                + str(len(delete_scopes))
                + "/"
                + str(len(current_scopes) - len(delete_scopes) + len(add_scopes))
            )

            response = input("\nshow scope tree (yes/no)? ")
            if response == "yes":
                resp = rc.get("/app_scopes/", timeout=30.0)
                app_scopes = json.loads(resp.content)
                app_scopes = sorted(app_scopes, key=lambda x: len(x["name"]))

                tree = Tree()

                scope_count = 0
                for app_scope in app_scopes:
                    if app_scope["name"].split(":")[0] == args.parent.split(":")[0]:
                        scope_count += 1
                        if len(app_scope["name"].split(":")) == 1:
                            tree.create_node(
                                app_scope["short_name"].replace("\n", " "),
                                app_scope["id"],
                            )
                        else:
                            tree.create_node(
                                app_scope["short_name"].replace("\n", " "),
                                app_scope["id"],
                                app_scope["parent_app_scope_id"],
                            )
                print(
                    "=============================== CURRENT ==============================="
                )
                tree.show()

            else:
                print("\nskipped!\n")
                # print("keystrokes: " + str(keystrokes) + '\n')

            aide.submit_statistics(
                tool_id="45799",
                pid=args.projectid,
                metadata={
                    "module": "annotations2scopes",
                    "report_savings": True,
                    "potential_savings": (len(add_scopes) + len(delete_scopes)) / 60,
                },
            )

        else:
            print("\nskipped!\n")
            quit()
    else:
        print("\nscopes in sync with annotations\n")


def delete_dependents(rc, resp, scope_id):
    for error in json.loads(resp.text)["details"]:
        for dependent in error["dependents"]:
            delete = True
            # policy
            if dependent["type"] == "ClusterEdge":
                url = "/openapi/v1/policies/"
            # filter
            elif dependent["type"] == "UserInventoryFilter":
                url = "/openapi/v1/filters/inventories/"
            # agent config intent
            elif dependent["type"] == "InventoryConfigIntent":
                url = "/openapi/v1/inventory_config/intents/"
            # # interface config intent
            # elif dependent['type'] == 'InventoryConfigIntentItem':
            #     url = ???
            # # forensics config intent
            # elif dependent['type'] == 'ForensicConfigIntent':
            #     url = ???
            # workspace
            elif dependent["type"] == "DataSet":
                url = "/openapi/v1/applications/"
                print(
                    "    "
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + " wait 15 min for deletion of dependent "
                    + dependent["type"]
                    + " "
                    + dependent["name"]
                )
            # scope
            elif dependent["type"] == "AppScope":
                print(
                    "    "
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + " wait 15 min for deletion of dependent "
                    + dependent["type"]
                    + " "
                    + dependent["name"]
                )
                delete = False

            if resp.status_code == 404:
                delete = False

            if delete:
                print(
                    "    delete dependent "
                    + dependent["type"]
                    + " "
                    + dependent["name"]
                )
                resp = rc.delete(url + dependent["id"])

                if resp.status_code == 200:
                    print(
                        "    "
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        + " "
                        + str(resp.status_code)
                        + " "
                        + resp.reason
                    )
                elif resp.status_code == 422:
                    delete_dependents(rc, resp, scope_id)
                    # delete_dependents(rc, resp, dependent['id'])
                elif resp.status_code == 404:
                    print(
                        "    "
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        + " wait 15 min for deletion of dependent "
                        + dependent["type"]
                        + " "
                        + dependent["name"]
                    )
                else:
                    print("    " + str(resp.status_code) + " " + resp.text)
    if resp.status_code == 404:
        delete = False

    if delete:
        print("    delete " + scope_id[0])
        resp = rc.delete("/app_scopes/" + scope_id[1])
        if resp.status_code == 200:
            print(
                "    "
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                + " "
                + str(resp.status_code)
                + " "
                + resp.reason
            )
        elif resp.status_code == 422:
            delete_dependents(rc, resp, scope_id)
            # delete_dependents(rc, resp, dependent['id'])
        else:
            print("    " + str(resp.status_code) + " " + resp.text)

    return


if __name__ == "__main__":
    main()
