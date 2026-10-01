"""
QoS prediction service.

Loads qos_model.pkl and provides prediction helper.
"""

import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd

from .config import settings

logger = logging.getLogger(__name__)

FEATURE_COLS: List[str] = [
    "physical_cell_identity_pcell",
    "band_pcell",
    "rsrp_pcell",
    "rsrq_pcell",
    "rlc_downlink_throughput",
    "time_seconds",
    "time_delta_s",
    "rsrp_pcell_roll_mean_5",
    "rsrp_pcell_roll_std_5",
    "rsrq_pcell_roll_mean_5",
    "rsrq_pcell_roll_std_5",
    "rlc_downlink_throughput_roll_mean_5",
    "rlc_downlink_throughput_roll_std_5",
]

LABEL_MAP = {
    0: "Acceptable",
    1: "Assez bien",
    2: "Mauvaise",
    3: "Tres bonne",
}


def _ensure_numpy_compat_modules() -> None:
    """Alias numpy._core paths to numpy.core for older numpy versions."""
    import sys

    sys.modules.setdefault("numpy._core", np.core)
    core_umath = getattr(np.core, "_multiarray_umath", None)
    if core_umath is not None:
        sys.modules.setdefault("numpy._core._multiarray_umath", core_umath)
    core_dtype = getattr(np.core, "_dtype", None)
    if core_dtype is not None:
        sys.modules.setdefault("numpy._core._dtype", core_dtype)


def _ensure_sklearn_compat() -> None:
    """Add shims for legacy scikit-learn pickle references."""
    import sys
    import types

    try:
        from sklearn.pipeline import Pipeline as SkPipeline
        legacy_module = types.ModuleType("Pipeline")
        legacy_module.Pipeline = SkPipeline
        sys.modules["Pipeline"] = legacy_module
    except Exception:
        pass

    try:
        from sklearn.compose import _column_transformer
        if not hasattr(_column_transformer, "_RemainderColsList"):
            class _RemainderColsList(list):
                pass

            _column_transformer._RemainderColsList = _RemainderColsList
    except Exception:
        pass


class _NumpyCompatUnpickler(pickle.Unpickler):
    """Unpickler that maps legacy module paths to current equivalents."""

    def find_class(self, module: str, name: str):
        if module.startswith("numpy._core"):
            module = module.replace("numpy._core", "numpy.core", 1)
        if module == "Pipeline":
            import sklearn.pipeline as skl_pipeline
            if hasattr(skl_pipeline, name):
                return getattr(skl_pipeline, name)
            return skl_pipeline.Pipeline
        if module == "sklearn.compose._column_transformer" and name == "_RemainderColsList":
            from sklearn.compose import _column_transformer
            if hasattr(_column_transformer, "_RemainderColsList"):
                return _column_transformer._RemainderColsList
        return super().find_class(module, name)


def build_features(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Build the engineered feature dict expected by the QoS model."""
    rsrp = float(raw["rsrp"])
    rsrq = float(raw["rsrq"])
    throughput = float(raw["rlc_downlink_throughput"])
    band = float(raw["band"])
    pci = float(raw["physical_cell_identity"])

    time_seconds = int(time.time())

    return {
        "physical_cell_identity_pcell": pci,
        "band_pcell": band,
        "rsrp_pcell": rsrp,
        "rsrq_pcell": rsrq,
        "rlc_downlink_throughput": throughput,
        "time_seconds": time_seconds,
        "time_delta_s": 0.0,
        "rsrp_pcell_roll_mean_5": rsrp,
        "rsrp_pcell_roll_std_5": 0.0,
        "rsrq_pcell_roll_mean_5": rsrq,
        "rsrq_pcell_roll_std_5": 0.0,
        "rlc_downlink_throughput_roll_mean_5": throughput,
        "rlc_downlink_throughput_roll_std_5": 0.0,
    }


def _patch_column_transformers(model: Any) -> None:
    """Patch missing attrs on ColumnTransformer instances for older sklearn."""
    try:
        from sklearn.compose import ColumnTransformer
    except Exception:
        return

    def _ensure_ct_attrs(ct: Any) -> None:
        if not hasattr(ct, "_name_to_fitted_passthrough"):
            ct._name_to_fitted_passthrough = {}

    if isinstance(model, ColumnTransformer):
        _ensure_ct_attrs(model)
        return

    steps = getattr(model, "steps", None)
    if steps:
        for _, step in steps:
            _patch_column_transformers(step)
        return

    transformers = getattr(model, "transformers_", None)
    if transformers:
        for _, transformer, _ in transformers:
            _patch_column_transformers(transformer)


class QoSService:
    """Service for loading and using the QoS prediction model."""

    def __init__(self) -> None:
        self.model: Any = None
        self.feature_cols: List[str] = list(FEATURE_COLS)
        self.is_loaded: bool = False
        self.model_path: Path | None = None

    def _resolve_model_path(self) -> Path:
        model_path = settings.qos_model_path
        if model_path.exists():
            return model_path

        fallback_path = settings.output_dir / model_path.name
        if fallback_path.exists():
            logger.warning(
                "QoS model not found at %s. Falling back to %s.",
                model_path,
                fallback_path
            )
            return fallback_path

        return model_path

    def load_model(self) -> bool:
        """Load QoS model artifacts from disk."""
        try:
            model_path = self._resolve_model_path()
            if not model_path.exists():
                logger.error("QoS model not found: %s", model_path)
                return False

            _ensure_numpy_compat_modules()
            _ensure_sklearn_compat()

            artifacts = None
            try:
                artifacts = joblib.load(model_path)
                logger.info("Loaded QoS model with joblib")
            except ModuleNotFoundError as exc:
                if "numpy._core" in str(exc):
                    _ensure_numpy_compat_modules()
                if "Pipeline" in str(exc):
                    _ensure_sklearn_compat()
                try:
                    artifacts = joblib.load(model_path)
                    logger.info("Loaded QoS model with joblib (compat)")
                except Exception as retry_exc:
                    logger.warning("Joblib load failed: %s", retry_exc)
            except AttributeError as exc:
                if "_RemainderColsList" in str(exc):
                    _ensure_sklearn_compat()
                    try:
                        artifacts = joblib.load(model_path)
                        logger.info("Loaded QoS model with joblib (compat)")
                    except Exception as retry_exc:
                        logger.warning("Joblib load failed: %s", retry_exc)
                else:
                    logger.warning("Joblib load failed: %s", exc)
            except Exception as exc:
                logger.warning("Joblib load failed: %s", exc)

            if artifacts is None:
                try:
                    with open(model_path, "rb") as handle:
                        artifacts = _NumpyCompatUnpickler(handle).load()
                except ModuleNotFoundError as exc:
                    if "Pipeline" in str(exc):
                        _ensure_sklearn_compat()
                        with open(model_path, "rb") as handle:
                            artifacts = _NumpyCompatUnpickler(handle).load()
                    else:
                        raise

            if isinstance(artifacts, dict) and "model" in artifacts:
                self.model = artifacts["model"]
                artifact_cols = list(artifacts.get("feature_cols") or [])
                if artifact_cols and artifact_cols != FEATURE_COLS:
                    logger.warning(
                        "QoS feature list mismatch. Expected %s but got %s.",
                        FEATURE_COLS,
                        artifact_cols
                    )
            elif hasattr(artifacts, "predict"):
                self.model = artifacts
            else:
                logger.error("Unsupported QoS model artifact type: %s", type(artifacts))
                return False

            model_feature_names = getattr(self.model, "feature_names_in_", None)
            if model_feature_names is not None and list(model_feature_names) != FEATURE_COLS:
                logger.warning(
                    "QoS model feature list mismatch. Expected %s but got %s.",
                    FEATURE_COLS,
                    list(model_feature_names)
                )
            self.feature_cols = list(FEATURE_COLS)

            _patch_column_transformers(self.model)

            self.model_path = model_path
            self.is_loaded = True

            logger.info("Loaded QoS model from %s", model_path)
            logger.info("QoS feature order: %s", self.feature_cols)
            return True

        except Exception as exc:
            logger.error("Error loading QoS model: %s", exc)
            return False

    def _decode_label(self, pred: Any) -> str:
        if isinstance(pred, (np.integer, int)):
            return LABEL_MAP.get(int(pred), str(pred))
        if isinstance(pred, (np.floating, float)) and float(pred).is_integer():
            return LABEL_MAP.get(int(pred), str(pred))
        try:
            code = int(pred)
        except (TypeError, ValueError):
            return str(pred)
        return LABEL_MAP.get(code, str(pred))

    def _get_class_labels(self) -> List[str] | None:
        classes = None
        if hasattr(self.model, "classes_"):
            classes = list(self.model.classes_)
        else:
            steps = getattr(self.model, "steps", None)
            if steps:
                for _, step in reversed(steps):
                    if hasattr(step, "classes_"):
                        classes = list(step.classes_)
                        break

        if classes is None:
            return None
        return [self._decode_label(value) for value in classes]

    def predict(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Run QoS prediction using the loaded model."""
        if not self.is_loaded:
            raise RuntimeError("QoS model not loaded. Call load_model() first.")

        features = build_features(raw)
        missing = [name for name in self.feature_cols if name not in features]
        if missing:
            raise ValueError(f"Missing features: {', '.join(missing)}")

        feature_frame = pd.DataFrame([features], columns=self.feature_cols)
        pred = self.model.predict(feature_frame)[0]
        label = self._decode_label(pred)

        probabilities: Dict[str, float] = {}
        confidence: float | None = None
        if hasattr(self.model, "predict_proba"):
            prob_values = self.model.predict_proba(feature_frame)[0]
            class_labels = self._get_class_labels()
            if class_labels and len(class_labels) == len(prob_values):
                probabilities = {
                    class_label: float(prob)
                    for class_label, prob in zip(class_labels, prob_values)
                }
            else:
                probabilities = {
                    str(idx): float(prob)
                    for idx, prob in enumerate(prob_values)
                }
            confidence = round(float(np.max(prob_values)) * 100, 2)

        return {
            "predicted_class": label,
            "confidence": confidence,
            "probabilities": probabilities,
        }

    def get_status(self) -> Dict[str, Any]:
        """Return current QoS model status and metadata."""
        if not self.is_loaded:
            loaded = self.load_model()
            if not loaded:
                model_path = self._resolve_model_path()
                return {
                    "loaded": False,
                    "model_path": str(model_path),
                    "feature_cols": [],
                    "error": "QoS model not loaded",
                }

        return {
            "loaded": True,
            "model_path": str(self.model_path or self._resolve_model_path()),
            "model_type": type(self.model).__name__ if self.model else None,
            "feature_count": len(self.feature_cols),
            "feature_cols": list(self.feature_cols),
            "classes": [LABEL_MAP[key] for key in sorted(LABEL_MAP.keys())],
        }


qos_service = QoSService()
