# Name of Your Tool

<p align="center">
<a href="https://wwwin-github.cisco.com/pages/AIDE/User-Guide/"><img alt="AIDE: essentials" src="./docs/images/aide-essentials.svg"></a>
<a href="https://cxtools.cisco.com/cxestore/#/toolDetail/XXXXX"><img alt="CX eStore Tool ID" src="https://img.shields.io/badge/TOOL%20ID-XXXXX-blue"></a>

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

Note: see submodule README.md for details

## Getting Started

To interact with Tetration OpenAPI, scripts will require the Tetration UI FQDN, API key and secret, stored in enpoint.json and credentials.json respectively. By default, python scripts will first check cli params for paths, then parent directory and finally local directory. If json files are not found, user will be prompted for paths.

endpoint.json 

{
  "api_endpoint": "https://YOUR_TETRATION_UI_IP_OR_FQDN/"
}

credentials.json 

{
  "api_key": "YOUR_API_KEY",
  "api_secret": "YOUR_API_SECRET"
}

### Prerequisites

python 3

pip

$ pip install tetpyclient

Note: Any additional libraries required by submodules will noted in the submodule README.md

## Installing

$ git clone https://wwwin-github.cisco.com/AIDE/tetration-python-tools.git

## Usage

See submodule README.md

## Authors

Greg Jost
grjost@cisco.com

## License

This project is covered under the terms described in [LICENSE](./LICENSE)

## Acknowledgments

- Tetration Incubation
- Tetration Business Unit
- Tetration Development