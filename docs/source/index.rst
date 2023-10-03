.. science_jubilee documentation master file, created by
   sphinx-quickstart on Mon Oct  2 14:56:41 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Science Jubilee's Documentation!
===========================================
.. image:: ../../wiki/images/pipetting.gif
   :width: 600
   :align: center
   :alt: A looping gif of a pipette tool dispensing blue liquid.

What is a Science Jubilee?
--------------------------

This wiki includes information for lab automation using `Jubilee <https://jubilee3d.com/index.php?title=Main_Page>`_- which is, in turn, an open-source & extensible multi-tool motion platform. If that doesn't mean much to you, you can think of it as a 3D printer that can change its tools. This repository contains information for outfitting a Jubilee with tools and associated control software for various lab automation applications. 

Currently, we include tools + software which support broad application areas including liquid handling (using 10cc/50cc syringe and OpenTrons Pipette), imaging (using top-down, side-facing cameras), and sample manipulation (using 10cc syringe, inoculation loop).

While these applications might cater exactly to your planned use case, they most likely will not! Our goal here is not to provide all the tools needed to automate an experiment, but rather to lower the threshold to automation in a way that allows scientists design and reuse systems- without compromising the level of control over the experiment. Hopefully, the examples here provide a foundation for you to design all sorts of niche experiments!

How to Use the Documentation
----------------------------
This wiki is primarily concerned with configuring and operating a Jubilee for scientific experiments, including documentation & examples. We encourage you to poke around the examples to get a feel for what you can do! That said, designing an experiment first requires building a Jubilee. This wiki also contains information to help scientists to get started with Jubilee more generally. 

If you want to build a Jubilee...
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Resources to build a Jubilee are consolidated on the `Jubilee Build Resources <https://github.com/machineagency/science_jubilee/wiki/Jubilee-Build-Resources>`_ page. All the parts needed to build a Jubilee have been assembled into a kit, but note that if you want to use the tools discussed on this page, there are additional parts & assembly required (see **If you want to make a Duckbot** section below).
* We've also put together a `video series <https://www.youtube.com/watch?v=8JUbr9aU8eQ>`_ which guides you through the assembly instructions


If you want to set up your Jubilee for laboratory automation...
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* This means you already have a fully functioning Jubilee! You can head over to the `Making a Science Jubilee <https://github.com/machineagency/science_jubilee/wiki/Making-a-Science-Jubilee>`_ page for more information on building the various tools. 
* While the examples in this wiki will often use multiple or all of our example tools, note that there is no requirement to build every tool. 

If you want to operate a Science Jubilee...
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* This means you have a fully functioning Jubilee, outfitted with specific tools relevant to your application! Documentation on the software provided in this repository can be found on the `Operating a Science Jubilee <https://github.com/machineagency/science_jubilee/wiki/Operating-a-Science-Jubilee>`_ page. You can also look at the `Examples <https://github.com/machineagency/science_jubilee/wiki/Examples>`_, or consult the `Reference <https://github.com/machineagency/science_jubilee/wiki/Reference>`_.


If you have questions...
^^^^^^^^^^^^^^^^^^^^^^^^
* For questions or issues relevant to this project in particular, you can `create a new issue <https://github.com/machineagency/science_jubilee/issues>`_ in this github repo.
* For questions about the Jubilee in general, be sure to check out the `Jubilee <https://jubilee3d.com/index.php?title=Main_Page>`_ project page. There's a lot of information there!
* There's also an active community of Jubilee builders & extenders on Discord. For general questions, there's a ton of expertise to be found there, and you'll often get a quick reply for troubleshooting. See **Join the Community!** below.

Join the Community!
^^^^^^^^^^^^^^^^^^^
* Whether you've built a Jubilee or are just interested in what sorts of things other people are up to, we encourage you to `join the Jubilee Builders & Extenders Discord <https://discord.gg/jubilee>`_! There's a large community of Jubilee builders doing all sorts of things there; you might be particularly interested in the `#lab-automation` channel.
* For a more focused discussion, you can also join our `Open Source Lab Automation Discord <https://discord.com/invite/j9Bqv3djvN>`_!

API Reference
-------------

.. toctree::
   :maxdepth: 2



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
