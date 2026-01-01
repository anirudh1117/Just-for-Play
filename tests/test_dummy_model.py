from mlapp.testing.dummy_model import DummyModel
import pandas as pd


def test_dummy_model_predict():
    df = pd.DataFrame({"close": [100]})
    model = DummyModel(score=0.75)

    pred = model.predict(df)
    assert pred[0] == 0.75
