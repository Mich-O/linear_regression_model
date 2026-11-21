"""Predict from one admission using a fitted pipeline."""

from collections.abc import Mapping

import pandas as pd


def predict_one(pipeline, admission: Mapping[str, object]) -> float:
    row = pd.DataFrame([admission], columns=pipeline.feature_names_in_)
    return float(pipeline.predict(row)[0])
