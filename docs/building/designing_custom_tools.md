---
title: Designing Custom Tools
---

(designing-custom-tools)=
# Designing Custom Tools

```{figure} _static/tool-template.png
:scale: 50 %

The shortcut to 3D modeling a tool with the right placements is to simply build on top of the CAD files in [the template folder](https://github.com/machineagency/jubilee/tree/main/tools/jubilee_tools/tool_template).
```

```{figure} _static/tool-template-reference-dims.png
:scale: 50 %

starting from scratch is also straightforward. To create a custom tool that locks into Jubilee's carriage, you must place the tool balls and the wedge plate in a specific location, specified in the [Tool Template Reference Dimensions](https://github.com/machineagency/jubilee/raw/main/tools/jubilee_tools/tool_template/references/tool_template_reference_dimensions.pdf), shown above.
```


```{figure} _static/tool-interference-diagram.png
:scale: 50 %

There are a few size constraints that may influence your tool's shape, shown above. A number of example tools are shown in the [Tool Interface Diagram PDF](https://github.com/machineagency/jubilee/raw/main/frame/references/tool_interface_diagram.pdf). Note that many of these constraints are soft. Using longer dowel pins on the parking post will allow for deeper tools. Also, moving the tool's active center past the leftmost line will result in a working tool that simply has a bit less Y-axis travel.
```
