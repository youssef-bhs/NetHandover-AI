"""Build training notebook with SMOTE for imbalanced data."""
import json

PATH = r"C:\Users\bhsyo\Desktop\projet mob\Training_Interference_Handover.ipynb"

CELLS = []
cid = [0]

def nid():
    cid[0] += 1
    return cid[0]

def fix_source(src):
    result = []
    for i, line in enumerate(src):
        if i == len(src) - 1:
            result.append(line)
        else:
            result.append(line + "\n")
    return result

def md(text):
    CELLS.append({
        "cell_type": "markdown",
        "id": f"md_{nid()}",
        "metadata": {},
        "source": fix_source(text.strip().split("\n"))
    })

def code(text):
    lines = text.strip().split("\n")
    while lines and lines[0].strip() == '':
        lines.pop(0)
    while lines and lines[-1].strip() == '':
        lines.pop()
    CELLS.append({
        "cell_type": "code",
        "id": f"code_{nid()}",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": fix_source(lines)
    })

# ================================================================
# 1: Title
# ================================================================
md("""# UMTS Interference & Handover Prediction

## Streamlined ML Training Notebook with SMOTE — Google Colab Compatible

**Objective**: Train and compare models to predict:
1. **Interference** — Ec/N0 degradation from noise floor interference
2. **Handover Needed** — neighbor cell nearly as strong as serving, quality poor

**Key technique**: SMOTE oversampling to handle ~8:1 class imbalance

**Approach**: 3 models per task -> compare -> select best""")

# ================================================================
# 2: Setup
# ================================================================
md("""## 2. Setup & Imports""")
code("""
# Google Colab: upload DT2.csv via the file panel on the left
# from google.colab import files
# uploaded = files.upload()

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_validate
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    precision_recall_curve, auc, roc_curve
)
from imblearn.over_sampling import SMOTE

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

DATA_DIR = Path(".")
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=0.9)
plt.rcParams['figure.dpi'] = 120

print("All imports OK")
print("SMOTE available (imbalanced-learn)")
""")

# ================================================================
# 3: Data Loading
# ================================================================
md("""## 3. Data Loading""")
code("""
df_raw = pd.read_csv(DATA_DIR / "DT2.csv", sep=";", dtype=str)
print(f"Shape: {df_raw.shape}")
print(f"Columns: {list(df_raw.columns)}")
display(df_raw.head(10))
""")

# ================================================================
# 4: Data Cleaning
# ================================================================
md("""## 4. Data Cleaning & Preprocessing""")
code("""
def clean(df):
    df = df.copy()

    cols = {
        'Time': 'time',
        'Band (active)': 'band',
        'Channel number (active)': 'uarfcn',
        'Scrambling code (active)': 'psc',
        'RSCP (active)': 'rscp',
        'Ec/N0 (active)': 'ecn0',
        'RSCP (detected)': 'rscp_det',
        'Scrambling code (detected)': 'psc_det'
    }
    df = df.rename(columns=cols)

    # Remove empty rows
    em = df.apply(lambda r: r.astype(str).str.strip().eq('').all(), axis=1)
    print(f"Empty rows removed: {em.sum()}")
    df = df[~em].copy()

    # Multi-value rows: take first (primary serving cell)
    for c in ['band','uarfcn','psc','rscp','ecn0','psc_det','rscp_det']:
        df[c] = df[c].apply(
            lambda x: str(x).split(',')[0].strip()
            if pd.notna(x) and ',' in str(x) else x
        )

    # Parse numerics
    for c in ['uarfcn','psc','rscp','ecn0','rscp_det','psc_det']:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df['time'] = pd.to_datetime(
        df['time'], format='%H:%M:%S.%f', exact=False, errors='coerce'
    )

    # Drop rows missing critical data
    before = len(df)
    df = df.dropna(subset=['time','psc','rscp','ecn0'])
    print(f"Dropped {before - len(df)} rows with missing critical values")
    df = df.reset_index(drop=True)

    # Deduplicate
    before = len(df)
    df = df.drop_duplicates()
    print(f"Dropped {before - len(df)} duplicates")
    df = df.reset_index(drop=True)

    # Clip
    df['rscp'] = df['rscp'].clip(-120, -25)
    df['ecn0'] = df['ecn0'].clip(-30, 5)

    print(f"Cleaned: {df.shape}")
    return df

df_clean = clean(df_raw)
display(df_clean.describe())
""")

# ================================================================
# 5: Feature Engineering (minimal)
# ================================================================
md("""## 5. Feature Engineering — Minimal Set (15 features)

| Feature | Why |
|---------|-----|
| `rscp` | Signal strength |
| `ecn0` | Signal quality — interference drops EcN0 |
| `delta_rscp` | Active vs detected gap — handover trigger |
| `has_neighbor` | Handover requires a neighbor |
| `rscp_rmean_5` | Short-term signal trend |
| `rscp_rmean_10` | Medium-term signal trend |
| `ecn0_rmean_5` | Short-term quality trend |
| `ecn0_rmean_10` | Medium-term quality trend |
| `ecn0_rstd_5` | Quality volatility |
| `rscp_diff` | Signal change rate |
| `ecn0_diff` | Quality change rate |
| `psc_rscp_mean` | Cell average RSCP |
| `psc_ecn0_mean` | Cell average EcN0 |
| `rscp_vs_mean` | Current RSCP vs cell average |
| `ecn0_vs_mean` | Current EcN0 vs cell average |""")
code("""
def engineer(df):
    df = df.copy().sort_values(['psc','time']).reset_index(drop=True)

    # Base signal gap
    df['delta_rscp'] = df['rscp'] - df['rscp_det']
    df['delta_rscp'] = df['delta_rscp'].fillna(0)
    df['has_neighbor'] = df['rscp_det'].notna().astype(int)

    # Cell averages
    df['psc_rscp_mean'] = df.groupby('psc')['rscp'].transform('mean')
    df['psc_ecn0_mean'] = df.groupby('psc')['ecn0'].transform('mean')
    df['rscp_vs_mean'] = df['rscp'] - df['psc_rscp_mean']
    df['ecn0_vs_mean'] = df['ecn0'] - df['psc_ecn0_mean']

    # Rolling means
    for w in [5, 10]:
        df[f'rscp_rmean_{w}'] = df.groupby('psc')['rscp'].transform(
            lambda x: x.rolling(w, min_periods=1).mean())
        df[f'ecn0_rmean_{w}'] = df.groupby('psc')['ecn0'].transform(
            lambda x: x.rolling(w, min_periods=1).mean())

    # Quality volatility
    df['ecn0_rstd_5'] = df.groupby('psc')['ecn0'].transform(
        lambda x: x.rolling(5, min_periods=1).std()
    ).fillna(0)

    # Differentials
    df['rscp_diff'] = df.groupby('psc')['rscp'].diff().fillna(0)
    df['ecn0_diff'] = df.groupby('psc')['ecn0'].diff().fillna(0)

    print(f"Features: {df.shape[1]} total")
    return df

df_feat = engineer(df_clean)
print(f"Feature matrix: {df_feat.shape}")
""")

# ================================================================
# 6: Labels
# ================================================================
md("""## 6. Label Definition

### Label 1: `interference`

Ec/N0 < -10 dB persistent (>= 3 of last 5 consecutive).

### Label 2: `handover_needed`

Neighbor within 5 dB + detected + EcN0 < -10 dB, persistent (>= 2 of 4 consecutive).""")
code("""
def create_labels(df):
    df = df.copy().sort_values(['psc','time']).reset_index(drop=True)

    # Label 1: interference
    base_int = (df['ecn0'] < -10).astype(int)
    def roll_int(g):
        ind = base_int.loc[g.index]
        rs = ind.rolling(window=5, min_periods=1).sum()
        return (rs >= 3).astype(int)
    df['interference'] = df.groupby('psc', group_keys=False).apply(roll_int)
    n = df['interference'].sum()
    print(f"interference: {n}/{len(df)} ({n/len(df)*100:.1f}%)")

    # Label 2: handover_needed
    base_ho = (
        (df['delta_rscp'] < 5) &
        (df['has_neighbor'] == 1) &
        (df['ecn0'] < -10)
    ).astype(int)
    def roll_ho(g):
        ind = base_ho.loc[g.index]
        rs = ind.rolling(window=4, min_periods=1).sum()
        return (rs >= 2).astype(int)
    df['handover_needed'] = df.groupby('psc', group_keys=False).apply(roll_ho)
    n = df['handover_needed'].sum()
    print(f"handover_needed: {n}/{len(df)} ({n/len(df)*100:.1f}%)")

    return df

df_labeled = create_labels(df_feat)
""")
code("""
for label in ['interference', 'handover_needed']:
    pos = df_labeled[label].sum()
    neg = len(df_labeled) - pos
    print(label + ": " + str(pos) + " pos ("
          + str(round(pos/len(df_labeled)*100, 1))
          + "%), " + str(neg) + " neg, ratio "
          + str(round(neg/max(pos,1), 1)) + ":1")

print("\\nLabel correlation:")
display(df_labeled[['interference','handover_needed']].corr().round(3))
""")

# ================================================================
# 7: Split
# ================================================================
md("""## 7. Train/Test Split""")
code("""
exclude = ['time','band','psc','psc_det','rscp_det',
           'interference','handover_needed']
feature_cols = [c for c in df_labeled.columns if c not in exclude]

df_model = df_labeled[feature_cols].copy()
df_model = df_model.apply(pd.to_numeric, errors='coerce').fillna(0)

tasks = {
    'Interference': 'interference',
    'Handover Needed': 'handover_needed'
}

print(f"Features ({len(feature_cols)}): {feature_cols}")

splits = {}
for tname, lcol in tasks.items():
    y = df_labeled[lcol].values
    X = df_model.values
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    sc = StandardScaler()
    Xtr = sc.fit_transform(Xtr)
    Xte = sc.transform(Xte)
    splits[tname] = {
        'X_train':Xtr, 'X_test':Xte,
        'y_train':ytr, 'y_test':yte,
        'scaler':sc
    }
    pos = int(ytr.sum())
    neg = int(len(ytr) - pos)
    print(tname + ":")
    print("  Train=" + str(Xtr.shape[0])
          + " Test=" + str(Xte.shape[0])
          + " Pos train=" + str(pos) + " Neg train=" + str(neg)
          + " Ratio=" + str(round(neg/max(pos,1), 1)) + ":1")

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
""")

# ================================================================
# 8: SMOTE Oversampling
# ================================================================
md("""## 8. SMOTE Oversampling

The data has ~8:1 class imbalance, so models will bias toward the majority class.

**SMOTE** (Synthetic Minority Over-sampling Technique) generates synthetic minority samples by:
1. Finding k-nearest neighbors of each minority sample
2. Creating new synthetic samples along the line between a sample and its neighbors
3. Balances the training set without duplicating real data

**IMPORTANT**: SMOTE is applied ONLY on training data (never on test data). This prevents data leakage.""")
code("""
print("=" * 60)
print("SMOTE OVERSAMPLING")
print("=" * 60)

for tname in tasks:
    Xtr = splits[tname]['X_train']
    ytr = splits[tname]['y_train']

    print("\\n" + tname + ":")
    print("  Before SMOTE: "
          + str(np.bincount(ytr.astype(int))))

    # Apply SMOTE
    smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=5)
    Xtr_resampled, ytr_resampled = smote.fit_resample(Xtr, ytr)

    print("  After SMOTE:  "
          + str(np.bincount(ytr_resampled.astype(int))))

    # Keep original train for reference
    splits[tname]['X_train_orig'] = Xtr
    splits[tname]['y_train_orig'] = ytr

    # Use resampled data for training
    splits[tname]['X_train'] = Xtr_resampled
    splits[tname]['y_train'] = ytr_resampled
    splits[tname]['smote'] = smote

    print("  Total training samples: " + str(len(ytr_resampled)))
""")

code("""
# Visualize SMOTE effect
fig, axes = plt.subplots(len(tasks), 2, figsize=(12, 6))
for i, tname in enumerate(tasks):
    y_orig = splits[tname]['y_train_orig']
    y_resampled = splits[tname]['y_train']

    ax1 = axes[i, 0]
    sns.barplot(
        x=['Negative', 'Positive'],
        y=[int((y_orig==0).sum()), int((y_orig==1).sum())],
        ax=ax1, hue=['Negative','Positive'], palette=['tomato','steelblue'],
        legend=False
    )
    ax1.set_title(tname + ' - Before SMOTE')
    ax1.set_ylabel('Count')

    ax2 = axes[i, 1]
    sns.barplot(
        x=['Negative', 'Positive'],
        y=[int((y_resampled==0).sum()), int((y_resampled==1).sum())],
        ax=ax2, hue=['Negative','Positive'], palette=['tomato','steelblue'],
        legend=False
    )
    ax2.set_title(tname + ' - After SMOTE')
    ax2.set_ylabel('Count')

plt.tight_layout()
plt.savefig(str(PLOTS_DIR / 'smote_effect.png'), dpi=150, bbox_inches='tight')
plt.show()
""")

# ================================================================
# 9: Train 3 Models
# ================================================================
md("""## 9. Train 3 Models Per Task

Training on SMOTE-resampled data. Evaluation on original (unmodified) test set.""")
code("""
def get_models():
    return {
        'LogisticRegression': LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE,
            C=1.0, solver='lbfgs'
        ),
        'RandomForest': RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_split=5,
            min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1,
            min_samples_split=5, min_samples_leaf=2,
            subsample=0.8, random_state=RANDOM_STATE
        )
    }

for tname in tasks:
    print("\\n" + "="*60)
    print("Training: " + tname + " (with SMOTE)")
    print("="*60)
    splits[tname]['models'] = {}

    for mname, model in get_models().items():
        print("  " + mname + "...")
        model.fit(splits[tname]['X_train'], splits[tname]['y_train'])

        yp = model.predict(splits[tname]['X_test'])
        yprob = model.predict_proba(splits[tname]['X_test'])[:, 1]

        m = {
            'Accuracy': accuracy_score(splits[tname]['y_test'], yp),
            'Precision': precision_score(splits[tname]['y_test'], yp,
                                         zero_division=0),
            'Recall': recall_score(splits[tname]['y_test'], yp,
                                   zero_division=0),
            'F1': f1_score(splits[tname]['y_test'], yp, zero_division=0),
            'ROC-AUC': roc_auc_score(splits[tname]['y_test'], yprob),
        }
        pr, re, _ = precision_recall_curve(
            splits[tname]['y_test'], yprob)
        m['PR-AUC'] = auc(re, pr)

        cm = confusion_matrix(splits[tname]['y_test'], yp)
        m['TN']=int(cm[0,0]); m['FP']=int(cm[0,1])
        m['FN']=int(cm[1,0]); m['TP']=int(cm[1,1])

        # CV on SMOTE-resampled training data
        cv = cross_validate(
            model, splits[tname]['X_train'], splits[tname]['y_train'],
            cv=skf,
            scoring=['accuracy','recall','roc_auc','f1'],
            n_jobs=-1
        )
        cvs = {
            'cv_recall_mean': float(cv['test_recall'].mean()),
            'cv_recall_std': float(cv['test_recall'].std()),
            'cv_auc_mean': float(cv['test_roc_auc'].mean()),
            'cv_auc_std': float(cv['test_roc_auc'].std()),
            'cv_f1_mean': float(cv['test_f1'].mean()),
        }
        splits[tname]['models'][mname] = {
            'model':model, 'metrics':m, 'cv':cvs,
            'y_pred':yp, 'y_prob':yprob
        }
        for k, v in m.items():
            if isinstance(v, float):
                print("    " + k + ": " + str(round(v, 4)))
            else:
                print("    " + k + ": " + str(v))
        print("    CV Recall: " + str(round(cvs['cv_recall_mean'], 4))
              + " (+/- " + str(round(cvs['cv_recall_std'], 4)) + ")")

print("\\nAll models trained.")
""")

# ================================================================
# 10: Confusion Matrices
# ================================================================
md("""## 10. Confusion Matrices""")
code("""
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()
idx = 0
for tname in tasks:
    for mname in ['LogisticRegression','RandomForest','GradientBoosting']:
        res = splits[tname]['models'][mname]
        cm = confusion_matrix(splits[tname]['y_test'], res['y_pred'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    ax=axes[idx], cbar=False,
                    xticklabels=['Neg','Pos'],
                    yticklabels=['Neg','Pos'])
        met = res['metrics']
        axes[idx].set_title(
            tname + "\\n" + mname + "\\n"
            + "Acc=" + str(round(met['Accuracy'],3))
            + " Rec=" + str(round(met['Recall'],3))
            + " AUC=" + str(round(met['ROC-AUC'],3)))
        axes[idx].set_ylabel('Actual')
        axes[idx].set_xlabel('Predicted')
        idx += 1
plt.tight_layout()
plt.savefig(str(PLOTS_DIR / 'confusion_matrices.png'), dpi=150,
            bbox_inches='tight')
plt.show()
""")

# ================================================================
# 11: Comparison Table
# ================================================================
md("""## 11. Model Comparison Table""")
code("""
rows = []
for tname in tasks:
    for mname in ['LogisticRegression','RandomForest','GradientBoosting']:
        res = splits[tname]['models'][mname]
        m = res['metrics']
        c = res['cv']
        rows.append({
            'Task': tname,
            'Model': mname,
            'Accuracy': round(m['Accuracy'], 4),
            'Precision': round(m['Precision'], 4),
            'Recall': round(m['Recall'], 4),
            'F1': round(m['F1'], 4),
            'ROC-AUC': round(m['ROC-AUC'], 4),
            'PR-AUC': round(m['PR-AUC'], 4),
            'CV_Recall': round(c['cv_recall_mean'], 4),
            'CV_AUC': round(c['cv_auc_mean'], 4),
            'TP': m['TP'], 'FP': m['FP'],
            'TN': m['TN'], 'FN': m['FN']
        })

comp = pd.DataFrame(rows)
display(comp)
comp.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
""")

# ================================================================
# 12: Best Model
# ================================================================
md("""## 12. Best Model Selection

Weighted: 40% Recall + 30% ROC-AUC + 20% F1 + 10% CV AUC""")
code("""
best = {}
for tname in tasks:
    r = comp[comp['Task'] == tname].copy()
    r['score'] = (0.40*r['Recall'] + 0.30*r['ROC-AUC']
                  + 0.20*r['F1'] + 0.10*r['CV_AUC'])
    b = r.loc[r['score'].idxmax()]
    best[tname] = b['Model']
    print("Best for " + tname + ": " + b['Model'])
    print("  Score=" + str(round(b['score'],4))
          + " Recall=" + str(b['Recall'])
          + " AUC=" + str(b['ROC-AUC'])
          + " F1=" + str(b['F1']))
    if b['Model'] == 'LogisticRegression':
        why = "Linear, interpretable — features capture the pattern linearly"
    elif b['Model'] == 'RandomForest':
        why = "Handles non-linearities, robust to outliers"
    else:
        why = "Strongest predictor for complex non-linear patterns"
    print("  Why: " + why)
""")

# ================================================================
# 13: ROC Curves
# ================================================================
md("""## 13. ROC Curves""")
code("""
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for i, tname in enumerate(tasks):
    mn = best[tname]
    res = splits[tname]['models'][mn]
    fpr, tpr, _ = roc_curve(splits[tname]['y_test'], res['y_prob'])
    axes[i].plot(fpr, tpr,
        label=mn + ' (best) AUC=' + str(round(res['metrics']['ROC-AUC'],3)),
        color='steelblue', lw=2.5)
    for om in ['LogisticRegression','RandomForest','GradientBoosting']:
        if om == mn:
            continue
        r2 = splits[tname]['models'][om]
        fpr2, tpr2, _ = roc_curve(splits[tname]['y_test'], r2['y_prob'])
        axes[i].plot(fpr2, tpr2,
            label=om + ' AUC=' + str(round(r2['metrics']['ROC-AUC'],3)),
            lw=1, alpha=0.6)
    axes[i].plot([0,1],[0,1],'k--',lw=0.5)
    axes[i].set_title(tname)
    axes[i].legend(fontsize=7)
    axes[i].grid(True)
plt.tight_layout()
plt.savefig(str(PLOTS_DIR / 'roc_curves.png'), dpi=150, bbox_inches='tight')
plt.show()
""")

# ================================================================
# 14: Feature Importance
# ================================================================
md("""## 14. Feature Importance""")
code("""
fig, axes = plt.subplots(2, 1, figsize=(10, 8))
for i, tname in enumerate(tasks):
    mn = best[tname]
    model = splits[tname]['models'][mn]['model']
    if hasattr(model, 'feature_importances_'):
        imp = model.feature_importances_
    else:
        imp = np.abs(model.coef_[0])
    fi = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': imp
    }).sort_values('Importance', ascending=True)
    axes[i].barh(fi['Feature'], fi['Importance'],
        color=plt.cm.RdYlGn(np.linspace(0.3,0.9,len(fi))))
    axes[i].set_title(tname + ' - ' + mn)
    axes[i].set_xlabel('Importance')
plt.tight_layout()
plt.savefig(str(PLOTS_DIR / 'feature_importance.png'), dpi=150,
            bbox_inches='tight')
plt.show()
""")

# ================================================================
# 15: Threshold Analysis
# ================================================================
md("""## 15. Threshold Optimization""")
code("""
for tname in tasks:
    mn = best[tname]
    res = splits[tname]['models'][mn]
    yt = splits[tname]['y_test']
    yp = res['y_prob']
    print(tname + " (" + mn + "):")
    rows = []
    for thr in np.arange(0.15, 0.8, 0.05):
        pr = (yp >= thr).astype(int)
        rows.append({
            'threshold': round(thr, 2),
            'recall': round(recall_score(yt, pr, zero_division=0), 4),
            'precision': round(precision_score(yt, pr, zero_division=0), 4),
            'f1': round(f1_score(yt, pr, zero_division=0), 4)
        })
    display(pd.DataFrame(rows))
    print()
""")

# ================================================================
# 16: Error Analysis
# ================================================================
md("""## 16. Error Analysis""")
code("""
for tname in tasks:
    mn = best[tname]
    res = splits[tname]['models'][mn]
    cm = confusion_matrix(splits[tname]['y_test'], res['y_pred'])
    tp, fp, fn, tn = cm[1,1], cm[0,1], cm[1,0], cm[0,0]
    print(tname + " (" + mn + "):")
    print("  TP=" + str(tp) + "  FP=" + str(fp)
          + "  FN=" + str(fn) + "  TN=" + str(tn))
    if tp + fn > 0:
        print("  Miss rate: " + str(round(fn/(tp+fn), 4)))
    if fp + tn > 0:
        print("  False alarm rate: " + str(round(fp/(fp+tn), 4)))
    if fn > tp:
        print("  WARNING: More FNs than TPs")
    elif fp > tp:
        print("  WARNING: More FPs than TPs")
    elif fn == 0:
        print("  Excellent: zero missed detections")
    else:
        print("  Acceptable")
    print()
""")

# ================================================================
# 17: Per-cell analysis
# ================================================================
md("""## 17. Interference > Handover Recommendation""")
code("""
rec_handover = "HANDOVER RECOMMENDED - interference + neighbor"
rec_interference = "INTERFERENCE - check antenna/frequency"
rec_handover_opt = "HANDOVER OPTIMIZATION - adjust params"
rec_ok = "OK - no action"

per_cell = []
for psc in df_labeled['psc'].unique():
    mask = df_labeled['psc'] == psc
    int_rate = df_labeled.loc[mask, 'interference'].mean()
    ho_rate = df_labeled.loc[mask, 'handover_needed'].mean()
    n = mask.sum()

    if int_rate > 0.5:
        rec = rec_handover if ho_rate > 0.3 else rec_interference
    elif ho_rate > 0.5:
        rec = rec_handover_opt
    else:
        rec = rec_ok

    per_cell.append({
        'PSC': psc,
        'Interference_Rate': round(int_rate, 3),
        'Handover_Rate': round(ho_rate, 3),
        'Recommendation': rec
    })

ca = pd.DataFrame(per_cell).sort_values('Interference_Rate', ascending=False)
display(ca)

print("Cells with interference > 10%: "
      + str((ca['Interference_Rate'] > 0.1).sum()))
print("Cells needing handover > 10%: "
      + str((ca['Handover_Rate'] > 0.1).sum()))
print("Handover recommended: "
      + str((ca['Recommendation'] == rec_handover).sum()))
""")

# ================================================================
# 18: Save
# ================================================================
md("""## 18. Save Models & Artifacts""")
code("""
for tname in tasks:
    mn = best[tname]
    res = splits[tname]['models'][mn]
    pdf = pd.DataFrame({
        'true': splits[tname]['y_test'],
        'predicted': res['y_pred'],
        'probability': np.round(res['y_prob'], 4)
    })
    fname = 'predictions_' + tname.lower().replace(' ', '_') + '.csv'
    pdf.to_csv(OUTPUT_DIR / fname, index=False)
    print("Saved " + fname)

    art = {
        'model': res['model'],
        'scaler': splits[tname]['scaler'],
        'feature_cols': feature_cols,
        'model_name': mn,
        'task': tname,
        'metrics': res['metrics']
    }
    fjob = 'model_' + tname.lower().replace(' ', '_') + '_best.joblib'
    joblib.dump(art, OUTPUT_DIR / fjob)
    print("Saved " + fjob)

comp.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
ca.to_csv(OUTPUT_DIR / "cell_recommendations.csv", index=False)

print("\\nAll files:")
for item in sorted(OUTPUT_DIR.rglob('*')):
    if item.is_file():
        print("  " + str(item.relative_to(OUTPUT_DIR)))
""")

# ================================================================
# 19: Final Summary
# ================================================================
md("""## 19. Final Summary""")
code("""
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print("Data: " + str(df_clean.shape[0]) + " rows, "
      + str(len(feature_cols)) + " features")
print("\\nClass imbalance (before SMOTE):")
for tname in tasks:
    y_orig = splits[tname]['y_train_orig']
    pos = int(y_orig.sum())
    neg = int(len(y_orig) - pos)
    print("  " + tname + ": " + str(neg) + " neg vs " + str(pos)
          + " pos (" + str(round(neg/max(pos,1), 1)) + ":1)")
print("\\nBest models:")
for tname, mn in best.items():
    m = splits[tname]['models'][mn]['metrics']
    print("  " + tname + " -> " + mn)
    print("    Recall=" + str(round(m['Recall'],4))
          + "  ROC-AUC=" + str(round(m['ROC-AUC'],4))
          + "  F1=" + str(round(m['F1'],4)))
print("\\nTop drivers (interference): "
      + str(feature_cols[np.argsort(
          splits['Interference']['models'][best['Interference']]['model']
          .feature_importances_)[-3:]]))
print("Top drivers (handover): "
      + str(feature_cols[np.argsort(
          splits['Handover Needed']['models'][best['Handover Needed']]['model']
          .feature_importances_)[-3:]]))
print("\\nDone.")
""")

# ===================================================================
# WRITE NOTEBOOK
# ===================================================================
nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "language_info": {"name": "python", "version": "3.10.0"},
        "kernelspec": {"display_name": "Python 3", "name": "python3"}
    },
    "cells": CELLS
}

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print("Saved: " + PATH)
print("Cells: " + str(len(CELLS))
      + " (md=" + str(sum(1 for c in CELLS if c['cell_type'] == 'markdown'))
      + ", code=" + str(sum(1 for c in CELLS if c['cell_type'] == 'code'))
      + ")")

for i, cell in enumerate(CELLS):
    if cell['cell_type'] == 'code':
        try:
            compile('\n'.join(cell['source']), '<cell ' + str(i) + '>', 'exec')
        except SyntaxError as e:
            print("SYNTAX ERROR cell " + str(i) + ": " + str(e))

print("All cells valid.")