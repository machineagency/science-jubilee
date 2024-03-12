import numpy as np
import image_processing as img

import bayesopt.bayesian_optimizer as bayesian_optimizer
import bayesopt.model as model

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process import kernels

import jubilee_protocols

import matplotlib.pyplot as plt

import cv2

from IPython.display import display, clear_output


"""
This module should handle the bayesian optimization loop type stuff
"""

def BO_campaign(initial_data, acquisition_function, acq_kwargs, number_of_iterations, target_color, jubilee, pipette, camera, sample_volume, red_stock, yellow_stock, blue_stock, samples, trash_well, start_well = 0):
    """
    This should be a child-safed way to run BO on the platform

    initial data: The already acquired initial data points to seed BO
    acquisition function:
    number of iterations: number of samples to test in BO campaigncquisitions.optimize_EI
# acq_kwargs = {'xi':0.3}
    jubilee: jubilee object
    pipette: jubilee pipette object
    camera: jubilee camera object
    sample_volume: volume to make for sample, probably in mL but depends on pipette
    red_stock, yellow, blue stock: wells with stock location
    samples: labware object to make samples in. For now this only works with one piece of labware.    
    """
    n_points = 101 # number of grid points on sampling grid

    # define possible sampling grid
    available_points = get_constrained_points(n_points)
    # we know we are working with a 3-variable constrained design space here so can just hard-code that
    # instantiate a bayesian optimizer object
    kernel = kernels.Matern(nu = 1/2)
    internal_model = model.GaussianProcessModel(kernel, scale = True, alpha = 1e-5)

    bo = bayesian_optimizer.BayesianOptimizer(None, acquisition_function, internal_model, initial_data, valid_points = available_points, acq_kwargs = acq_kwargs)

    # check that we have enough sample wells for the number of iterations we want to run 

    assert len(samples.wells) > number_of_iterations, 'Error: Too many samples to test for number of wells in labware.'

    # get first set of points from model
    query_point = bo.campaign_iteration(None, None)[0]

    rgb_values_sampled = []
    ryb_points_sampled = []
    images = []
    scores = []


    # plt.ion()
#     fig, ax = plt.subplots(1,2, figsize = (20,8))

#     ax[0].set_title('Most Recent Image')
#     ax[1].set_title('Color Loss Plot')
#     ax[1].set_xlabel('Iteration')
#     ax[1].set_ylabel('Loss')

    for i in range(number_of_iterations):
        # query point from BO model
        # get well
        print(f'Starting iteration {i}')

        # figure out how to get the next well with the new setup
        well = samples[i+start_well]
        # run point in real world
        print(f'Dispensing into well {well}')
        print(f'RYB values tested: {query_point}')
        new_RGB, image = jubilee_protocols.sample_point(jubilee, pipette, camera, query_point, sample_volume, well, red_stock, yellow_stock, blue_stock, trash_well, show_frame = False)

        images.append(image)
        new_color = normalize_color(new_RGB)


        ryb_points_sampled.append(query_point)
        rgb_values_sampled.append(new_RGB)
        score = color_loss_calculation(target_color, new_color)
        scores.append(score)
        query_point = bo.campaign_iteration(query_point, score)[0]

        try:
            plot_results(rgb_values_sampled, target_color, image)#, fig, ax)
        except Exception as e:
            print(e)
            pass

    return ryb_points_sampled, rgb_values_sampled, images, score, bo

def plot_results(rgb_values_sampled, target_color, f):#, fig, ax):
    # get loss values
    loss_vals = [color_loss_calculation(target_color, normalize_color(rgb)) for rgb in rgb_values_sampled]
    norm_colors = [normalize_color(rgb) for rgb in rgb_values_sampled]
    # plot iteration vs. loss with color observed as marker color
    

    image = f #cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    # imgcv = cv2.imdecode(imgbuf, cv2.IMREAD_COLOR)
    # imgcv_rgb = imgcv[:,:,[2,1,0]]
    plt.figure(figsize=(20,8))
    plt.subplot(121)
    plt.imshow(image)
    plt.subplot(122)
    iteration_index = [idx+1 for idx in range(len(loss_vals))]
    plt.scatter(iteration_index, loss_vals, marker='o', color=norm_colors, s=300)
    # for i, loss in enumerate(loss_vals):
    #     ax[1].scatter(i, loss_vals[i], marker = 'o', color = norm_colors[i], s = 200)
    #     ax[0].imshow(image)

    plt.show()

    return


def get_constrained_points(n_points):
    """
    Get the available points in 3-dimensional sample space with volumetric mixing constraint
    """


    R = np.linspace(0, 1, n_points)
    Y = np.linspace(0, 1, n_points)
    B = np.linspace(0,1, n_points)

    # do a brute force constrained sampling to get points in the design space
    test_arr = np.array(np.meshgrid(R, Y, B)).T.reshape(-1,3)
    indices = np.where(test_arr.sum(axis = 1) != 1)[0]
    testable_points = np.delete(test_arr, indices, axis = 0)

    return testable_points

def initial_random_sample(testable_points, n_sample = 12):
    """
    Sample n_sample points from testable_points to get initial data
    """
    rng = np.random.default_rng(seed = 4)
    selected_inds = rng.integers(0, len(testable_points), n_sample)
    selected_points = testable_points[selected_inds, :]
   
    return selected_points


def color_loss_calculation(target_color, measured_color):
    """
    Get the score for a point
    """
    distance = [np.abs(np.array(t) - np.array(m)) for t, m in zip(target_color, measured_color)]
    score = np.linalg.norm(distance)

    return 1 - score


def normalize_color(RYB):
    """
    normalize 0-255 or 0-1 to 0-1
    """
    RYB = list(RYB)
    if np.any([v > 1 for v in RYB]):
        RYB = [i/255 for i in RYB]
    return RYB