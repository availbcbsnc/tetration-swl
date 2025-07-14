# Tetration Python Tools

<p align="center">
<a href="https://wwwin-github.cisco.com/pages/AIDE/User-Guide/"><img alt="AIDE: essentials" src="./docs/images/aide-essentials.svg"></a>
<a href="https://cxtools.cisco.com/cxestore/#/toolDetail/45799"><img alt="CX eStore Tool ID" src="https://img.shields.io/badge/TOOL%20ID-45799-blue"></a>

</p>

A collection of CRUD tools and other utilities written in python for Tetration.

create, read, update, delete:

- scopes
- filters
- applications

utilities:

- annotations
- applications
- flows
- convos
- sensors

misc:

- xmind
- miniadm

## Documentation

All the documentation for this project can be found on the following [link](https://wwwin-github.cisco.com/pages/AIDE/tetration-python-tools/)

## Getting Started

See installing section below for notes on how to deploy the project on a live system.

### Prerequisites

- Tetration `api_key` and `api_secret` are needed, create a file `credentials.json` as it's shown in the following example:

```json
{
  "api_key": "a9a107a94dcf4a2345666b04c060811117",
  "api_secret": "4de709b6dc857dh733nsn78023a4d04b4afxxa8fad"
}
```

- Tetration cluster ip or name, create a file `endpoint.json` as it's shown in the following example:

```json
{
  "api_endpoint": "https://name.domain.com/"
}
```

- Python 3.x

### Installing

1. Install using `pip install git+https://wwwin-github.cisco.com/AIDE/tetration-python-tools.git`

## Usage

### Anything to Annotations

```bash
$ anything2annotations --h
usage: anything2annotations [-h] -f FILE -i IP [-m MASK] -n NEW -s SHORT [-l LONG] [-p PARENT] [-d DELIMITED] [-a ADD] [-k KEEP] [-e EXCLUDE]
                            [-c CASE] [-R REGEX] [-S SEARCH] [-V VLOOKUP] [-C COMBINE] -P PROJECTID [--log_level LOG_LEVEL]

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
  -R REGEX              replace regex with sub (field=regex:sub,regex:sub;field=regex:sub,regex:sub) OPTIONAL special chars [comma] [colon]
                        [equals] [semicolon]
  -S SEARCH             search source for regex and assign value to dest (source=regex:dest=value,source=regex:dest=value) OPTIONAL special
                        chars [comma] [colon] [equals]
  -V VLOOKUP            lookup key in external file, replace dest with column index (filename:key;index1=dest1,index2=dest2) OPTIONAL
  -C COMBINE            assign space delimitted fields to dest (dest1=field1,field2,field3;dest2=field4,field5) OPTIONAL
  -P PROJECTID, --pid PROJECTID
                        Project ID
  --log_level LOG_LEVEL
                        The log level to be used. (default: logging.CRITICAL)
```

```bash
$ python anything2annotations.py -f snow.csv -i "IP Address" -n APPLICATION -s "Sys Code:SYSCODE" -l "Service Id:DESCRIPTION" -p "Application Layer:APPLICATION_LAYER" -d "Support group:APP_SUPPORT_GROUP,Group email:APP_SUPPORT_EMAIL" -k "Fully qualified domain name:FQDN,Location:LOCATION,HSupport group:HOST_SUPPORT_GROUP,Class:OS,Environment:LIFECYCLE" -e "Status=Absent;State=Missing,Retired" -c upper -R "Environment=Development:DEV,Production:PROD,System Test:TEST,System Integration:SI;Service Id=[colon].*:" -a APPLIANCE=A,SOURCE=SNOW -V "syscodes.csv:Sys Code;2:Service Id,3:Application Layer"

regex substitution

vlookup

transposing

concatenating

formatting

rows: 40128
discarded: 699

final: 6391
shared: 2096

created: annotations_snow.csv
```

### Annotations to Scopes

```bash
$ annotations2scopes --h
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


$ python annotations2scopes.py -p Example -s class:loc:env:app

building scope tree per annotations

warning: orphaned 10.1.0.1 Example:internal:campus::app7
warning: orphaned 10.1.0.2 Example:internal:campus::app8
warning: orphaned 10.4.1.1 Example:internal:common::ntp
warning: orphaned 10.4.1.2 Example:internal:common::smtp
warning: orphaned 10.4.1.3 Example:internal:common::dns

comparing to configured scope tree


ips (total/orphaned/scoped): 18/5/13

scopes (current/add/delete/future): 1/21/0/22

show scope tree (yes/no)? yes
=============================== CURRENT ===============================
Example

================================= NEW =================================
Example
├── internal
│   ├── campus
│   ├── common
│   ├── datacenter
│   │   ├── dev
│   │   │   ├── app1
│   │   │   ├── app2
│   │   │   ├── app3
│   │   │   ├── app4
│   │   │   ├── app5
│   │   │   └── app6
│   │   └── prod
│   │       ├── app1
│   │       ├── app2
│   │       ├── app3
│   │       ├── app4
│   │       ├── app5
│   │       └── app6
│   └── regional offices
├── partner
└── public cloud


configure scopes (yes/no)? yes
add Example:partner
add Example:internal
add Example:public cloud
add Example:internal:common
add Example:internal:campus
add Example:internal:datacenter
add Example:internal:regional offices
add Example:internal:datacenter:prod
add Example:internal:datacenter:dev
add Example:internal:datacenter:dev:app3
add Example:internal:datacenter:dev:app5
add Example:internal:datacenter:dev:app6
add Example:internal:datacenter:prod:app5
add Example:internal:datacenter:dev:app2
add Example:internal:datacenter:prod:app6
add Example:internal:datacenter:prod:app3
add Example:internal:datacenter:dev:app4
add Example:internal:datacenter:prod:app1
add Example:internal:datacenter:dev:app1
add Example:internal:datacenter:prod:app4
add Example:internal:datacenter:prod:app2

add 21 (yes/no)? yes
1/21 create Example:partner
    2020-05-26 10:15:18 200 OK
2/21 create Example:internal
    2020-05-26 10:15:18 200 OK
3/21 create Example:public cloud
    2020-05-26 10:15:19 200 OK
4/21 create Example:internal:common
    2020-05-26 10:15:19 200 OK
5/21 create Example:internal:campus
    2020-05-26 10:15:20 200 OK
6/21 create Example:internal:datacenter
    2020-05-26 10:15:20 200 OK
7/21 create Example:internal:regional offices
    2020-05-26 10:15:20 200 OK
8/21 create Example:internal:datacenter:prod
    2020-05-26 10:15:21 200 OK
9/21 create Example:internal:datacenter:dev
    2020-05-26 10:15:21 200 OK
10/21 create Example:internal:datacenter:dev:app3
    2020-05-26 10:15:22 200 OK
11/21 create Example:internal:datacenter:dev:app5
    2020-05-26 10:15:22 200 OK
12/21 create Example:internal:datacenter:dev:app6
    2020-05-26 10:15:22 200 OK
13/21 create Example:internal:datacenter:prod:app5
    2020-05-26 10:15:23 200 OK
14/21 create Example:internal:datacenter:dev:app2
    2020-05-26 10:15:23 200 OK
15/21 create Example:internal:datacenter:prod:app6
    2020-05-26 10:15:23 200 OK
16/21 create Example:internal:datacenter:prod:app3
    2020-05-26 10:15:24 200 OK
17/21 create Example:internal:datacenter:dev:app4
    2020-05-26 10:15:24 200 OK
18/21 create Example:internal:datacenter:prod:app1
    2020-05-26 10:15:24 200 OK
19/21 create Example:internal:datacenter:dev:app1
    2020-05-26 10:15:25 200 OK
20/21 create Example:internal:datacenter:prod:app4
    2020-05-26 10:15:25 200 OK
21/21 create Example:internal:datacenter:prod:app2
    2020-05-26 10:15:25 200 OK
commit scope changes
    2020-05-26 10:15:25 200 OK

ips (total/orphaned/scoped): 18/5/13

scopes (previous/add/delete/current): 1/21/0/22

show scope tree (yes/no)? no

skipped!

```

## Contributing

If there is a process for others to contribute to this tool, detail it in a CONTRIBUTING.rst file and reference it here using syntax like:

[Contribution guidelines for this project](./.github/CONTRIBUTING.rst)

## Authors

## License

This project is covered under the terms described in [LICENSE](./LICENSE)

## Acknowledgments
