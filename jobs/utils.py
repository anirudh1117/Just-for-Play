
# ---------------------------------------------------------
# Helper: log messages inside a job
# ---------------------------------------------------------

from jobs.models import JobLog


def append_job_log(job_id, message):
    """
    Append a log entry for the given job and also print to console.
    """

    if not job_id:
        # allow dry-run / CLI execution without job
        print(f"[JOB None] {message}")
        return
    
    try:
        JobLog.objects.create(
            job_id=job_id,
            message=message,
        )
    except Exception as e:
        print("Failed to write JobLog:", e)

    print(f"[JOB {job_id}] {message}")

import math

def clean_json(obj):
    """
    Recursively clean NaN / Inf for JSON compatibility.
    PostgreSQL JSON cannot store NaN.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return obj

    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [clean_json(x) for x in obj]

    return obj
