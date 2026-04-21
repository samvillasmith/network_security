class NetworkModel:
    def __init__(self, preprocessor, model):
        self.preprocessor = preprocessor
        self.model = model

    def predict(self, X):
        x_transform = self.preprocessor.transform(X)
        return self.model.predict(x_transform)
