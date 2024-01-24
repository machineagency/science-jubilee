# 🔬🧪 Science Jubilee ⚡⚙️
### Controlling Jubilees for Science!

<p align="center"><img src="./docs/images/pipetting.gif" width="800"/></p>

This repository hosts files to build and control a [Jubilee](https://jubilee3d.com/index.php?title=Main_Page) for scientific applications. The core of the software is a Python interface for Jubilee to navigate labware installed in the machine. We currently provide assembly instructions, control software, and examples for various tools including OT-2 pipettes, syringes, and cameras. While these tools might cater exactly to your planned use case, they most likely will not! We share these files as a starting point rather than an endpoint: we also provide instructions for developing new tools and associated software for controlling them. We hope you will build new tools for your application and contribute them back to the community for others to use and extend 🛠️

_Check out the [Documentation](https://machineagency.github.io/science_jubilee/) to get started!_


## Overview
### Hardware
This repository is designed to be used with the Jubilee platform, outfitted with tools for laboratory automation. Jubilee an open-source & extensible multi-tool motion platform—if that doesn't mean much to you, you can think of it as a 3D printer that can change its tools. You can read about [Jubilee](https://jubilee3d.com/index.php?title=Main_Page) more generally at the project page. 

### Software
The software here is intended to control Jubilee from Python scripts or Jupyter notebooks to design and run experiments. The folders are organized as follows:
```
calibration/                 # notebooks to support machine & tool setup/calibration
tool_library/                # design files, assembly instructions, & configuration info for all tools & plates
science_jubilee/
├── Machine.py               # jubilee machine driver
├── tools/
│   ├── configs/             # all tool configs are here
│   ├── Tool.py              # base tool class
│   └── ...                  # all tool modules are here
├── decks/
│   ├── configs/             # all deck configs are here
│   ├── Deck.py              # base deck class
│   └── ...                  # all deck modules are here
└── labware/
    ├── labware_definitions/ # all labware definitions are here
    └── Labware.py           # base labware class
```

### Labware and Wetware
The basic functionality supported by this software is intended to be used with a custom deck which accommodates up to 6 standard sized microplates. 

### Using science_jubilee
You can import and use science_jubilee modules by importing the modules you need at the top of your python file/notebook. For example, if we want to pipette using a lab automation deck, we might write:
```python
from science_jubilee.Machine import Machine                             # import machine driver
from science_jubilee.decks.LabAutomationDeck import LabAutomationDeck   # import lab automation deck module
from science_jubilee.tools.Pipette import Pipette                       # import pipette module
...                                                                     # you can import other decks/tools here, or make your own!
```
We can then make use of these modules in our code:
```python
m = Machine()                                                  # connect to your jubilee
deck = m.load_deck(deck_config_name)                           # setup your deck
tip_rack = deck.load_labware(opentrons_96_tiprack_300ul, 0)    # install an opentrons tip rack in slot 0 of the deck
pipette = Pipette(<index>, <name>, <tip_rack>, <config_file>)  # instantiate your pipette tool
m.load_tool(pipette)                                           # configure the pipette for use on the machine
...
```





