---
title: Documentation Contribution Guidelines
---

(documentation-contribution-guidelines)=
# Documentation Contribution Guidelines

## Documentation Overview

Most development starts with a GitHub Issue. See more about issues on the [Development page](https://machineagency.github.io/science-jubilee/development/index.html). The documentation consists of the documentation pages (like this one) and inline code documentation to generate the code reference. The documentation pages can be found in `science_jubilee/docs/source`. We use [Sphinx](https://www.sphinx-doc.org/en/master/) to generate the documentation, which in turn uses the [Markedly Structured Text (MyST) Parser](https://myst-parser.readthedocs.io/). MyST provides flexibility in that you can use standard Markdown files while exposing the more advanced features of the ReStructuredText (RST) format. The inline code can be found immediately after all functions in the `science-jubilee` package.

See below for information on how the documentation is organized and how it can be modified. For simple edits (e.g., fixing typos or adding clarification), simply click the "Edit on Github" button at the upper-right of the corresponding page. To make and submit more involved changes to the documentation, please follow the same steps outlined in the [Code Contribution Guidelines](#code-contribution-guidelines).

### Building the Docs

If you install the `science-jubilee` conda environment, all of the packages necessary to build the documentation should be installed automatically (make sure to `conda activate science-jubilee`). Otherwise, you will need to run `pip install -r docs/requirements.txt` in your environment first. Then, run the following lines:

```bash
cd docs
make html
```

You can preview the changes in the `_build/html` folder, which is untracked by git, as specified in `.gitignore`. Within VS Code for example, you can install the [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) extension, right-click on `docs/_build/html/index.html`, and select "Open with Live Server" to dynamically view the documentation. Run `make html` within the `docs` folder each time you'd like to view the changes.

### Adding New Pages

If you are adding new documentation pages, make sure to add a target header at the top of your new `.md` file, just before the top-level heading:

```markdown
(my-target-header)=
# My Top-level Heading
```

Click the "Show Source" button on the upper-right of this page to see a real example in this project. Refer to https://myst-parser.readthedocs.io/ for more information.

### Adding Inline Documentation

'Docstrings' are specifically formatted comments in code which can be used to generate documentation. We use the Sphinx docstring format to generate our API reference. Please see the description [here](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html), and/or take a look at existing docstrings in the repository!
