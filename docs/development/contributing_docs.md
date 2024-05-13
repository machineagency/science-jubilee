---
title: Documentation Contribution Guidelines
---

(documentation-contribution-guidelines)=
# Documentation Contribution Guidelines

## Documentation Overview

Most development starts with a GitHub Issue. See more about issues on the [Development page](https://machineagency.github.io/science-jubilee/development/index.html). The documentation consists of the documentation pages (like this one) and inline code documentation to generate the code reference. The documentation pages can be found in `science_jubilee/docs/source`. We use [Sphinx](https://www.sphinx-doc.org/en/master/) to generate the documentation, which in turn uses the ReStructured Text markup language. The inline code can be found immediately after all functions in the `science-jubilee` package.

This page provides information on how the documentation is organized and how it can be modified. To make and submit changes to the documentation, please follow the same steps outlined in the Code Contribution Guidelines.

### Building the Docs

All of the packages necessary to build the documentation are specified in `setup.py`, so you should be immediately able to build the documentation. To do so, ensure the virtual environment is activated. Then:

```bash
cd docs
make html
```

You can preview the changes in the `build/html` folder; the build folder is added to `.gitignore` by default which means this won't be added to the repository.

### Adding New Pages

If you are adding new documentation pages, make sure to add a label at the top of your new `.md` file like so:

```rst
.. _

<label>:
```

where you should replace `<label>` (including the angle brackets) with your label name. Sphinx has a nice primer on using reStructured Text [here](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).

### Adding Inline Documentation

'Docstrings' are specifically formatted comments in code which can be used to generate documentation. We use the Sphinx docstring format to generate our API reference. Please see the description [here](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html), and/or take a look at existing docstrings in the repository!
