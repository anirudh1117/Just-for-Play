import os
import time
import pickle
import pandas as pd
import lightgbm as lgb
import numpy as np

from sklearn.metrics import roc_auc_score

from jobs.utils import append_job_log
from mlapp.training.dataset_prep import clean_dataset
from mlapp.training.cv_generator import generate_time_cv_splits
from mlapp.training.params import LGB_PARAMS
from mlapp.training.constants import TARGET_COL, get_feature_columns
from mlapp.training.evaluation import evaluate_trading_performance

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

FEATURE_PATH = "mlapp/cache/features/latest_features.parquet"
MODEL_DIR = "mlapp/models_store"


# ---------------------------------------------------------
# LOAD LATEST FEATURE DATAFRAME
# ---------------------------------------------------------

def _get_latest_feature_df(job_id):
    append_job_log(job_id, f"Loading features from: {FEATURE_PATH}")

    if not os.path.exists(FEATURE_PATH):
        raise Exception(
            "Feature file not found. Run 'Compute Features' job first."
        )

    df = pd.read_parquet(FEATURE_PATH)
    append_job_log(job_id, f"Loaded DataFrame shape: {df.shape}")
    return df


# ---------------------------------------------------------
# SAVE TRAINED MODEL WITH VERSIONING
# ---------------------------------------------------------

def _save_model(model, job_id):
    os.makedirs(MODEL_DIR, exist_ok=True)
    ts = int(time.time())
    model_path = f"{MODEL_DIR}/model_5m_{ts}.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    append_job_log(job_id, f"Model saved at: {model_path}")
    return model_path


# ---------------------------------------------------------
# MAIN TRAINING ENTRYPOINT
# ---------------------------------------------------------

def run(job_id=None):
    append_job_log(job_id, "Starting LightGBM training pipeline")
    last_valid_df = None
    last_valid_X = None
    last_valid_y = None


    # ---------------------------------------------------------
    # 1) Load features
    # ---------------------------------------------------------
    df = _get_latest_feature_df(job_id)

    # ---------------------------------------------------------
    # 2) Clean dataset
    # ---------------------------------------------------------
    df = clean_dataset(df)
    append_job_log(job_id, f"Cleaned dataset shape: {df.shape}")

    # ---------------------------------------------------------
    # 3) Feature / target separation (STRICT)
    # ---------------------------------------------------------
    FEATURE_COLS = get_feature_columns(df)
    append_job_log(job_id, f"Using {len(FEATURE_COLS)} feature columns")

    # ---------------------------------------------------------
    # 4) Rolling Cross-Validation (Time-aware)
    # ---------------------------------------------------------
    append_job_log(job_id, "Running rolling time-based CV")

    cv_aucs = []
    fold = 1

    for train_df, valid_df in generate_time_cv_splits(df):
        X_train = train_df[FEATURE_COLS]
        y_train = train_df[TARGET_COL]

        X_valid = valid_df[FEATURE_COLS]
        y_valid = valid_df[TARGET_COL]

        # ---- class imbalance handling ----
        pos = y_train.sum()
        neg = len(y_train) - pos
        scale_pos_weight = neg / max(pos, 1)

        params = LGB_PARAMS.copy()
        params["scale_pos_weight"] = scale_pos_weight

        lgb_train = lgb.Dataset(X_train, y_train)
        lgb_valid = lgb.Dataset(X_valid, y_valid, reference=lgb_train)

        model = lgb.train(
            params,
            lgb_train,
            valid_sets=[lgb_valid],
            valid_names=["valid"],
            num_boost_round=2000,
            early_stopping_rounds=100,
            verbose_eval=False,
        )

        preds = model.predict(X_valid)
        auc = roc_auc_score(y_valid, preds)
        cv_aucs.append(auc)

        last_valid_df = valid_df
        last_valid_X = X_valid
        last_valid_y = y_valid


        append_job_log(
            job_id,
            f"CV Fold {fold} | AUC = {auc:.4f} | "
            f"Pos={int(pos)} Neg={int(neg)}"
        )
        fold += 1

    avg_auc = float(np.mean(cv_aucs))
    append_job_log(job_id, f"Average CV AUC: {avg_auc:.4f}")

    # ---------------------------------------------------------
    # 5) Train FINAL model on full dataset
    # ---------------------------------------------------------
    append_job_log(job_id, "Training final model on full dataset")

    X_full = df[FEATURE_COLS]
    y_full = df[TARGET_COL]

    pos = y_full.sum()
    neg = len(y_full) - pos
    scale_pos_weight = neg / max(pos, 1)

    final_params = LGB_PARAMS.copy()
    final_params["scale_pos_weight"] = scale_pos_weight

    lgb_full = lgb.Dataset(X_full, y_full)

    final_model = lgb.train(
        final_params,
        lgb_full,
        num_boost_round=500,
        verbose_eval=False,
    )

    append_job_log(job_id, "Final model training completed")

    # Predict on validation set
    probs = final_model.predict(last_valid_X)
    
    # Evaluate trading performance
    eval_df = evaluate_trading_performance(
        last_valid_df,
        probs,
        thresholds=[0.6, 0.65, 0.7, 0.75],
        reward_pct=0.015,
        risk_pct=0.005,
    )
    
    append_job_log(job_id, f"Evaluation summary:\n{eval_df}")


    # ---------------------------------------------------------
    # 6) Save model
    # ---------------------------------------------------------
    model_path = _save_model(final_model, job_id)

    append_job_log(job_id, "Training pipeline finished successfully")
    return f"Training completed. Model saved at {model_path}"
