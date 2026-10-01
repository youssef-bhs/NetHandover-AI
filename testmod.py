import pickle
import numpy as np
import pandas as pd


class _CoverageUnpickler(pickle.Unpickler):
    """Handle numpy 2.x module paths saved in older environments."""

    def find_class(self, module, name):
        if module.startswith("numpy._core"):
            module = module.replace("numpy._core", "numpy.core", 1)
        return super().find_class(module, name)

# 1. Load the pkl
with open("models/network_coverage_model.pkl", "rb") as f:
    artifacts = _CoverageUnpickler(f).load()

model  = artifacts["model"]
scaler = artifacts["scaler"]
le     = artifacts["label_encoder"]
FEATURE_COLS = artifacts["feature_cols"]

print("✅ Model loaded")
print("Features:", FEATURE_COLS)
print("Classes:", list(le.classes_))

# 2. Test with Mauvaise values
rsrp = -110.0
rsrq = -10.4
rlc = 8.5
test_input = {
    "RSRP": rsrp, "RSRQ": rsrq, "RLC_DL": rlc, "PCI": 227, "Band_enc": 1,
    "hour": 10, "minute": 30, "second": 15,
    "RSRP_lag1": rsrp - 0.5, "RSRP_lag2": rsrp - 1.0,
    "RSRP_roll3": rsrp - 0.3, "RSRP_roll5": rsrp - 0.2,
    "RSRQ_lag1": rsrq - 0.2, "RSRQ_lag2": rsrq - 0.4,
    "RSRQ_roll3": rsrq - 0.1, "RSRQ_roll5": rsrq - 0.1,
    "RLC_DL_lag1": rlc - 0.5, "RLC_DL_lag2": rlc - 0.8,
    "RLC_DL_roll3": rlc - 0.3, "RLC_DL_roll5": rlc - 0.2
}

# 3. Build feature array in exact order
X = pd.DataFrame([[float(test_input[col]) for col in FEATURE_COLS]], columns=FEATURE_COLS)
print("\nRaw features:", X)

# 4. Scale
X_scaled = scaler.transform(X)
print("Scaled features:", X_scaled)

# 5. Predict
pred_code = model.predict(X_scaled)[0]
proba     = model.predict_proba(X_scaled)[0]

print("\n" + "="*40)
print("Predicted class :", le.inverse_transform([pred_code])[0])
print("Confidence      :", round(proba.max() * 100, 2), "%")
print("Probabilities   :")
for cls, p in zip(le.classes_, proba):
    print(f"  {cls:15s}: {p:.4f}")
print("="*40)