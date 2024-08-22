---
title: Notes on traveling with Jubilee
---

(jubilee-travel)=
# Traveling with Jubilee

Updated August 21 2024


We have traveled internationally from the US to Mexico, Canada, and the EU with our Jubilee experimental automation platform. These are some lessons learned and best practices we have settled on. This is written from the perspective of traveling with a Jubilee system, but many of these considerations apply to any experiment automation equipment. This write-up is US-centric, but the ATA Carnet discussion is applicable internationally and the rest of the information should raise considerations for travel from other countries.

## Export Control

You should get your travel plans cleared by your institutions export control office. US export controls are intended to prevent the export of technologies related to weapons development. It is possible that these regulations will prevent export of lab automation equipment. With Jubilee, we avoided any issues with these regulations because the entire platform is open source, with build instructions and software freely available online.

## Customs

In the eyes of Customs, lab automation equipment is ‘commercial merchandise’ if it is used for demonstration/trade show purposes (e.x., demonstration at Accelerate conference) or experiments (e.x, travel to a beamline). This means that import duties could be levied on the equipment. There are a few ways to handle this. The best option will depend on how the equipment is packaged and how much it is worth. Simply not declaring the item can be risky. You could be theoretically be required to pay import duties on the equipment both when importing it into the country you are visiting and when re-importing it to the US. If the item is large enough to be packed in its own case, especially if the case is a pelican or flight case, you are likely to be questioned about it.
1.	Declare the item and pay the import duty and possibly taxes (sales, VAT, etc. depending on the locale). This can be a viable approach for low-value items and one-off travel. Make sure to do your research so you know what duty rate to expect, and come prepared with a well-documented valuation of the item so to avoid arbitrary valuations from customs agents. You should also fill out a [US CBP form 4455 certificate of registration](https://www.cbp.gov/document/forms/form-4455-certificate-registration) for your items. This will allow you to re-import to the items to the US without paying duties. To use this form, you will out the items you will be traveling with and present the form along with the items to a US customs officer before leaving the US. When you return to the US, present the form again. Note this does not help you avoid any duties with foreign customs.
2.	Obtain and use an ATA Carnet. This is the 'right' way to do temporary importation. An ATA Carnet is a 'passport for merchandise'. It is an internationally recognized customs document that allows you to temporarily import equipment without paying duties or taxes. To use an ATA carnet, you first purchase one from one of the authorized vendors in the US in advance of your trip. When purchasing, you will provide a list of all the items you plan to travel with including serial numbers and values. To use the carnet, you present it along with your items to customs each time the item is imported or exported. For a typical international trip, this means you get a stamp before you leave the US, on arrival at your destination country, before you leave your destination country, and upon return to the US. This does add a significant amount of time and logistics overhead to travel so plan accordingly. The cost of an ATA carnet starts at around $500, and the document is valid for one year. The price depends on the value of the listed goods. We use [Boomerang Carnets](https://www.atacarnet.com/) and would recommend them as they have excellent customer support.


Here are some specific tips for traveling with an ATA Carnet:
- When flying, you need to have your items inspected and Carnet stamped before they are checked for the first flight of your trip. Generally, you will tell the airline ticket agent that you need a Carnet stamped when you are checking in. They will call a customs officer, who will stamp your carnet at the check-in counter. Leave enough time for this when scheduling airport arrivals. Call the customs office ahead of time to confirm their hours and this procedure for calling an officer.
- It is recommended that you make the first flight of your trip an international flight if feasible. Technically, Carnets should be stamped at the port of departure, which is the last US airport the items transit through. A customs officer who wants to make your life miserable could require you to get the carnet stamped at your port of departure. If you have a connecting flight within the US and are checking your equipment, this would require you to claim your baggage at your connection, get your carnet stamped, re-check your bags, and clear security again – basically impossible on most connections. If a direct international departure isn't feasible, reasonable customs officers should be able to stamp you out at the first flight of your trip. Consider calling customs at your airport to make sure this will work before planning your trip.
- When you are having your carnet stamped on arrival at your foreign destination, ask  about procedures for finding a customs officer and getting your carnet stamped on departure.
- There are 2 ways to fill out the itemized list of equipment on the carnet: individually itemizing every component, and the ‘single line item’ approach. For custom, integrated equipment, it is possible to list the entire set of equipment as one line item with a made up serial number. For example, ‘Automated synthesis machine, serial number 1’. Then label each individual component in the shipment as ‘Integral component of automated synthesis machine, SN#1’ or something similar. We have known researchers who have successfully used this approach. It does give flexibility to add or modify equipment without re-printing your carnet. The itemized approach, on the other hand, requires you to pre-plan and list every component you will be traveling with. This can be more restrictive. However, the itemized list is what customs officers are used to seeing so it may raise fewer questions. In our experience, customs officers will ask to see one item with a serial number to match to the list. I make sure to list at least one serial number, even if it is for something trivial like an ethernet switch.

# Packing and transport

A major advantage of the Jubilee platform is it’s packability. With reasonable effort, Jubilee can be packed as airline checked baggage, greatly simplifying logistics compared to systems that require crating and shipping. Here is how we fly with our Jubilee and associated equipment:
-	We pack Jubilee by collapsing the Z axis. We replace all the vertical extrusion components with the 80mm extrusion pieces used to square the frame during assembly which reduces the total height including feet to ~10". We cut our 80mm extrusions down even further to save more space.
-	A major concern in packing for flying is weight. Most airlines have a 50 pound weight limit before (expensive) overweight fees kick in. Jubilee with tools is generally around 40 pounds. We generally pack Jubilee into two bags: One for the main motion platform top and bottom frame, and one for the Z axis components, bed, Jubilee tools, hand tools, spares, and other components. Paying for a second checked bag is generally much cheaper than paying overweight fees.
-	You will need some sort of case for Jubilee. We have tried a pelican case and a conventional suitcase before settling on a custom flight case. Finding a pelican case large enough to fit the Jubilee frame requires using a bulky, airline-oversized, and heavy case. A regular suitcase, on the other hand, provides little protection. We had a custom flight case made to fit Jubilee. It weighs 20 pounds, has an aluminum frame, and fits a collapsed Jubilee perfectly while staying within airline size requirements. We had ours made at [Custom Crating](https://customcrating.com/) in Seattle. Pricing is in line with an appropriately sized Pelican case. As a second bag, we use a regular suitcase as we are less concerned about protection for the non-frame components.
-	Pelican cases and flight cases will be treated as oversize baggage, even if they are not. This seems to greatly increase the risk of your bag being left behind at your departure airport. Given this, we fly with AirTags in our cases to assist with tracking down a lost Jubilee. It is also advisable to give yourself some extra time between your arrival and any activities that require a Jubilee to account for this increase risk of baggage issues.

![image](https://github.com/user-attachments/assets/cef3dc4e-68fc-47a4-9ce2-33b39580ee06)

_[[Source](https://jubilee3d.com/index.php?title=Specs#/media/File:Jubilee_overall_dimensions.png)]. Dimensions in mm. Equivalent to: 23.78" x 18.74" x 21.97". B2: Top-view. A2: side view._

## Products

### Jubilee in assembled state (untested)
1. [Pelican 0370](https://www.pelican.com/us/en/product/cases/cube-case/protector/0370/) (tight tolerance in longest dimension, likely to the point of needing to remove the Pelican foam, heavy)
2. [Outdoor Square Cushion/Cover Storage Bag](https://www.amazon.com/gp/product/B0BC8PTRHR/) (ample space, but requires significant custom padding/foam and at least one heavy duty cardboard insert at the bottom)
3. Custom ATA case 23" W x 28" D x 26" H (including foam). Standard Duty 3/8" Plywood. 2" foam all sides. (needs to be verified). E.g., [through Roadcases](https://www.roadcases.com/custom-quote-pull-along-case/) or a local ATA manufacturer. Note that lead times can be long (weeks).
4. Corrugated box [28" x 28" x 28"](https://www.uline.com/Product/Detail/S-4433/Corrugated-Boxes-200-Test/28-x-28-x-28-Corrugated-Boxes) (no hand holes)

Perhaps also:
1. Corrugated box [26" x 26" x 26"](https://www.uline.com/Product/Detail/S-4190/Corrugated-Boxes-200-Test/26-x-26-x-26-Corrugated-Boxes) (no hand holes)
2. Double-walled corrugated box [25" x 25" x 25"](https://www.uline.com/Product/Detail/S-22118/Heavy-Duty-Boxes/25-x-25-x-25-275-lb-Double-Wall-Corrugated-Boxes) (no hand holes)
3. [Triple-wall cardboard 24" x 24" x 24"](https://www.uline.com/Product/Detail/S-13331/Bulk-Cargo/24-x-24-x-24-1100-lb-Triple-Wall-Boxes) (no hand holes)
4. [Triple-wall cardboard 30" x 30" x 30"](https://www.uline.com/Product/Detail/S-11301/Bulk-Cargo/30-x-30-x-30-1100-lb-Triple-Wall-Boxes) (no hand holes)
5. Corrugated Boxes with hand holes [24" x 24" x 24"](https://www.uline.com/Product/Detail/S-14213/Moving-Boxes/24-x-24-x-24-Corrugated-Boxes-with-Hand-Holes)

### Jubilee in height-reduced state
1. [Pelican 1640](https://www.pelican.com/us/en/product/cases/transport-case/protector/1640/)
2. Custom ATA case 23" W x 28" D x 14" H (including foam). Standard Duty 3/8" Plywood. 2" foam all sides. (needs to be verified). E.g., [through Roadcases](https://www.roadcases.com/custom-quote-pull-along-case/) or a local ATA manufacturer. Note that lead times can be long (weeks).
