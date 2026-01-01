import os
import pandas as pd
from mlapp.features.feature_engine import FeatureEngine


FEATURE_PATH = "mlapp/cache/features/latest_features.parquet"


def run(job_id=None, days=90):
    engine = FeatureEngine(job_id=job_id, days=days)
    df = engine.run()

    # Save for training
    os.makedirs("mlapp/cache/features", exist_ok=True)
    df.to_parquet(FEATURE_PATH, index=False)

    return f"Features saved: {df.shape}"
