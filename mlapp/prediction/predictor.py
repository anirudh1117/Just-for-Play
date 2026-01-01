import os
import pickle
import pandas as pd
from jobs.utils import append_job_log

FEATURE_PATH = "mlapp/cache/features/latest_features.parquet"
MODEL_DIR = "mlapp/models_store"


class EveningPredictor:
    """
    Loads latest model + features, runs probability predictions for all symbols.
    """

    def __init__(self, job_id=None):
        self.job_id = job_id
        self.df = None            # full features DF
        self.latest_df = None     # one-row-per-symbol latest candle
        self.model = None
        self.feature_cols = None

    def log(self, msg):
        append_job_log(self.job_id, msg)

    # ---------------------------------------------------------
    # Load model
    # ---------------------------------------------------------
    def load_latest_model(self):
        self.log("Loading latest model...")

        if not os.path.exists(MODEL_DIR):
            raise Exception("MODEL_DIR does not exist. Train model first.")

        files = [f for f in os.listdir(MODEL_DIR) if f.endswith(".pkl")]
        if not files:
            raise Exception("No trained model found. Run 'Train Model' first.")

        files.sort()  # newest last
        latest = files[-1]
        model_path = os.path.join(MODEL_DIR, latest)

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)
        self.model_path = model_path

        self.log(f"Loaded model: {model_path}")

    # ---------------------------------------------------------
    # Load latest feature DataFrame
    # ---------------------------------------------------------
    def load_features(self):
        self.log("Loading latest features...")
        if not os.path.exists(FEATURE_PATH):
            raise Exception("No features found. Run 'Compute Features' first.")

        self.df = pd.read_parquet(FEATURE_PATH)
        self.log(f"Features loaded: {self.df.shape}")

    # ---------------------------------------------------------
    # Extract latest row per symbol (intraday EOD snapshot)
    # ---------------------------------------------------------
    def extract_latest_rows(self):
        self.log("Extracting latest candle per symbol...")
        self.df = self.df.sort_values(["symbol", "ts"])
        self.latest_df = self.df.groupby("symbol").tail(1).copy()
        self.log(f"Latest rows: {self.latest_df.shape}")

    # ---------------------------------------------------------
    # Prepare feature matrix (only ML features)
    # ---------------------------------------------------------
    def prepare_feature_matrix(self):
        self.log("Preparing feature matrix...")

        exclude = ["ts", "symbol", "date", "target_up_5m", "target_up_10m",
                   "fwd_ret_1m", "fwd_ret_5m", "fwd_ret_10m",
                   "fwd_close_1m", "fwd_close_5m", "fwd_close_10m"]

        self.feature_cols = [c for c in self.latest_df.columns if c not in exclude]

        self.log(f"Using {len(self.feature_cols)} ML features.")

    # ---------------------------------------------------------
    # Predict probabilities
    # ---------------------------------------------------------
    def predict(self):
        self.log("Running predictions for all symbols...")

        X = self.latest_df[self.feature_cols]
        preds = self.model.predict(X)

        self.latest_df["prob_up"] = preds
        self.log("Predictions computed.")

        return self.latest_df
