# mlapp/testing/dummy_model.py

class DummyModel:
    """
    Used for testing backtester/simulator when no ML model is trained yet.
    Always returns a fixed confidence score.
    """

    def __init__(self, score=0.8):
        self.score = score

    def predict(self, df):
        # return a single prediction for whole day
        return [self.score]
