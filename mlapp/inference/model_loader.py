import os
import pickle


MODEL_DIR = "mlapp/models_store"


def load_latest_model():
    files = [f for f in os.listdir(MODEL_DIR) if f.endswith(".pkl")]
    if not files:
        raise Exception("No trained models found")

    files.sort()
    latest = files[-1]
    path = os.path.join(MODEL_DIR, latest)

    with open(path, "rb") as f:
        model = pickle.load(f)

    return model, latest
