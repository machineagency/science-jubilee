from scipy.stats import norm
import numpy as np

def _UCB(pred_x, std_x, beta):
    """
    upper confidence bound acquisition function
    """
    return pred_x + beta*std_x

def _expected_improvement(pred_x, std_x, max_val, xi):
    """
    expected improvement acquisition function

    """
    meanterm = pred_x - max_val - xi
    term1 = meanterm*norm.cdf(meanterm/std_x)
    term2 = std_x*norm.pdf(meanterm/std_x)
    return term1+term2

def _probability_of_improvement(pred_x, std_x, max_val, xi):
    """
    return best point to query based on probability of improvement
    """
    inner = (pred_x - max_val - xi)/(std_x)
    return norm.cdf(inner)


def optimize_UCB(bo, n_querypts = 1, beta = 1):
    """
    Callable function to get the best query point using upper confidence bound acquisition function

    Parameters:
    -----------
    model: fitted model for problem
    data: current set of collected data
    points: set of points to consider
    n_querypts: how many points to return
    beta: parameter to control weight of uncertainty. More beta => more explore

    Returns:
    --------
    querypoints: list of points to query at
    """
    X, y = bo.all_data
    pred_X, std_X = bo.model.evaluate(bo.available_points)
    UCB = _UCB(pred_X, std_X, beta)
    query_ind = np.argsort(UCB)
    if bo.method == 'max':
        query_ind = np.flip(query_ind)
    querypts = bo.available_points[query_ind[:n_querypts],:]

    return querypts

def optimize_EI(bo, n_querypts = 1, xi = 1):
    """
    Callable function to get the best query point using expected improvement

    Parameters:
    -----------
    model: fitted model for problem
    data: current set of collected data
    points: set of points to consider
    n_querypts: how many points to return
    xi: tradeoff parameter to control explore/exploit

    Returns:
    --------
    querypoints: list of points to query at
    """
    X, y = bo.all_data
    pred_X, std_X = bo.model.evaluate(bo.available_points)
    max_val = y.max()
    EI = _expected_improvement(pred_X, std_X, max_val, xi)
    query_ind = np.argsort(EI)
    if bo.method == 'max':
        query_ind = np.flip(query_ind)
    querypts = bo.available_points[query_ind[:n_querypts],:]
    return querypts


def optimize_PI(bo, n_querypts = 1, xi = 1):
    """
    Callable function to get the best query point using probability of improvement

    Parameters:
    -----------
    model: fitted model for problem
    data: current set of collected data
    points: set of points to consider
    n_querypts: how many points to return
    xi: tradeoff parameter to control explore/exploit

    Returns:
    --------
    querypoints: list of points to query at
    """
    X, y = bo.all_data
    pred_y, std_y = bo.model.evaluate(bo.available_points)
    max_val = y.max()
    PI = _probability_of_improvement(pred_y, std_y, max_val, xi)
    query_ind = np.argsort(PI)
    if bo.method == 'max':
        query_ind = np.flip(query_ind)
    querypts = bo.available_points[query_ind[:n_querypts],:]
    return querypts