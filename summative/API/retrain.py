"""Read labelled uploads and refit the active recovery-duration pipeline."""

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from threading import Lock

import pandas as pd
from pydantic import BaseModel
from sklearn.base import clone

TARGET = "recovered_los"
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
INTEGER_FIELDS = ("adm_age", "adm_muac", "adm_oedema_YN", TARGET)
DECIMAL_FIELDS = ("adm_kg", "adm_cm", "adm_whz06")


def read_labelled_rows(content: bytes, schema: type[BaseModel]) -> pd.DataFrame:
    columns = [*schema.model_fields, TARGET]
    reader = csv.DictReader(StringIO(content.decode("utf-8-sig")), strict=True)
    if reader.fieldnames is None or sorted(reader.fieldnames) != sorted(columns):
        raise ValueError("CSV must contain these columns: " + ", ".join(columns))

    rows = []
    for line, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"CSV record {line} has the wrong number of fields.")
        try:
            for field in INTEGER_FIELDS:
                value = Decimal(row[field])
                if not value.is_finite() or value != value.to_integral_value():
                    raise ValueError(f"{field} must be a whole number.")
                row[field] = int(value)
            for field in DECIMAL_FIELDS:
                value = row[field].strip()
                row[field] = None if field == "adm_whz06" and not value else float(value)
            days = row.pop(TARGET)
            if days <= 0:
                raise ValueError("recovered_los must be a positive whole number.")
            admission = schema.model_validate(row)
        except (ValueError, InvalidOperation) as error:
            raise ValueError(f"CSV record {line}: {error}") from error
        rows.append({**admission.model_dump(), TARGET: days})

    if not rows:
        raise ValueError("CSV must contain at least one labelled record.")
    return pd.DataFrame(rows, columns=columns)


class ModelStore:
    def __init__(self, model, rows: pd.DataFrame):
        self.model = model
        self.rows = rows
        self.lock = Lock()

    def update(self, uploaded_rows: pd.DataFrame) -> int:
        # Publish the fitted pipeline only after the update succeeds.
        with self.lock:
            combined = pd.concat([self.rows, uploaded_rows], ignore_index=True)
            inputs = list(self.model.feature_names_in_)
            fitted = clone(self.model).fit(combined[inputs], combined[TARGET])
            self.model = fitted
            self.rows = combined
            return len(combined)
