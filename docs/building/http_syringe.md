---
title: HTTP Syringe
---

(http-syringe)=
# HTTP Syringe Tool

The HTTP Syringe tool is one adaptation of the [Digital Pipette tool developed by Naruki Yoshikawa et. al](https://pubs.rsc.org/en/content/articlehtml/2023/dd/d3dd00115f) to the Jubilee platform. This adaptation adds a Jubilee tool plate and parking post wings to the tool and adapts the control interface to integrate with the science-jubilee library. This tool uses a linear servo actuator mounted in a 3D printed frame to drive a disposable plastic syringe. The servo is controlled through a raspberry pi, which exposes an HTTP interface to interact with the science-jubilee library client for this tool. This tool is similar in principle to the other Jubilee [syringe tool](./syringe_tool.md). This tool uses linear servo motors instead of stepper motors and leadscrews. This makes this version lighter, easier to build, and extensible to a multi-tool setup with fewer duet boards. The stepper motor version will provide more force for handling viscous liquids.

### Pros of this tool
- Low cost liquid handling - this tool can be built for a per-tool cost of around $80USD, with some additional control hardware costs spread across multiple tools. This is much cheaper than the [OT2 Pipette tool](./pipette_tool.md).
- Swappable liquid-contacting parts. Everything that comes into contact with liquids and their vapors is fast and easy to swap out, so you don't need to worry about damaging expensive equipment with incompatible solvents. You do still need to worry about solvent compatibility for safety and experimental fidelity reasons.
- Choice of syringe tips - this tool uses syringes with Luer-lock tips, which is the standard interface for syringe tips. This gives you access to a wide range of tips/needles for various purposes. Sharp, blunt, flexible, stout, long, short - there are endless options out there.
- Potentially faster batch dispensing compared to traditional pipette tool, especially for bulk liquid quantities
- No headspace volume. This tool allows you to remove all air from the plunger-barrel-liquid system. This results in better performance with volatile liquids (no headspace evaporation leading to dripping and inaccurate dispense) and better performance when injecting liquids into sealed containers, such as when using pre-slit silicone septa to manage evaporation

### Cons of this tool

- lower accuracy and precision. Performance is lower than the OT2 pipette for water.
- No disposable pipette tips. This tool places liquid to be transferred in direct contact with the syringe barrel. To perform multi-liquid transfers, multiple tools or a thorough rinse process are needed.

## Parts list

This Jubilee adaptation of the tool uses a single control box to manage several individual syringe tools. The linear servos are driven off of raspberry pi GPIO pins, so in practice the number of tools will be limited by how many you can fit on a Jubilee. 5 is likely the maximum on a standard Jubilee V2. All printed parts are printed in PLA.



### For each tool

You will need one set of these parts for each indivdual tool you want to build.

#### Parts to purchase

| Description | Quantity per tool | Vendor 1 | Est. total cost |
| --- |--- | --- | --- |
| Linear servo actuator, Actuonix L16-100-63-6-R | 1 | [Actuonix](https://www.actuonix.com/l16-100-63-6-r) | $70 |
| M12 4-pin connector | 1 | [Lonlonty via Amazon](https://www.amazon.com/gp/product/B09YLP4K5W/ref=ox_sc_act_title_2?smid=A3EPS00U1KMPT0&th=1) | $4.50 per tool (sold in 4 pack) |
| M12 4-pin panel mount socket | 1 | [Lonlonty via Amazon](https://www.amazon.com/gp/product/B0BBQTDLHP/ref=ox_sc_act_title_3?smid=A3EPS00U1KMPT0&th=1) |$4.25 per tool (sold in 4 pack) |
| M3 brass heat set inserts | 12 | [Mcmaster](https://www.mcmaster.com/94180A361/) | $4.30 |
| 22g Hookup wire | 18 feet | Any brand is fine | $ 3? |
| 1/8" expandable wiring sleeve | 6ft | [Alex Tech via Amazon](https://www.amazon.com/gp/product/B074GN12PY/ref=ox_sc_act_title_1?smid=A2N7NRZ9X3BHHN&th=1) | $ 1 ($13/100 foot roll) |
| Misc. M3 and M4 hardware | varies | [Suggested kit to have on hand](https://www.amazon.com/gp/product/B07L9MMN9K/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1) | $2ish |
| Jubilee tool vitamins (wedge plat and tool balls) | 1 set | Filastruder | |

Syringes:

The current printed parts are designed to hold either a [1cc](https://www.amazon.com/gp/product/B07VF8CKGL/ref=ox_sc_act_title_5?smid=A18RDK02R6I57P&psc=1) or [10cc](https://www.amazon.com/10ml-Syringe-Only-Luer-Lock/dp/B01DARHDV8/ref=sr_1_3?crid=157GJLC30XVJ9&dib=eyJ2IjoiMSJ9.JYh8OK67Yvbzp72tx29uGPg2PpjDkoZIzsEHqbYSZ7TYDGa-Sa4S9bgk6averhVPRhEEJLBaSeq55-h_R6KBy-3E__mDWWLcme8gDJF1JErycS3PMi3kNcYuwfLxHXUDP5t9UrDaUMRaovhOoNNO0yoqu2blQeJPCUe3FRBHP9loqN849YvCNJWKWEzBr71nXPECYZNnN9whmp4yb87-eWIGlAg91gXPcKN2ZjXPnkX6C0X8VHkihBx9TQ35pdH86HpgMS505LQlFKOdfIELqcExhh4P1VwwJeMGbCOaKWs.sSyVTbBx5DhOUQGO_iug8xDHJREEMmHR4Y9glbD2uC0&dib_tag=se&keywords=10mL+luer+lock+syringe&qid=1718385114&s=industrial&sprefix=10ml+luer+lock+syringe%2Cindustrial%2C102&sr=1-3) syringe. Specifically, they are designed around the ones listed. If you are using a different volume or brand, you may need to re-design the mounting interface. At the time of writing, both of the above listed options are out of stock, so shifting to a more reliable vendor may be worthwhile.

Tips: We use a variety of blunt-tip luer lock tips with our syringe tools. We like [these](https://www.amazon.com/PATIKIL-Dispensing-Industrial-Dispenser-Refilling/dp/B0D54JYHJW/ref=sr_1_3?crid=8U54ML0Q5WUU&dib=eyJ2IjoiMSJ9.lqbSIws96oCkUxH1IUWBeoqKI8IBdezGy_FkfO05G-UBV5-DZlUc070givTsPLRKbBQEKaZr6wG-HoViokRqMkQfyflPnY46FBKP6PLXuVWl4uAfd-NATXmoF3wk0A9WS2G_I_fT5FQ8TCb23iuE5L859UOixh29JzJnZWCchLsl4a_j0wrqF9PDTv4UlefOLnzpfGn_G3HQvdWgbbkWPgiZwbMcQkqD6nytF5QBoWo.J8J1qaeqtn5_aSEC7nXtrKesdgwb6mBToZGHfpkcbbE&dib_tag=se&keywords=20+gauge+2+inch+luer+lock&qid=1721855915&sprefix=20+gauge+2+inch+luer+lock%2Caps%2C129&sr=8-3) 20gauge, 50mm blunt tips for general liquid handling as they are stout enough to pierce silicone septa and long enough to aspirate liquid from the bottom of a 20cc scintillation vial.



#### Parts to print

##### Shared between 1cc and 10cc tool:

| Part Name | Quantity | Link | Print notes |
| --- | --- |--- |---|
| Tool platform upper | 1 | [platform_upper v5.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/shared/platform_upper%20v5.stl) | |
| Tool Template assembly | 1 | [tool_template_assembly v1.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/shared/tool_template_assembly%20v1.stl) | |
| Left tool wing | 1 | [left_tool_wing_v2.STL](https://github.com/machineagency/jubilee/blob/main/tools/jubilee_tools/tool_template/fabrication_exports/3d_printed_parts/left_tool_wing_v2.STL) | |
| Right tool wing |1 | [right_tool_wing_v2.STL](https://github.com/machineagency/jubilee/blob/main/tools/jubilee_tools/tool_template/fabrication_exports/3d_printed_parts/right_tool_wing_v2.STL)| |

##### For 1cc tool:

| Part Name | Quantity | Link | Print notes |
| --- | --- |--- |---|
| Tool platform lower 1cc | 1 | [platform_bottom_1cc v2.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/1cc_tool/stl/platform_bottom_1cc%20v2.stl) | |
| Barrel cover 1cc | 1 | [cover_1cc v3.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/1cc_tool/stl/cover_1cc%20v3.stl) | |
| Plunger holder 1cc | 1 | [holder_1cc v7.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/1cc_tool/stl/holder_1cc%20v7.stl) | Mind your supports and print orientation |
| Plunger holder clamp 1cc | 1 | [holder_clamp v2.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/1cc_tool/stl/holder_clamp%20v2.stl) | Mind your supports and print orientation |


##### For 10cc tool:

| Part Name | Quantity | Link | Print notes |
| --- | --- |--- |---|
| Tool platform lower 10cc | 1 | [platform_bottom_10cc v2.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/10cc_tool/stl/platform_bottom_10cc%20v2.stl) | Should be printed flat side down |
| Barrel cover 10cc | 1 | [cover_10cc v4.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/10cc_tool/stl/cover_10cc%20v4.stl) | |
| Plunger holder 10cc | 1 | [holder_10cc v2.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/10cc_tool/stl/holder_10cc%20v2.stl) | Mind your supports and print orientation |
| Plunger holder clamp 0cc | 1 | [holder_clamp v2.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/syringe_tool/10cc_tool/stl/holder_clamp%20v2.stl) | Mind your supports and print orientation |



### Control hardware

You will need one control module for each Jubilee you want to use the HTTP syringe tool on.

#### Parts to buy

| Description | Quantity per control box | Vendor 1 | Est. total cost | Notes |
| --- |--- | --- | --- | --- |
| Raspberry pi 4 8GB | 1 | [PiShip.us](https://www.pishop.us/product/raspberry-pi-4-model-b-8gb/) | $75 | This is flexible. You may need to change GPIO pin assignments in config if you use a different model. We use an 8GB, you may get away with less but we haven't tested. |
| Power distribution block | 1 | [OONO via Amazon](https://www.amazon.com/OONO-Position-Terminal-Distribution-Module/dp/B08TBXQ7H6/ref=sr_1_3?crid=2ZD59UP98KSSE&dib=eyJ2IjoiMSJ9.VDL0yrriSw98HH3HSdMQCPu5tR6vFn_NjP1MQDyjlVvZq11R6gfC8QEUImkzIuxZl3K45rECgXTy7UR1XbZMpJuJt9Lo49jD8egx4TtOViwwxhsSZhpGEcJBFf853l1VcLYOtsawSCovyp_athqycIeZ_EphVpPjTXWIBMoq5i90lFp2x6XdogyqCFs0Ykhf7E1LH0awGIW7vMrfwRbJvR61KKnl7QtyPtm5bWbgNmUWVxeqBXLPjU69BrEYLv43MGQsVOyxMHKXEfyifGAgGshT69ZpbV6wf1HMe5D4cow.qczkP7hsfwwzLTHg3t4G82QOWhHOCbJLC2rbQlEkjfQ&dib_tag=se&keywords=power+distribution+block&qid=1729535907&s=industrial&sprefix=power+dist%2Cindustrial%2C131&sr=1-3) | $11 | |
| 6V DC power supply | 1 |  [Amazon](https://www.amazon.com/Adapter-5-5x2-1mm-5-5x2-5mm-Compatible-Transformer/dp/B092V8X3BP/ref=sr_1_2?dib=eyJ2IjoiMSJ9.tHYpU3Y-55bU6BM_CfqZYlx-yR4MiHk1GtG07SLcHFGLOAPByDb2ujJqmuR51KiQJJ2k4V-0Z3n7CldXQ3ETL5FpiGHyatbHA-WNR2OcQjpTyc58Y4XWeoj3edFZheUrvvUK0mojRPqhw7UzrgsL4t4uvfThlVm5IcG6X8iqdtxLVz44LUGmczwgYUAWtht9J80D89duwXblc-ZDaGzKLMKl2KRjTYH1XRzpaBwS2Fo.hv2nWvmS6r5vVf0eeyb5AOdvKBntJ9iwJz1BwGM4L9E&dib_tag=se&keywords=6V+power+supply&qid=1729536066&sr=8-2) | $11 | You probably have one sitting in your box of cables somewhere |
| Panel mount barrel jack receptacle | 1 | [Amazon](https://www.amazon.com/Threaded-Adapter-Connector-Dustproof-lkelyonewy/dp/B091PS6XQ4/ref=sr_1_2?crid=288HCJKLPYV3P&dib=eyJ2IjoiMSJ9.0Q1S6sIiXe-kWvF8vq1JgzY8TBsTPqDVonVb7SyN9etA-gxjz6PUTxn8poH7016Shbk_X0MhAuM-OP2mkh6XacjCYxlHDNBa0lz1i5FC803dg3MH9OLnE-Af25lFkVaDH_7zgevY4h-X9wcTbku1aZD7XktAwlytzJvK930COp6k_M_nEKlVfIY9eNehtef69rwAW89MxRJ2PPMLgWRuYivmKq7eod-7V-88LbgKXQA.IJXnX9Fnqca85pJHn6URVh6XH1zX3Q5jff1i1H8N5Yk&dib_tag=se&keywords=panel+mount+barrel+connector&qid=1729536147&sprefix=panel+mount+barrel%2Caps%2C143&sr=8-2) | $1.5 (Sold in 8 pack) | Any other quick-connect plug for DC power will work here |


### Parts to print

This control support module is designed to fit onto the [Autonomous Formulation Lab](https://pubs.acs.org/doi/full/10.1021/acs.chemmater.2c03118) modular frame system. For use with Jubilee, modifying this box to mount to the back panel of Jubilee would make more sense.

| Part Name | Quantity | Link | Print notes |
| --- | --- |--- |---|
|Control support module | 1 | [module_main v2.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/control_box/stl/module_main%20v2.stl) | |
| Lid | 1 | [module_lid v3.stl](https://github.com/machineagency/science-jubilee/blob/main/tool_library/HTTPsyringe/designs/control_box/stl/module_lid%20v3.stl) | |

## Assembly Instructions

to come!
## Software configuration
to come!

## Using the tool
to come !


#### License

The original Digital Pipette tool, and this derivative work, are licensed under [CC4.0](https://creativecommons.org/licenses/by/4.0/)
