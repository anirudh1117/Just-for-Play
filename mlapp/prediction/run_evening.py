from jobs.utils import append_job_log
from mlapp.prediction.predictor import EveningPredictor
from mlapp.prediction.generate_signals import final_signal_processing
from mlapp.prediction.save_predictions import save_evening_shortlist



def run(job_id=None):
    """
    Evening prediction pipeline entrypoint.
    Loads model, features, and generates probability predictions.
    """
    predictor = EveningPredictor(job_id=job_id)

    append_job_log(job_id, "Starting evening prediction...")

    predictor.load_latest_model()
    predictor.load_features()
    predictor.extract_latest_rows()
    predictor.prepare_feature_matrix()

    result_df = predictor.predict()

    # Generate final signals
    signals = final_signal_processing(result_df)

    append_job_log(job_id, f"Signals generated: {signals.shape}")
    # Save into DB
    count = save_evening_shortlist(signals, predictor.model_path, job_id)

    return f"Evening predictions ready: {signals.shape[0]} stocks."
