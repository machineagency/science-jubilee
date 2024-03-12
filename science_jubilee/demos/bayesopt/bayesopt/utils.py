import numpy as np

class Oracle():
    """
    Provides a noisy 'ground truth' oracle from a SKlearn estimator
    """
    def __init__(self, estimator, noise_std):
        """
        Build a noisy oracle as ground truth
        """
        
        self.estimator = estimator
        self.std = noise_std
        
    def predict(self, X):
        y_pred = self.estimator.predict(X)
        noise = np.random.normal(loc = 0, scale = self.std, size = y_pred.shape)
        return y_pred + noise
    



def lighten_color(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])