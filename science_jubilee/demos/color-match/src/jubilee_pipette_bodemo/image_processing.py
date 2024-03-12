import cv2
import numpy as np
import matplotlib.pyplot as plt

def process_image(f):
    """
    externally callable function to run processing pipeline
    
    takes an image as a bstring
    """
    image = f #cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    radius = 30
    masked_image = _mask_image(image, radius)
    values = _get_rgb_avg(masked_image)
    return values



def _mask_image(image, radius):

    mask = np.zeros(image.shape[:2], dtype = "uint8")
    cv2.circle(mask, (600, 600), radius, 255, -1)
    masked = cv2.bitwise_and(image, image, mask=mask)
    plt.imshow(masked)
    plt.show()
    return masked



def _get_rgb_avg(image):
    # bgr = []
    rgb = []
    for dim in [0,1,2]:
        flatdim = image[:,:,dim].flatten()
        indices = flatdim.nonzero()[0]
        if len(indices) > 0:
            value = flatdim.flatten()[indices].mean()
        else:
            value = 0
        rgb.append(value)

    # rgb = [bgr[i] for i in [2,1,0]]

    return rgb