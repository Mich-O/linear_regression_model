"""Serve the fitted Nara recovery-duration model."""

import csv
from hashlib import sha256
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Self

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from joblib import load
from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_io import predict_one
from retrain import MAX_UPLOAD_BYTES, ModelStore, UpdateConflict, read_labelled_rows

MODEL_PATH = Path(__file__).with_name("best_model.pkl")
TRAINING_PATH = MODEL_PATH.with_name("training_rows.csv.gz")


class Admission(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    # Bounds cover the measurements represented in the modeling cohort.
    adm_age: int = Field(ge=6, le=59, description="Age in months", examples=[18])
    adm_kg: float = Field(ge=3, le=20, description="Weight in kg", examples=[7.2])
    adm_cm: float = Field(ge=50, le=115, description="Height or length in cm", examples=[73])
    adm_muac: int = Field(ge=74, le=124, description="MUAC in mm", examples=[115])
    adm_whz06: float | None = Field(
        ge=-5, le=5, description="Weight-for-height z-score. Send null if unavailable.",
        examples=[-2.8, None],
    )
    adm_waz06: float | None = Field(
        ge=-6, le=5, description="Weight-for-age z-score, or null if unavailable.",
    )
    adm_haz06: float | None = Field(
        ge=-6, le=6, description="Height-for-age z-score, or null if unavailable.",
    )
    adm_sex: Literal["Female", "Male"]
    adm_oedema_YN: int = Field(ge=0, le=1, description="Oedema at admission, 0 or 1")
    adm_referral: Literal["CHW - Relais", "Family MUAC", "Other", "Walk-in"]
    adm_category: int = Field(
        ge=1, le=2, description="1 for MUAC below 115 mm or oedema, otherwise 2.",
    )

    @model_validator(mode="after")
    def check_admission_category(self) -> Self:
        expected = 1 if self.adm_muac < 115 or self.adm_oedema_YN == 1 else 2
        if self.adm_category != expected:
            raise ValueError(f"Admission category must be {expected} for the supplied MUAC and oedema.")
        return self


class Prediction(BaseModel):
    predicted_days: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = ModelStore(load(MODEL_PATH), pd.read_csv(TRAINING_PATH))
    yield


app = FastAPI(
    title="Nara Nutrition Follow-up",
    description="Estimates elapsed days to recovered discharge, conditional on recovery.",
    lifespan=lifespan,
)


# Permit browser requests from the local demo and the deployed service origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:7357",
        "http://127.0.0.1:7357",
        "https://nara-follow-up-api.onrender.com",
    ],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


@app.post("/predict", response_model=Prediction)
def predict(admission: Admission, request: Request) -> Prediction:
    return Prediction(predicted_days=predict_one(request.app.state.store.model, admission.model_dump()))


@app.post("/retrain")
def retrain(file: UploadFile, request: Request) -> dict[str, int]:
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV must be 2 MiB or smaller.")
    try:
        rows = read_labelled_rows(content, Admission)
    except (ValueError, csv.Error) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        total = request.app.state.store.update(rows, sha256(content).digest())
    except UpdateConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"uploaded_rows": len(rows), "training_rows": total}
