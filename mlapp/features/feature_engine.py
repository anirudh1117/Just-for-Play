import pandas as pd
from jobs.utils import append_job_log

from mlapp.features.loaders import load_candles_df
from mlapp.features.indicators import add_price_features, add_volume_features, add_volatility_features, add_vwap, add_momentum_features
from mlapp.features.time_features import add_time_features
from mlapp.features.targets import (
    add_forward_returns,
    add_binary_targets,
    add_vol_adj_targets,
    clean_targets
)
from mlapp.training.label_generator import generate_trade_labels



class FeatureEngine:
    """
    Orchestrates the entire feature computation pipeline.
    """

    def __init__(self, job_id=None, days=90):
        self.job_id = job_id
        self.days = days
        self.df = None

    def log(self, msg):
        append_job_log(self.job_id, msg)

    # ---------------------------------------------------------
    # Pipeline steps
    # ---------------------------------------------------------

    def load_raw_data(self):
        self.log(f"Loading candles for last {self.days} days...")
        self.df = load_candles_df(self.days)
        self.log(f"Loaded {len(self.df):,} candles.")

    def compute_base_indicators(self):
        self.log("Computing price features...")
        self.df = add_price_features(self.df)

        self.log("Computing volatility features...")
        self.df = add_volatility_features(self.df)

        self.log("Computing volume features...")
        self.df = add_volume_features(self.df)

        self.log("Computing VWAP...")
        self.df = add_vwap(self.df)

        self.log("Computing momentum features (RSI, EMA, MACD, StochRSI)...")
        self.df = add_momentum_features(self.df)




    def compute_time_features(self):
        self.log("Adding time features...")
        self.df = add_time_features(self.df)

    # ---------------------------------------------------------
    # Run full pipeline
    # ---------------------------------------------------------

    def run(self):
        self.load_raw_data()
        self.compute_base_indicators()
        self.compute_time_features()
    
        self.log("Computing forward returns...")
        self.df = add_forward_returns(self.df)
    
        self.log("Computing binary targets...")
        self.df = add_binary_targets(self.df)
    
        self.log("Computing volatility-adjusted targets...")
        self.df = add_vol_adj_targets(self.df)
    
        self.log("Cleaning noisy rows...")
        self.df = clean_targets(self.df)
    
        self.log(f"Final dataset ready: {self.df.shape}")
        return self.df
    
    def run_on_df1(self, df: pd.DataFrame):
        """
        Run full feature + target pipeline on a provided candle DataFrame.

        This is used by batch per-instrument computation.
        """
        self.df = df

        self.compute_base_indicators()
        self.compute_time_features()

        self.log("Computing forward returns...")
        self.df = add_forward_returns(self.df)

        self.log("Computing binary targets...")
        self.df = add_binary_targets(self.df)

        self.log("Computing volatility-adjusted targets...")
        self.df = add_vol_adj_targets(self.df)

        self.log("Cleaning noisy rows...")
        self.df = clean_targets(self.df)

        df = df.sort_values(["symbol", "ts"]).reset_index(drop=True)

        self.log("Label generationws...")
        self.df = generate_trade_labels(self.df)

        self.log(f"Final dataset ready: {self.df.shape}")
        return self.df
    
    def run_on_df(self, df):
        raw_df = df.sort_values(["symbol", "ts"]).reset_index(drop=True)
    
        # 1. FEATURES (past only)
        self.df = raw_df.copy()
        self.compute_base_indicators()
        self.compute_time_features()
        features_df = self.df.copy()
    
        # 2. LABELS (future only)
        labels_df = generate_trade_labels(raw_df)
    
        # 3. MERGE
        self.df = features_df.merge(
            labels_df[["symbol", "ts", "target_up_5m"]],
            on=["symbol", "ts"],
            how="inner"
        )
    
        return self.df


    
    
