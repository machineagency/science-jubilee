"""
Utilities to compute metrics
"""
import numpy as np

def calculate_top_percent(testable_points, y_true, sampled_points, threshold = 0.9, method = 'gt'):
    """
    Find the % of the sampled points that are within the top sampled points possible for data

    Parameters:
    -----------
    testable_points: all valid points in design space
    y_true: True labels for points in design space
    sampled_points: points sampled by sampling scheme
    threshold: threshold value of y_true for a point to be considered a top candidate
    method: gt or lt - greater than or less than threshold

    Returns:
    --------
    int: top percent value

    """
    
    assert testable_points.shape[1] == sampled_points.shape[1], 'Possible and sampled points should have the same dimensions'
    assert testable_points.shape[0] == y_true.shape[0], 'testable points and y_true should be same length'
    
    # get the number of top candidates
    sorted_y_true = np.sort(y_true)
    if method == 'gt':
        n_candidates = len(sorted_y_true[sorted_y_true > threshold])
    elif method == 'lt':
        n_candidates = len(sorted_y_true[sorted_y_true < threshold])
    else:
        raise AssertionError('method must be gt or lt')
        
    assert n_candidates > 0, 'No candidate points found, use a looser threshold'
    
    top_indices = np.argsort(y_true)[-n_candidates:]
    top_points = testable_points[top_indices]

    count = 0
    indices = []
    for i, row in enumerate(sampled_points):
        loc = np.where((row == top_points).all(axis = 1))[0]
        if len(loc) == 1:
            count +=1
            indices.append(i)
        if len(loc) > 1:
            raise AssertionError('Something went wrong in point picking')
            
    return count/n_candidates


def top_percent_campaign(testable_points, y_true, sampled_points, threshold = 0.9, method = 'gt'):
    """
    calculates the top percentage value for every iteration in a campaign
    """
    top_percents = []
    for i in range(len(sampled_points)):
        iteration_points = sampled_points[:i,:]
        top_percents.append(calculate_top_percent(testable_points, y_true, iteration_points, threshold = threshold, method = method))
    
    return top_percents


def enhancement_factor(testable_points, y_true, bo_points, random_points, toppercent_threshold = 0.9, toppercent_method = 'gt'):
    """
    Calculate the enhancement factor, defined as top%_{BO}/top%_{random}
    """
    
    assert len(bo_points) == len(random_points), 'BO and random should have same number of points'
    
    bo_top_percent = top_percent_campaign(testable_points, y_true, bo_points, threshold = toppercent_threshold, method=toppercent_method)
    random_top_percent = top_percent_campaign(testable_points, y_true, random_points, threshold = toppercent_threshold, method=toppercent_method)
    
    ef = np.array(bo_top_percent)/np.array(random_top_percent)
    zerovals = [np.inf, np.nan]
    
    for val in zerovals:
        ef[ef==val] = 0
    ef = np.nan_to_num(ef, nan=0)
        
    return ef 

def acceleration_factor(testable_points, y_true, bo_points, rand_points, acc_thresh_bounds = (0,1), toppercent_threshold = 0.9, toppercent_method = 'gt'):

    # for a range of a threshold values (ie 0-1]:
    
    assert len(bo_points) == len(rand_points), 'bo points and rand points should have same number of points'
    thresholds = np.linspace(acc_thresh_bounds[0], acc_thresh_bounds[1], 51)
    n_points = len(bo_points)

    bo_top_percents = top_percent_campaign(testable_points, y_true, bo_points, threshold = toppercent_threshold, method=toppercent_method)
    rand_top_percents = top_percent_campaign(testable_points, y_true, rand_points, threshold=toppercent_threshold, method=toppercent_method)

    bo_iterations = []
    rand_iterations = []

    for threshold in thresholds:
        #rint(threshold)
        # find the iteration at which met for bo
        found = False
        for i, tp in enumerate(bo_top_percents):
            if tp > threshold:
                bo_iterations.append(i)
                found = True
                break
        if not found:
            bo_iterations.append(n_points)

        # find a the iteration at which met for random
        found = False
        for i, tp in enumerate(rand_top_percents):
            if tp > threshold:
                rand_iterations.append(i)
                found = True
                break
        if not found:
            rand_iterations.append(n_points)

        # divide

    acc_fact = np.array(bo_iterations)/np.array(rand_iterations)
        # append
        
    return (thresholds, acc_fact)