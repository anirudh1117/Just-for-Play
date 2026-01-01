import os
import pickle
import pandas as pd
from jobs.utils import append_job_log


class MorningPredictor:

    def __init__(self, job_id=None):
        self.job_id = job_id
        self.model = None
        self.feature_cols = None
        self.model_path = None

    def log(self, msg):
        append_job_log(self.job_id, msg)

    # ------------------------------------------------------
    # Load latest model (same as evening)
    # ------------------------------------------------------
    def load_latest_model(self, model_dir="mlapp/models_store"):
        files = [f for f in os.listdir(model_dir) if f.endswith(".pkl")]
        if not files:
            raise Exception("No trained model found.")

        files.sort()
        latest = files[-1]
        self.model_path = os.path.join(model_dir, latest)

        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)

        self.log(f"Loaded model: {self.model_path}")

    # ------------------------------------------------------
    # Filter + Pick Top 3 Stocks
    # ------------------------------------------------------
    def select_top3(self, df):
        """
        Apply filters and select the final top 3 picks.
        """
        # Basic quality filters
        df = df[df["volume"] > 0]
        df = df[df["atr_14"] > 0]
        df = df[df["close"] > 20]

        # Rank by probability from live features
        df = df.sort_values("prob_up_live", ascending=False)

        return df.head(3).copy()

    # ------------------------------------------------------
    # Compute entry/target/stoploss
    # ------------------------------------------------------
    def compute_levels(self, df):
        df["entry"] = df["vwap"]
        df["stoploss"] = df["entry"] - df["atr_14"] * 1.2
        df["target"] = df["entry"] + df["atr_14"] * 2

        df["confidence"] = (df["prob_up_live"] * 100).round(2)

        return df

    # ------------------------------------------------------
    # Main prediction
    # ------------------------------------------------------
    def predict(self, feature_df):
        """
        feature_df = live feature DataFrame from LiveFeatureEngine
        """

        # Prepare feature columns
        drop_cols = ["symbol", "ts"]
        self.feature_cols = [c for c in feature_df.columns if c not in drop_cols]

        X = feature_df[self.feature_cols]

        # ML inference
        preds = self.model.predict(X)
        feature_df["prob_up_live"] = preds

        # Select top 3
        top3 = self.select_top3(feature_df)

        # Compute final entry/SL/Target
        top3 = self.compute_levels(top3)

        self.log(f"Selected top 3 picks: {list(top3['symbol'])}")

        return top3
