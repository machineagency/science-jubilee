"""
This module should handle all interactions with the real world
"""
import image_processing as img
import numpy as np

import matplotlib
from matplotlib import pyplot as plt



def sample_point(jubilee, pipette, camera, RYB: tuple, volume: float, well, red_stock, yellow_stock, blue_stock, trash_well, show_frame = True):
    """
    Sample a specified point. 

    Inputs:
    jubilee: Jubilee Machine object
    Pipette: Jubilee library pipette object, configured
    Camera: Jubilee library camera tool
    RYB (tuple) - (R, Y, B) values - either 0-1 or 0-255.
    volume: total sample volume
    well: location to prepare sample
    red_stock: location for red stock 
    yellow_stock: location for yellow stock
    blue_stock: location for blue stock

    Returns:
    -------
    RGB - tuple RGB value of resulting solution
    """

    ########
    # Volume calculation code
    #################

    #print('Start of sample sequence position: ', jubilee.get_position())
    RYB = list(RYB)
    # get the volumes of each color
    if np.isclose(sum(RYB), 1):
        pass
    elif np.isclose(sum(RYB) ,255):
        RYB = [i/255 for i in RYB]
    else:
        raise AssertionError('Error: Volume fractions of RYB must add to 1 or 255')
    
    volumes = [vf*volume for vf in RYB]    

    print('Calculated RYB volumes, in uL: ', volumes)
    

    ###############
    # Liquid handling stuff
    ###############

    # pipette colors into well
    # pipette red:
    #pickup the red tip from rack
    jubilee.pickup_tool(pipette)
    #dirty check to make sure we are clearing z. need to fix whatever bug is causing this issue
    jubilee.move_to(z = 100)

    #print('Pipette picked up: ', jubilee.get_position()['Z'])
    #print('Tool offsets: ', jubilee.tool_z_offsets)

    #this is a mess to make sure we aren't pipetting more than 300 ul. Fix in transfer function

    #print('red tip: ', red_tip)
    try:
        red_tip = pipette.red_tip
    except AttributeError:
        pipette.red_tip = pipette.first_available_tip
        red_tip = pipette.red_tip
        pipette.increment_tip()

    if volumes[0] > 0:
        pipette.pickup_tip(red_tip)

        #print('Offsets after picking up tip: ')
        #print('Tool offsets: ', jubilee.tool_z_offsets)
            
        #print(f'Dispensing {volumes[0]} of red')
        #print('red tip: ', red_tip)
        if volumes[0] > 300:
            pipette.transfer(volumes[0]/2, red_stock, well, blowout = True)
            pipette.transfer(volumes[0]/2, red_stock, well, blowout = True)
        else:
            pipette.transfer(volumes[0], red_stock, well, blowout = True)
        # return tip to same location
        pipette.return_tip(location = red_tip)
    else:
        pass
    #print('Offsets after returning tip: ', jubilee.tool_z_offsets)

    # same for yellow
    
    try:
        yellow_tip = pipette.yellow_tip
    except AttributeError:
        pipette.yellow_tip = pipette.first_available_tip
        yellow_tip = pipette.yellow_tip
        pipette.increment_tip()

    if volumes[1] > 0:
        #print(f'Dispensing {volumes[1]} of yellow')
        pipette.pickup_tip(yellow_tip)
        if volumes[1] > 300:
            pipette.transfer(volumes[1]/2, yellow_stock, well, blowout = True)
            pipette.transfer(volumes[1]/2, yellow_stock, well, blowout = True)
        else:
            pipette.transfer(volumes[1], yellow_stock, well, blowout = True)
            # return tip to same location
        pipette.return_tip(location = yellow_tip)
    
    else:
        pass

    # for blue:
    # get a new tip
    #print('Next tip: ', pipette.first_available_tip)
    if volumes[2] > 0:
        pipette.pickup_tip()

        #print(f'Dispensing {volumes[2]} of blue')
        if volumes[2] > 300:
            pipette.transfer(volumes[2]/2, blue_stock, well, blowout = True)
            pipette.transfer(volumes[2]/2, blue_stock, well, mix_after = (275, 5), blowout = True)
            # discard tip 
        else:
            pipette.transfer(volumes[2], blue_stock, well, mix_after = (275, 5), blowout = True)
            # discard tip 
        pipette.drop_tip(trash_well)
    else:
        # add a mix here even if no blue
        pass
    
    #pipette.pickup_tip()
    #print('Offsets with tip: ', jubilee.tool_z_offsets)
    #pipette.drop_tip(trash_well)
    #print('offsets after dropping tip: ', jubilee.tool_z_offsets)




    #print('About to park pipette: ', jubilee.get_position()['Z'])
    jubilee.park_tool()
    #print('just parked pipette: ', jubilee.get_position()['Z'])
    #print('Tool offsets: ', jubilee.tool_z_offsets)
    
    # will this park the tool automatically?
    jubilee.pickup_tool(camera)
    #print('Just picked up camera: ', jubilee.get_position()['Z'])
    image = camera.get_well_image(well=well)
    if show_frame:
        plt.imshow(image)
        plt.show()
    #Camera.view_image(image, masked = True)
    #print('About to drop bed :', jubilee.get_position()['Z'])
    #jubilee.move(dz = 50)

    jubilee.park_tool()
    #print('just parked camera: ', jubilee.get_position()['Z'])
    #print('Tool offsets :', jubilee.tool_z_offsets)
    # do post-processing 
    RGB = img.process_image(image)
    
    return RGB, image