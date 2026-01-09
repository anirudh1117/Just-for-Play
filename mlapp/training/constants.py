TARGET_COL = "target_up_5m"

META_COLS = [
    "symbol",
    "ts",
    "label",
    "label_raw",
    "feature_version",
]

def get_feature_columns(df):
    return [c for c in df.columns if c not in META_COLS]
