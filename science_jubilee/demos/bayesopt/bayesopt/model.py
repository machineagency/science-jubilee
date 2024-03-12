import sklearn.gaussian_process as gp
from sklearn.preprocessing import MinMaxScaler
from sklearn.pipeline import Pipeline
import sklearn

class Model():
    def __init__():
        """
        Super class for bayesian optimization models
        """

    def update(new_data):
        """
        update model with new data
        """
        return None
    
    def evaluate(points):
        """
        get predicted value and uncertainty at points
        """
        return None
    

class GaussianProcessModel(Model):
    def __init__(self, kernel, alpha = 1e-10, scale = True):
        """
        Use a gaussian process regressor as the BO model

        Parameters:
        -----------
        estimator - sklearn estimator, or one that adheres to sklearn model
        skelarnestimator - flag to turn off type checking if you know your model is not from sklearn but will work
        """
        pipeline_steps = []
        if scale:
            pipeline_steps.append(('scaler', MinMaxScaler()))
        else:
            pass
        estimator = gp.GaussianProcessRegressor(kernel = kernel, alpha = alpha, n_restarts_optimizer = 10)
        pipeline_steps.append(('estimator', estimator))

        self.pipeline = Pipeline(pipeline_steps)

    def update(self, data):
        """
        'updates' model by re-training on new data
        """
        assert type(data) == tuple, 'Pass data as a tuple of (X, y)'
        X, y = data
        pipeline = sklearn.base.clone(self.pipeline)
        pipeline.fit(X,y)
        self.pipeline = pipeline

        return None
    
    def evaluate(self, points):
        """
        Evaluate model prediction and get uncertainty estimates at points. 
        """
        prediction, std = self.pipeline.predict(points, return_std = True)
        return prediction, std
