---
title: Installation Guide for Science Jubilee
---
# Installation

To install `science-jubilee`:

To install `science-jubilee`:

### Unix/Mac:

To set up `science-jubilee` on Unix/Mac:

- Clone the repository:  
  ```bash
  git clone https://github.com/machineagency/science-jubilee.git
  ```

- Navigate to the project directory:  
  ```bash
  cd science-jubilee
  ```

- Create a virtual environment:  
  ```bash
  python3 -m venv .venv
  ```

- Activate the virtual environment:  
  ```bash
  source .venv/bin/activate
  ```
  *Note: You should now see `(.venv)` to the left of your command line prompt! If you wish to leave the virtual environment, type `deactivate` from any directory.*

- Update pip:  
  ```bash
  python3 -m pip install --upgrade pip
  ```

- Install the package:  
  ```bash
  python3 -m pip install -e .
  ```

- Installation complete!  
  Whenever you try to run programs using `science_jubilee`, ensure the virtual environment is activated.

### Windows (Using Git Bash)

To set up `science-jubilee` on Windows using Git Bash:
- Download Git Bash.

- Clone the repository:  
  ```bash
  git clone https://github.com/machineagency/science-jubilee.git
  ```
  *Note: cloning may fail because of a copy-paste issue; manually typing the command will solve this.*

- Navigate to the project directory:  
  ```bash
  cd science-jubilee
  ```

- Create a virtual environment:  
  ```bash
  python -m venv .venv
  ```

- Activate the virtual environment:  
  ```bash
  source .venv/Scripts/activate
  ```
  *Note: In Git Bash, you can use the Unix-style `source` command instead of the Windows-specific activation scripts.*

- Update pip:  
  ```bash
  python -m pip install --upgrade pip
  ```

- Install the package:  
  ```bash
  python -m pip install -e .
  ```

- Installation complete!  
  Whenever you try to run programs using `science_jubilee`, ensure the virtual environment is activated.


## Jupyter Notebooks

To use `science_jubilee` from within Jupyter notebooks:

- If you do not already have JupyterLab installed, do so from outside of your virtual environment: `python3 -m pip install jupyterlab`.
- Activate the virtual environment where `science_jubilee` is installed.
- Add your virtual environment to Jupyter: `python3 -m ipykernel install --user --name=<your_kernel_name>`
- Launch JupyterLab: `jupyter lab`
- When creating notebooks, be sure to choose the kernel you just added!
