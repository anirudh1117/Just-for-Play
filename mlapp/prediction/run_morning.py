import asyncio
from jobs.utils import append_job_log
from mlapp.live.morning_collector import MorningCollector
from mlapp.live.live_feature_engine import LiveFeatureEngine
from mlapp.prediction.morning_predictor import MorningPredictor
from mlapp.prediction.save_final_picks import save_final_picks


def run(job_id=None, minutes=15, access_token=None):
    """
    Full morning prediction pipeline.
    """

    append_job_log(job_id, "Starting morning live prediction...")

    # 1) Collect live data
    collector = MorningCollector(access_token=access_token, job_id=job_id)
    candles = asyncio.run(collector.collect(minutes=minutes))

    # 2) Convert candles → features
    engine = LiveFeatureEngine(candles)
    feature_df = engine.run()

    append_job_log(job_id, f"Generated live features: {feature_df.shape}")

    # 3) Predict using ML model
    predictor = MorningPredictor(job_id=job_id)
    predictor.load_latest_model()

    top3 = predictor.predict(feature_df)

    append_job_log(job_id, f"Final top 3 picks selected: {top3.shape}")

    # 4) Save to DB
    save_final_picks(top3, predictor.model_path, job_id)

    return "Morning prediction completed."
