# specimens2illustrations

## About

This repository includes scripts to process botanical monographs published in the Open Access journal [PhytoKeys](https://phytokeys.pensoft.net).
The data included in the monograph can be used to build multi-modal datasets, such as:
- herbarium specimen images plus the textual descriptions of the species represented
- herbarium specimen images plus the scientific illustrations created using the specimen as a reference

## How to use

### In remote infrastructure (continuous integration in github actions)

This is the simplest way to run the software and to get an understanding of what it is doing, as you don't need to install any software locally.

1. Navigate to the `actions` tab of the repository (see [screenshot](https://github.com/KewBridge/specimens2illustrations/assets/3758694/163fcd30-311d-4f73-84ce-10bf1463275a))
2. Click `Makefile CI` in the left hand sidebar, and then on the `run workflow` dropdown. In the dropdown, click on the green `run workflow` button (see [screenshot](https://github.com/KewBridge/specimens2illustrations/assets/3758694/737ff333-9f4a-4984-96c8-d8b2fb02e488))
3. Wait a moment and you will see a new workflow run appear at the top of the list. (see [screenshot](https://github.com/KewBridge/specimens2illustrations/assets/3758694/4d6636a6-f3cc-44dc-895e-eca60326bdd8))
4. Click on the workflow to see the steps being executed (see [screenshot](https://github.com/KewBridge/specimens2illustrations/assets/3758694/661daf83-1c1e-4162-b120-9fb544a84aac))
5. Click on the step `build` to see the output of the actual commands (see [screenshot](https://github.com/KewBridge/specimens2illustrations/assets/3758694/dce9027a-586f-461b-9796-b8e22860561c))
6. When the build has completed, you can access the products of the build (named `data`) in the artifacts list at the bottom of the screen (see [screenshot](https://github.com/KewBridge/specimens2illustrations/assets/3758694/8cc2f05f-5e99-4002-b7ed-d468f244cf4d))

### Locally (on your own machine)

#### Pre-requisities
You will need a git client in order to get the code from github. 
To run the software you'll need `python` installed on your local machine, and the dependency management tool `make`. See the useful links section below for resources about using and understanding the tool make. 

#### How to run
1. Open a command line shell
2. Clone the github repository into a directory on your local machine
3. `cd` into the new directory
3. Install python dependencies: `pip install -r requirements.txt`
4. Use make to generate the target (the processed text files): `make all`

Note: as the `Makefile` is configured to define dependencies between targets, it will first execute commands to download the XML format data using the list of DOIs supplied. (DOI == Digital Object Identifier, a resolvable persistent identifier for a bibliographic work). The DOIs are defined as a variable in the first line of the Makefile. Then the XML format data is processed using `xml2illustrationdata.py` to generate the processed text file. See comments within the makefile for more details.

## Useful links

- Make
    - Introduction to [reproducibility with make](https://the-turing-way.netlify.app/reproducible-research/make.html)
    - Manual:
        - File name functions: https://www.gnu.org/software/make/manual/html_node/File-Name-Functions.html
        - Variables: https://www.gnu.org/software/make/manual/html_node/Automatic-Variables.html
        - Special targets (eg .PRECIOUS): https://www.gnu.org/software/make/manual/html_node/Special-Targets.html
- Discussions about building multi-modal datasets:
    -   Specimens and illustrations - [discussion #1](https://github.com/orgs/KewBridge/discussions/1)
    -   Specimens and textual descriptions (TBC)

## Problems / questions

Please raise an issue in the [issue tracker](https://github.com/KewBridge/specimens2illustrations/issues) for this repository.

## Contributing

Contributions are welcome. Please first submit an issue describing the problem being fixed, or the new functionality proposed to be added - and include a reference to the relevant issue in the commit message, for traceability.

## Contacts

- Nicky Nicolson (n.nicolson@kew.org)
