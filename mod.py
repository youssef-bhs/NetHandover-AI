import os
from pathlib import Path
if "LOKY_MAX_CPU_COUNT" not in os.environ:
    cpu_limit = os.cpu_count() or 1
    if cpu_limit > 1:
        cpu_limit -= 1
    os.environ["LOKY_MAX_CPU_COUNT"] = str(cpu_limit)

import pandas as pd
import numpy as np
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, confusion_matrix,
                              ConfusionMatrixDisplay, roc_auc_score)
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier
from imblearn.combine import SMOTETomek
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings("ignore")

# ── Palette ───────────────────────────────────────────────────────────────────
PALETTE = {
    "Tres bonne": "#1a7abf",
    "Bonne":      "#808080",
    "Moyenne":    "#f5d742",
    "Mauvaise":   "#2ecc40"
}
CLASS_ORDER = ["Tres bonne", "Bonne", "Moyenne", "Mauvaise"]
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.family": "DejaVu Sans"})

# ── Load & Merge ──────────────────────────────────────────────────────────────
raw = pd.read_excel(r"C:\Users\bhsyo\Desktop\projet mob\data\raw\DT1.xlsx")
raw.columns = ["Time", "PCI", "Band", "RSRP", "RSRQ", "RLC_DL"]
raw["Time"] = pd.to_datetime(raw["Time"], format="%H:%M:%S.%f", errors="coerce")
raw = raw.sort_values("Time").reset_index(drop=True)

rsrp_df = raw[raw["RSRP"].notna() & raw["Time"].notna()][["Time","PCI","Band","RSRP","RSRQ"]].sort_values("Time").reset_index(drop=True)
rlc_df  = raw[raw["RLC_DL"].notna() & raw["Time"].notna()][["Time","RLC_DL"]].sort_values("Time").reset_index(drop=True)

df = pd.merge_asof(rsrp_df, rlc_df, on="Time", direction="nearest", tolerance=pd.Timedelta("2s"))
df = df.dropna().drop_duplicates().reset_index(drop=True)

def rsrp_to_class(v):
    if   v >= -80:  return "Tres bonne"
    elif v >= -90:  return "Bonne"
    elif v >= -100: return "Moyenne"
    else:           return "Mauvaise"

df["coverage_zone"] = df["RSRP"].apply(rsrp_to_class)

df["hour"]     = df["Time"].dt.hour
df["minute"]   = df["Time"].dt.minute
df["second"]   = df["Time"].dt.second
df["Band_enc"] = df["Band"].astype("category").cat.codes

for col in ["RSRP", "RSRQ", "RLC_DL"]:
    df[f"{col}_lag1"]  = df[col].shift(1)
    df[f"{col}_lag2"]  = df[col].shift(2)
    df[f"{col}_roll3"] = df[col].rolling(3, min_periods=1).mean()
    df[f"{col}_roll5"] = df[col].rolling(5, min_periods=1).mean()

df = df.dropna().reset_index(drop=True)

FEATURE_COLS = [
    "RSRP", "RSRQ", "RLC_DL", "PCI", "Band_enc",
    "hour", "minute", "second",
    "RSRP_lag1", "RSRP_lag2", "RSRP_roll3", "RSRP_roll5",
    "RSRQ_lag1", "RSRQ_lag2", "RSRQ_roll3", "RSRQ_roll5",
    "RLC_DL_lag1","RLC_DL_lag2","RLC_DL_roll3","RLC_DL_roll5"
]

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — DATA EXPLORATION
# ═══════════════════════════════════════════════════════════════════════════════
fig1, axes = plt.subplots(3, 3, figsize=(20, 16))
fig1.patch.set_facecolor("#f8f9fa")
fig1.suptitle("📊 Exploration des Données — Drive Test LTE",
              fontsize=17, fontweight="bold", y=0.98, color="#1a1a2e")

# 1-1 Class distribution
ax = axes[0, 0]
vc = df["coverage_zone"].value_counts()
bars = ax.bar([c for c in CLASS_ORDER if c in vc.index],
              [vc.get(c, 0) for c in CLASS_ORDER if c in vc.index],
              color=[PALETTE[c] for c in CLASS_ORDER if c in vc.index],
              edgecolor="white", lw=1.5, zorder=3)
ax.set_title("Distribution des Classes de Couverture", fontweight="bold")
ax.set_ylabel("Nombre d'échantillons")
for b in bars:
    pct = int(b.get_height()) / len(df) * 100
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+5,
            f"{int(b.get_height())}\n({pct:.1f}%)", ha="center", fontsize=8)
ax.tick_params(axis="x", rotation=12)

# 1-2 RSRP distribution with thresholds
ax = axes[0, 1]
ax.hist(df["RSRP"], bins=50, color="#1a7abf", edgecolor="white", alpha=0.85)
for th, col, lbl in [(-80,"#2ecc40","−80 dBm (TB/B)"),
                      (-90,"#f5d742","−90 dBm (B/M)"),
                      (-100,"#e74c3c","−100 dBm (M/Mv)")]:
    ax.axvline(th, color=col, ls="--", lw=2, label=lbl)
ax.set_title("Distribution RSRP (dBm)", fontweight="bold")
ax.set_xlabel("RSRP (dBm)"); ax.set_ylabel("Fréquence")
ax.legend(fontsize=8)

# 1-3 RSRQ distribution
ax = axes[0, 2]
ax.hist(df["RSRQ"], bins=40, color="#f39c12", edgecolor="white", alpha=0.85)
ax.axvline(df["RSRQ"].mean(), color="red", ls="--", lw=1.5,
           label=f"Moyenne={df['RSRQ'].mean():.1f}")
ax.set_title("Distribution RSRQ (dB)", fontweight="bold")
ax.set_xlabel("RSRQ (dB)"); ax.set_ylabel("Fréquence")
ax.legend(fontsize=8)

# 1-4 RLC_DL distribution
ax = axes[1, 0]
ax.hist(df["RLC_DL"], bins=40, color="#27ae60", edgecolor="white", alpha=0.85)
ax.axvline(df["RLC_DL"].mean(), color="red", ls="--", lw=1.5,
           label=f"Moyenne={df['RLC_DL'].mean():.1f} Mbps")
ax.set_title("Distribution Débit DL (Mbps)", fontweight="bold")
ax.set_xlabel("RLC DL (Mbps)"); ax.set_ylabel("Fréquence")
ax.legend(fontsize=8)

# 1-5 RSRP vs RSRQ scatter
ax = axes[1, 1]
for cls in CLASS_ORDER:
    g = df[df["coverage_zone"] == cls]
    ax.scatter(g["RSRP"], g["RSRQ"], c=PALETTE[cls],
               label=cls, alpha=0.4, s=10, rasterized=True)
for th in [-80, -90, -100]:
    ax.axvline(th, color="gray", ls="--", lw=0.8, alpha=0.6)
ax.set_title("RSRP vs RSRQ par Classe", fontweight="bold")
ax.set_xlabel("RSRP (dBm)"); ax.set_ylabel("RSRQ (dB)")
ax.legend(fontsize=7, markerscale=2)

# 1-6 RSRP vs RLC_DL scatter
ax = axes[1, 2]
for cls in CLASS_ORDER:
    g = df[df["coverage_zone"] == cls]
    ax.scatter(g["RSRP"], g["RLC_DL"], c=PALETTE[cls],
               label=cls, alpha=0.4, s=10, rasterized=True)
ax.set_title("RSRP vs Débit DL par Classe", fontweight="bold")
ax.set_xlabel("RSRP (dBm)"); ax.set_ylabel("Débit DL (Mbps)")
ax.legend(fontsize=7, markerscale=2)

# 1-7 Boxplot RSRP per class
ax = axes[2, 0]
bp = ax.boxplot([df[df["coverage_zone"]==c]["RSRP"].values for c in CLASS_ORDER],
                patch_artist=True, medianprops=dict(color="black", lw=2))
for patch, cls in zip(bp["boxes"], CLASS_ORDER):
    patch.set_facecolor(PALETTE[cls]); patch.set_alpha(0.8)
ax.set_xticklabels(CLASS_ORDER, rotation=12, fontsize=8)
ax.set_title("RSRP par Classe de Couverture", fontweight="bold")
ax.set_ylabel("RSRP (dBm)")

# 1-8 Boxplot RLC_DL per class
ax = axes[2, 1]
bp = ax.boxplot([df[df["coverage_zone"]==c]["RLC_DL"].values for c in CLASS_ORDER],
                patch_artist=True, medianprops=dict(color="black", lw=2))
for patch, cls in zip(bp["boxes"], CLASS_ORDER):
    patch.set_facecolor(PALETTE[cls]); patch.set_alpha(0.8)
ax.set_xticklabels(CLASS_ORDER, rotation=12, fontsize=8)
ax.set_title("Débit DL par Classe de Couverture", fontweight="bold")
ax.set_ylabel("Débit DL (Mbps)")

# 1-9 Correlation heatmap
ax = axes[2, 2]
corr = df[["RSRP", "RSRQ", "RLC_DL", "PCI"]].corr()
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
            center=0, linewidths=0.5, ax=ax, cbar=True)
ax.set_title("Matrice de Corrélation des KPIs", fontweight="bold")

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("plot1_exploration.png", dpi=140, bbox_inches="tight",
            facecolor=fig1.get_facecolor())
plt.close()
print("✅ Figure 1 saved → plot1_exploration.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — TIME SERIES & TEMPORAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
fig2, axes = plt.subplots(3, 1, figsize=(20, 14))
fig2.patch.set_facecolor("#f8f9fa")
fig2.suptitle("📡 Analyse Temporelle — Drive Test LTE",
              fontsize=17, fontweight="bold", y=0.99, color="#1a1a2e")

# 2-1 RSRP time series coloured by class
ax = axes[0]
for cls in CLASS_ORDER:
    g = df[df["coverage_zone"] == cls]
    ax.scatter(g.index, g["RSRP"], c=PALETTE[cls],
               label=cls, alpha=0.55, s=5, rasterized=True)
for th, col in [(-80,"#1a7abf"),(-90,"#808080"),(-100,"#e74c3c")]:
    ax.axhline(th, color=col, ls="--", lw=1, alpha=0.7)
ax.set_title("Série Temporelle RSRP — Carte de Qualité de Couverture",
             fontweight="bold")
ax.set_xlabel("Index (chronologique)"); ax.set_ylabel("RSRP (dBm)")
handles = [mpatches.Patch(color=PALETTE[c], label=c) for c in CLASS_ORDER]
ax.legend(handles=handles, fontsize=8, loc="lower right")

# 2-2 RLC_DL time series
ax = axes[1]
for cls in CLASS_ORDER:
    g = df[df["coverage_zone"] == cls]
    ax.scatter(g.index, g["RLC_DL"], c=PALETTE[cls],
               label=cls, alpha=0.45, s=5, rasterized=True)
ax.set_title("Série Temporelle Débit DL", fontweight="bold")
ax.set_xlabel("Index (chronologique)"); ax.set_ylabel("Débit DL (Mbps)")
handles = [mpatches.Patch(color=PALETTE[c], label=c) for c in CLASS_ORDER]
ax.legend(handles=handles, fontsize=8, loc="upper right")

# 2-3 RSRP rolling mean vs raw
ax = axes[2]
ax.plot(df.index, df["RSRP"], color="#1a7abf", alpha=0.3, lw=0.6, label="RSRP brut")
ax.plot(df.index, df["RSRP_roll3"], color="#e74c3c", lw=1.2, label="Moyenne glissante 3")
ax.plot(df.index, df["RSRP_roll5"], color="#f39c12", lw=1.2, label="Moyenne glissante 5")
ax.set_title("RSRP Brut vs Moyennes Glissantes (lag features)", fontweight="bold")
ax.set_xlabel("Index (chronologique)"); ax.set_ylabel("RSRP (dBm)")
ax.legend(fontsize=9)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig("plot2_timeseries.png", dpi=140, bbox_inches="tight",
            facecolor=fig2.get_facecolor())
plt.close()
print("✅ Figure 2 saved → plot2_timeseries.png")

# ═══════════════════════════════════════════════════════════════════════════════
# TRAIN MODEL
# ═══════════════════════════════════════════════════════════════════════════════
X = df[FEATURE_COLS].copy()
le = LabelEncoder()
y  = le.fit_transform(df["coverage_zone"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_tr_sc = scaler.fit_transform(X_train)
X_te_sc = scaler.transform(X_test)

k = min(4, min(np.bincount(y_train)) - 1)
X_res, y_res = SMOTETomek(
    smote=SMOTE(random_state=42, k_neighbors=k), random_state=42
).fit_resample(X_tr_sc, y_train)
sample_weights = compute_sample_weight("balanced", y=y_res)

model = XGBClassifier(n_estimators=400, max_depth=5, learning_rate=0.08,
                      subsample=0.75, colsample_bytree=0.75,
                      min_child_weight=3, gamma=0.15,
                      eval_metric="mlogloss", random_state=42, n_jobs=-1)
model.fit(X_res, y_res, sample_weight=sample_weights)

y_pred  = model.predict(X_te_sc)
y_proba = model.predict_proba(X_te_sc)
acc     = (y_pred == y_test).mean()
report  = classification_report(y_test, y_pred,
                                 target_names=le.classes_, output_dict=True)
cm      = confusion_matrix(y_test, y_pred)
auc     = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")

print(classification_report(y_test, y_pred, target_names=le.classes_))

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — MODEL EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════
fig3, axes = plt.subplots(2, 3, figsize=(20, 12))
fig3.patch.set_facecolor("#f8f9fa")
fig3.suptitle("🤖 Évaluation du Modèle XGBoost — Prédiction de Couverture LTE",
              fontsize=16, fontweight="bold", y=0.99, color="#1a1a2e")

# 3-1 Confusion matrix
ax = axes[0, 0]
ConfusionMatrixDisplay(cm, display_labels=le.classes_).plot(
    ax=ax, colorbar=False, cmap="Blues")
ax.set_title("Matrice de Confusion (Ensemble de Test)",
             fontweight="bold", fontsize=11)
ax.tick_params(axis="x", rotation=15)

# 3-2 Precision/Recall/F1
ax = axes[0, 1]
met_df = pd.DataFrame({k: report[k] for k in le.classes_},
                       index=["precision","recall","f1-score"]).T
x = np.arange(len(met_df)); w = 0.25
for i, (m, c) in enumerate(zip(["precision","recall","f1-score"],
                                ["#2196F3","#4CAF50","#FF9800"])):
    ax.bar(x+i*w, met_df[m], w, label=m.capitalize(), color=c, alpha=0.87, zorder=3)
ax.set_xticks(x+w)
ax.set_xticklabels(met_df.index, rotation=12, fontsize=9)
ax.set_ylim(0, 1.15)
ax.axhline(acc, color="red", ls="--", lw=1.2, label=f"Accuracy={acc:.2f}")
ax.set_title("Précision / Rappel / F1 par Classe", fontweight="bold", fontsize=11)
ax.legend(fontsize=8); ax.set_ylabel("Score")

# 3-3 Feature importance
ax = axes[0, 2]
imp = pd.Series(model.feature_importances_, index=FEATURE_COLS).sort_values()
thr = imp.quantile(0.75)
ax.barh(imp.index, imp.values,
        color=["#e74c3c" if v >= thr else "#3498db" for v in imp.values],
        edgecolor="white")
ax.set_title("Importance des Features (XGBoost)\n(rouge = top 25%)",
             fontweight="bold", fontsize=11)
ax.set_xlabel("Score d'importance")

# 3-4 Class probabilities distribution (violin)
ax = axes[1, 0]
prob_df = pd.DataFrame(y_proba, columns=le.classes_)
prob_df["true_class"] = le.inverse_transform(y_test)
for i, cls in enumerate(le.classes_):
    subset = prob_df[prob_df["true_class"] == cls][cls]
    parts = ax.violinplot(subset, positions=[i], showmedians=True)
    for pc in parts["bodies"]:
        pc.set_facecolor(PALETTE.get(cls, "#888")); pc.set_alpha(0.7)
ax.set_xticks(range(len(le.classes_)))
ax.set_xticklabels(le.classes_, rotation=12, fontsize=8)
ax.set_title("Distribution des Probabilités Prédites\n(pour les vrais échantillons de chaque classe)",
             fontweight="bold", fontsize=11)
ax.set_ylabel("Probabilité prédite")

# 3-5 SMOTE before/after
ax = axes[1, 1]
before = dict(zip(le.classes_, np.bincount(y_train)))
after  = dict(zip(le.classes_, np.bincount(y_res)))
x = np.arange(len(le.classes_)); w = 0.35
ax.bar(x-w/2, [before[c] for c in le.classes_], w,
       label="Avant SMOTETomek", color="#3498db", alpha=0.85)
ax.bar(x+w/2, [after[c] for c in le.classes_], w,
       label="Après SMOTETomek", color="#e74c3c", alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(le.classes_, rotation=12, fontsize=8)
ax.set_title("Rééquilibrage des Classes\nAvant vs Après SMOTETomek",
             fontweight="bold", fontsize=11)
ax.legend(fontsize=9); ax.set_ylabel("Nombre d'échantillons")

# 3-6 Accuracy gauge
ax = axes[1, 2]; ax.axis("off")
color = "#27ae60" if acc >= 0.95 else "#f39c12" if acc >= 0.80 else "#e74c3c"
ax.add_patch(plt.Circle((0.5,0.52),0.38,color=color,alpha=0.12))
ax.add_patch(plt.Circle((0.5,0.52),0.38,fill=False,edgecolor=color,lw=3.5))
ax.text(0.5,0.58,f"{acc*100:.1f}%",ha="center",va="center",
        fontsize=36,fontweight="bold",color=color)
ax.text(0.5,0.35,"Accuracy Globale",ha="center",va="center",
        fontsize=13,color="#444")
ax.text(0.5,0.23,f"AUC-ROC = {auc:.4f}",ha="center",va="center",
        fontsize=10,color=color,fontweight="bold")
ax.text(0.5,0.13,f"XGBoost | SMOTETomek | n_test={len(y_test)}",
        ha="center",va="center",fontsize=8,color="#888")
ax.set_xlim(0,1); ax.set_ylim(0,1)
ax.set_title("Performance du Modèle", fontweight="bold", fontsize=11)

plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig("plot3_evaluation.png", dpi=140, bbox_inches="tight",
            facecolor=fig3.get_facecolor())
plt.close()
print("✅ Figure 3 saved → plot3_evaluation.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — FEATURE DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════════════
fig4, axes = plt.subplots(2, 3, figsize=(20, 11))
fig4.patch.set_facecolor("#f8f9fa")
fig4.suptitle("🔬 Analyse Approfondie des Features",
              fontsize=16, fontweight="bold", y=0.99, color="#1a1a2e")

# 4-1 RSRP KDE per class
ax = axes[0, 0]
for cls in CLASS_ORDER:
    df[df["coverage_zone"]==cls]["RSRP"].plot.kde(
        ax=ax, label=cls, color=PALETTE[cls], lw=2.2)
for th, col in [(-80,"#1a7abf"),(-90,"gray"),(-100,"goldenrod")]:
    ax.axvline(th, color=col, ls="--", lw=1.1, alpha=0.75)
ax.set_title("Densité RSRP par Classe", fontweight="bold")
ax.set_xlabel("RSRP (dBm)"); ax.set_ylabel("Densité")
ax.legend(fontsize=8)

# 4-2 RSRQ KDE per class
ax = axes[0, 1]
for cls in CLASS_ORDER:
    df[df["coverage_zone"]==cls]["RSRQ"].plot.kde(
        ax=ax, label=cls, color=PALETTE[cls], lw=2.2)
ax.set_title("Densité RSRQ par Classe", fontweight="bold")
ax.set_xlabel("RSRQ (dB)"); ax.set_ylabel("Densité")
ax.legend(fontsize=8)

# 4-3 RLC_DL KDE per class
ax = axes[0, 2]
for cls in CLASS_ORDER:
    df[df["coverage_zone"]==cls]["RLC_DL"].plot.kde(
        ax=ax, label=cls, color=PALETTE[cls], lw=2.2)
ax.set_title("Densité Débit DL par Classe", fontweight="bold")
ax.set_xlabel("Débit DL (Mbps)"); ax.set_ylabel("Densité")
ax.legend(fontsize=8)

# 4-4 RSRP lag1 vs RSRP
ax = axes[1, 0]
for cls in CLASS_ORDER:
    g = df[df["coverage_zone"]==cls]
    ax.scatter(g["RSRP"], g["RSRP_lag1"], c=PALETTE[cls],
               label=cls, alpha=0.3, s=8, rasterized=True)
ax.plot([-130,-50],[-130,-50], "k--", lw=1, alpha=0.5, label="y=x")
ax.set_title("RSRP vs RSRP Lag 1\n(Stabilité du signal)", fontweight="bold")
ax.set_xlabel("RSRP (t)"); ax.set_ylabel("RSRP (t−1)")
ax.legend(fontsize=7, markerscale=2)

# 4-5 Cumulative feature importance
ax = axes[1, 1]
imp_desc = imp.sort_values(ascending=False)
cumul    = np.cumsum(imp_desc.values) / imp_desc.sum()
ax.plot(range(1,len(cumul)+1), cumul, "o-", color="#1a7abf", lw=2)
ax.axhline(0.80, color="red",    ls="--", lw=1.2, label="80%")
ax.axhline(0.90, color="orange", ls="--", lw=1.2, label="90%")
ax.fill_between(range(1,len(cumul)+1), cumul, alpha=0.1, color="#1a7abf")
ax.set_title("Importance Cumulée des Features", fontweight="bold")
ax.set_xlabel("Nombre de features")
ax.set_ylabel("Importance cumulée")
ax.set_xticks(range(1,len(cumul)+1))
ax.set_xticklabels(imp_desc.index, rotation=45, ha="right", fontsize=7)
ax.legend(fontsize=9)

# 4-6 Stats table per class
ax = axes[1, 2]; ax.axis("off")
stats = df.groupby("coverage_zone")[["RSRP","RSRQ","RLC_DL"]].mean().round(1)
stats = stats.reindex([c for c in CLASS_ORDER if c in stats.index])
table_data = [[cls,
               f"{stats.loc[cls,'RSRP']:.1f}",
               f"{stats.loc[cls,'RSRQ']:.1f}",
               f"{stats.loc[cls,'RLC_DL']:.1f}"]
              for cls in stats.index]
col_labels = ["Classe","RSRP moy.\n(dBm)","RSRQ moy.\n(dB)","Débit moy.\n(Mbps)"]
tbl = ax.table(cellText=table_data, colLabels=col_labels,
               loc="center", cellLoc="center")
tbl.auto_set_font_size(False); tbl.set_fontsize(10)
tbl.scale(1.2, 2.2)
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_facecolor("#1a7abf"); cell.set_text_props(color="white", fontweight="bold")
    elif r > 0 and c == 0:
        cls_name = table_data[r-1][0]
        cell.set_facecolor(PALETTE.get(cls_name, "#fff"))
        cell.set_text_props(fontweight="bold")
    else:
        cell.set_facecolor("#f8f9fa" if r % 2 == 0 else "white")
    cell.set_edgecolor("#ddd")
ax.set_title("Statistiques Moyennes par Classe", fontweight="bold", pad=20)

plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig("plot4_features.png", dpi=140, bbox_inches="tight",
            facecolor=fig4.get_facecolor())
plt.close()
print("✅ Figure 4 saved → plot4_features.png")

# ── Quick test ────────────────────────────────────────────────────────────────
print("\n--- Tests de validation ---")
for label, rsrp, rsrq, rlc in [
    ("Tres bonne", -72.0, -5.0,  25.0),
    ("Bonne",      -85.0, -8.3,  11.8),
    ("Moyenne",    -95.0, -9.3,  10.3),
    ("Mauvaise",  -110.0,-10.4,   8.5),
]:
    t = {col: 0.0 for col in FEATURE_COLS}
    t.update({"RSRP": rsrp, "RSRQ": rsrq, "RLC_DL": rlc, "PCI": 227,
              "Band_enc": 1, "hour": 10, "minute": 30, "second": 15,
              "RSRP_lag1": rsrp-0.5, "RSRP_lag2": rsrp-1.0,
              "RSRP_roll3": rsrp-0.3, "RSRP_roll5": rsrp-0.2,
              "RSRQ_lag1": rsrq-0.2, "RSRQ_lag2": rsrq-0.4,
              "RSRQ_roll3": rsrq-0.1, "RSRQ_roll5": rsrq-0.1,
              "RLC_DL_lag1": rlc-0.5, "RLC_DL_lag2": rlc-0.8,
              "RLC_DL_roll3": rlc-0.3, "RLC_DL_roll5": rlc-0.2})
    X_t  = pd.DataFrame([[float(t[c]) for c in FEATURE_COLS]], columns=FEATURE_COLS)
    X_ts = scaler.transform(X_t)
    pred  = le.inverse_transform(model.predict(X_ts))[0]
    proba = model.predict_proba(X_ts)[0].max()
    status = "✅" if pred == label else "❌"
    print(f"{status} Expected: {label:12s} → Got: {pred:12s} ({proba*100:.1f}%)")

# ── Save model ────────────────────────────────────────────────────────────────
output_dir = Path("models")
output_dir.mkdir(exist_ok=True)
model_path = output_dir / "network_coverage_model.pkl"
with open(model_path, "wb") as f:
    pickle.dump({"model": model, "scaler": scaler,
                 "label_encoder": le, "feature_cols": FEATURE_COLS}, f)
print(f"\n✅ Modèle sauvegardé → {model_path}")
print(f"✅ Accuracy: {acc:.4f} | AUC-ROC: {auc:.4f}")
print("✅ 4 figures sauvegardées: plot1_exploration.png, plot2_timeseries.png, plot3_evaluation.png, plot4_features.png")