"""
Coverage model service.

Loads network_coverage_model.pkl and provides prediction helper.
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from .config import settings

logger = logging.getLogger(__name__)

FEATURE_COLS: List[str] = [
    "RSRP",
    "RSRQ",
    "RLC_DL",
    "PCI",
    "Band_enc",
    "hour",
    "minute",
    "second",
    "RSRP_lag1",
    "RSRP_lag2",
    "RSRP_roll3",
    "RSRP_roll5",
    "RSRQ_lag1",
    "RSRQ_lag2",
    "RSRQ_roll3",
    "RSRQ_roll5",
    "RLC_DL_lag1",
    "RLC_DL_lag2",
    "RLC_DL_roll3",
    "RLC_DL_roll5",
]


class _CoverageUnpickler(pickle.Unpickler):
    """Unpickler that maps numpy 2.0 module paths to numpy 1.x equivalents."""

    def find_class(self, module: str, name: str):
        if module.startswith("numpy._core"):
            module = module.replace("numpy._core", "numpy.core", 1)
        return super().find_class(module, name)


class CoverageService:
    """Service for loading and using the network coverage model."""

    def __init__(self) -> None:
        self.model: Any = None
        self.scaler: Any = None
        self.label_encoder: Any = None
        self.feature_cols: List[str] = list(FEATURE_COLS)
        self.is_loaded: bool = False
        self.model_path: Path | None = None

    def _resolve_model_path(self) -> Path:
        model_path = settings.network_coverage_model_path
        if model_path.exists():
            return model_path

        fallback_path = settings.output_dir / model_path.name
        if fallback_path.exists():
            logger.warning(
                "Coverage model not found at %s. Falling back to %s.",
                model_path,
                fallback_path
            )
            return fallback_path

        return model_path

    def load_model(self) -> bool:
        """Load coverage model artifacts from disk."""
        try:
            model_path = self._resolve_model_path()
            if not model_path.exists():
                logger.error("Coverage model not found: %s", model_path)
                return False

            with open(model_path, "rb") as handle:
                artifacts = _CoverageUnpickler(handle).load()

            missing_keys = [
                key
                for key in ("model", "scaler", "label_encoder", "feature_cols")
                if key not in artifacts
            ]
            if missing_keys:
                logger.error("Coverage model artifact missing keys: %s", ", ".join(missing_keys))
                return False

            artifact_cols = list(artifacts.get("feature_cols") or [])
            if artifact_cols and artifact_cols != FEATURE_COLS:
                logger.warning(
                    "Coverage model feature list mismatch. Expected %s but got %s.",
                    FEATURE_COLS,
                    artifact_cols
                )

            self.model = artifacts["model"]
            self.scaler = artifacts["scaler"]
            self.label_encoder = artifacts["label_encoder"]
            self.feature_cols = list(FEATURE_COLS)
            self.model_path = model_path
            self.is_loaded = True

            logger.info("Loaded coverage model from %s", model_path)
            logger.info("Coverage feature order: %s", self.feature_cols)
            return True

        except Exception as exc:
            logger.error("Error loading coverage model: %s", exc)
            return False

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Run coverage prediction using the loaded model."""
        if not self.is_loaded:
            raise RuntimeError("Coverage model not loaded. Call load_model() first.")

        missing = [name for name in self.feature_cols if name not in features]
        if missing:
            raise ValueError(f"Missing features: {', '.join(missing)}")

        ordered = [float(features[name]) for name in self.feature_cols]
        logger.info("Coverage predict input: %s", features)
        logger.info("Coverage feature vector: %s", ordered)

        feature_array = np.array([ordered], dtype=float)
        features_scaled = self.scaler.transform(feature_array)
        pred_code = self.model.predict(features_scaled)[0]
        pred_proba = self.model.predict_proba(features_scaled)[0]

        predicted_label = self.label_encoder.inverse_transform([pred_code])[0]
        probabilities = {
            label: float(prob)
            for label, prob in zip(self.label_encoder.classes_, pred_proba)
        }
        confidence = round(float(np.max(pred_proba)) * 100, 2)

        logger.info(
            "Coverage prediction: class=%s confidence=%.2f probabilities=%s",
            predicted_label,
            confidence,
            probabilities
        )

        return {
            "predicted_class": predicted_label,
            "confidence": confidence,
            "probabilities": probabilities,
        }

    def _get_feature_stats(self) -> Dict[str, Dict[str, float]]:
        if self.scaler is None:
            return {}

        mean = getattr(self.scaler, "mean_", None)
        scale = getattr(self.scaler, "scale_", None)
        if mean is None or scale is None:
            return {}

        if len(mean) != len(self.feature_cols) or len(scale) != len(self.feature_cols):
            return {}

        return {
            name: {"mean": float(mu), "std": float(std)}
            for name, mu, std in zip(self.feature_cols, mean, scale)
        }

    def get_status(self) -> Dict[str, Any]:
        """Return current coverage model status and metadata."""
        if not self.is_loaded:
            loaded = self.load_model()
            if not loaded:
                model_path = self._resolve_model_path()
                return {
                    "loaded": False,
                    "model_path": str(model_path),
                    "feature_cols": [],
                    "error": "Coverage model not loaded",
                }

        model_path = self.model_path or self._resolve_model_path()
        classes = list(self.label_encoder.classes_) if self.label_encoder is not None else []

        return {
            "loaded": True,
            "model_path": str(model_path),
            "model_type": type(self.model).__name__ if self.model else None,
            "feature_count": len(self.feature_cols),
            "feature_cols": list(self.feature_cols),
            "feature_stats": self._get_feature_stats(),
            "classes": classes,
        }


coverage_service = CoverageService()
