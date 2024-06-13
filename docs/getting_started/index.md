---
title: Getting Started with Science Jubilee
---

(getting-started)=
# Getting Started

## Installation

```{eval-rst}
.. card:: Installation
    :class-card: intro-card
    :shadow: md

    Instructions for installing ``science_jubilee``, including integration with Jupyter notebooks.

    +++

    .. button-ref:: installation
        :ref-type: ref
        :click-parent:
        :color: secondary
        :expand:

        Installation Guide
```

## Overview

`science_jubilee` provides a Python interface to operate a Jubilee. It is comprised of:
- a `Machine`, which controls the Jubilee motion platform;
- `tools`, which provide task-specific functionality;
- `decks`, which can be attached to the Jubilee bed plate;
- and `labware` to be used on the machine.

These tutorials focus on applications using a Lab Automation deck which holds 6 standard sized microplates, thus allowing Jubilee to navigate between labware wells. However, there is no requirement to use the Lab Automation deck, and you might find it useful to develop alternative decks for your application!

```{eval-rst}
.. grid:: 1 2 2 2
    :gutter: 4
    :padding: 2 2 0 0
    :class-container: sd-text-center

    .. grid-item-card:: ``science_jubilee`` Primer
        :class-card: intro-card
        :shadow: md

        An introduction to key concepts, including: G-Code, coordinate systems, and an overview of the ``science_jubilee`` Python modules.

        +++

        .. button-ref:: primer
            :ref-type: ref
            :click-parent:
            :color: secondary
            :expand:

            Primer

    .. grid-item-card:: New User Guide
        :class-card: intro-card
        :shadow: md

        A complete start-to-finish walkthrough on running an experiment on Jubilee, starting with purchasing a machine.

        +++

        .. button-ref:: new-user-guide
            :ref-type: ref
            :click-parent:
            :color: secondary
            :expand:

            New User Guide


    .. grid-item-card:: Intro to the Machine Driver
        :class-card: intro-card
        :shadow: md

        Control the Jubilee motion platform and pickup tools using ``science_jubilee``

        +++

        .. button-ref:: machine-intro
            :ref-type: ref
            :click-parent:
            :color: secondary
            :expand:

            Machine Tutorial

    .. grid-item-card:: Lab Automation Deck and Labware
        :class-card: intro-card
        :shadow: md

        Set up a lab automation deck and navigate wells using standard labware.

        +++

        .. button-ref:: deck-guide
            :ref-type: ref
            :click-parent:
            :color: secondary
            :expand:

            Lab Automation Deck Tutorial

    .. grid-item-card::  Pipetting Intro
        :class-card: intro-card
        :shadow: md

        Use the lab automation deck and the pipette tool to run a serial dilution.

        +++

        .. button-ref:: pipette-guide
            :ref-type: ref
            :click-parent:
            :color: secondary
            :expand:

            Serial Dilution Pipetting Tutorial

    .. grid-item-card::  Color Mixing Demo Guide
        :class-card: intro-card
        :shadow: md

        Run an autonomous optimization experiment on Jubilee.

        +++

        .. button-ref:: color-mixing-setup
            :ref-type: ref
            :click-parent:
            :color: secondary
            :expand:

            Color Mixing Demo Guide
```

```{toctree}
:hidden:
installation
primer
new_user_guide
machine_intro
deck_guide
pipette_guide
color_mixing_setup
```
