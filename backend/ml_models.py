"""
ML models for freight prediction trained on REAL Indian Railway OD data (FY 2025-26).
Feature engineering + RandomForest/GradientBoosting via scikit-learn.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression

from real_data import ml_training_frame

_rng = np.random.default_rng(42)


class FreightModels:
    FEATS = ["distance_km", "wagons", "loaded_pct", "priority", "congestion", "weather", "is_dfc"]

    def __init__(self):
        df = ml_training_frame()
        X = df[self.FEATS]

        self.eta = RandomForestRegressor(n_estimators=80, max_depth=12, random_state=1, n_jobs=1)
        self.eta.fit(X, df["eta_hrs"])

        self.circuit = GradientBoostingRegressor(n_estimators=120, max_depth=4, random_state=2)
        self.circuit.fit(X, df["circuit_hrs"])

        self.util = LinearRegression()
        self.util.fit(X, df["util_pct"])

        self.cong = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=3)
        self.cong.fit(X, df["cong_next"])

        self.eta_importance = dict(zip(self.FEATS, self.eta.feature_importances_.tolist()))
        self.circuit_importance = dict(zip(self.FEATS, self.circuit.feature_importances_.tolist()))
        self.eta_score = round(float(self.eta.score(X, df["eta_hrs"])), 3)
        self.circuit_score = round(float(self.circuit.score(X, df["circuit_hrs"])), 3)
        self.trained_rows = int(len(df))

    def _row(self, payload: dict) -> pd.DataFrame:
        return pd.DataFrame([{
            "distance_km": float(payload.get("distance_km", 500)),
            "wagons": int(payload.get("wagons", 58)),
            "loaded_pct": float(payload.get("loaded_pct", 85)),
            "priority": int(payload.get("priority", 2)),
            "congestion": float(payload.get("congestion", 0.4)),
            "weather": float(payload.get("weather", 0.2)),
            "is_dfc": int(payload.get("is_dfc", 0)),
        }])

    def _contribs(self, importance: dict, x: pd.DataFrame) -> list[dict]:
        contribs = [{"feature": f, "importance": round(importance[f], 3), "value": float(x[f].iloc[0])}
                    for f in self.FEATS]
        contribs.sort(key=lambda c: c["importance"], reverse=True)
        return contribs[:5]

    def predict_eta(self, payload):
        x = self._row(payload)
        pred = float(self.eta.predict(x)[0])
        return {"eta_hours": round(pred, 2), "contributions": self._contribs(self.eta_importance, x),
                "model": "RandomForestRegressor", "r2": self.eta_score}

    def predict_circuit(self, payload):
        x = self._row(payload)
        pred = float(self.circuit.predict(x)[0])
        return {"circuit_hours": round(pred, 2), "contributions": self._contribs(self.circuit_importance, x),
                "model": "GradientBoostingRegressor", "r2": self.circuit_score}

    def predict_utilization(self, payload):
        x = self._row(payload)
        pred = float(self.util.predict(x)[0])
        pred = max(30.0, min(100.0, pred))
        band = "optimal" if pred >= 85 else ("moderate" if pred >= 70 else "underutilized")
        return {"utilization_pct": round(pred, 2), "band": band, "model": "LinearRegression"}

    def predict_congestion(self, payload):
        x = self._row(payload)
        pred = float(self.cong.predict(x)[0])
        pred = max(0.0, min(1.0, pred))
        level = "critical" if pred >= 0.75 else ("high" if pred >= 0.55 else ("moderate" if pred >= 0.35 else "low"))
        return {"congestion_forecast": round(pred, 3), "level": level, "model": "GradientBoostingRegressor"}

    def predict_demand(self, payload):
        base = float(payload.get("current_tonnes", 12000))
        growth = float(payload.get("growth_pct", 4)) / 100.0
        seasonality = float(payload.get("seasonality", 0.05))
        horizon_days = int(payload.get("horizon_days", 30))
        series = []
        for d in range(horizon_days):
            trend = base * (1 + growth) ** (d / 365.0)
            seas = trend * seasonality * np.sin(2 * np.pi * d / 30.0)
            series.append(round(trend + seas + _rng.normal(0, base * 0.02), 1))
        return {
            "horizon_days": horizon_days,
            "forecast": series,
            "total_tonnes": round(float(np.sum(series)), 1),
            "peak_day": int(np.argmax(series)) + 1,
        }
