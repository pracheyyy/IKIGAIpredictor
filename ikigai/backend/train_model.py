"""
IKIGAI ML Training Script
Generates 2000-row synthetic dataset matching the schema:
Student_ID, Study_Hours_Per_Day, Extracurricular_Hours_Per_Day,
Sleep_Hours_Per_Day, Social_Hours_Per_Day,
Physical_Activity_Hours_Per_Day, GPA, Stress_Level

Trains:
  1. Stress Level Classifier  (Low / Medium / High)
  2. GPA Regressor
Saves models + scaler to /backend/models/
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
import joblib, os, json, warnings
warnings.filterwarnings("ignore")

np.random.seed(42)
N = 2000
os.makedirs("models", exist_ok=True)

# ── 1. GENERATE SYNTHETIC DATA ─────────────────────────────────
def assign_stress(row):
    score = 0
    # Sleep deprivation
    if row["Sleep_Hours_Per_Day"] < 5:   score += 3
    elif row["Sleep_Hours_Per_Day"] < 6: score += 2
    elif row["Sleep_Hours_Per_Day"] > 9: score += 1
    # Overwork
    if row["Study_Hours_Per_Day"] > 9:   score += 3
    elif row["Study_Hours_Per_Day"] > 7: score += 1
    # Physical activity helps
    if row["Physical_Activity_Hours_Per_Day"] < 0.3: score += 2
    elif row["Physical_Activity_Hours_Per_Day"] > 1.5: score -= 1
    # Social balance
    if row["Social_Hours_Per_Day"] < 0.5: score += 1
    elif row["Social_Hours_Per_Day"] > 5:  score += 1
    # Extracurricular overload
    if row["Extracurricular_Hours_Per_Day"] > 4: score += 2
    # GPA pressure proxy (low GPA + high study = burnout)
    if row["GPA"] < 2.5 and row["Study_Hours_Per_Day"] > 6: score += 2

    if score >= 5:   return "High"
    elif score >= 2: return "Medium"
    else:            return "Low"

def compute_gpa(row):
    g = 2.0
    # Study helps up to a point
    study = row["Study_Hours_Per_Day"]
    if 3 <= study <= 7:   g += 1.5
    elif study > 7:        g += 0.8
    elif study < 2:        g -= 0.5
    # Sleep
    sleep = row["Sleep_Hours_Per_Day"]
    if 7 <= sleep <= 8.5: g += 0.5
    elif sleep < 5:        g -= 0.8
    # Physical activity boosts focus
    if row["Physical_Activity_Hours_Per_Day"] >= 1: g += 0.3
    # Social balance
    if 1 <= row["Social_Hours_Per_Day"] <= 3: g += 0.2
    # Noise
    g += np.random.normal(0, 0.3)
    return round(np.clip(g, 1.0, 4.0), 2)

rows = []
for i in range(1, N + 1):
    study   = round(np.random.triangular(1, 4, 12), 1)
    extra   = round(np.random.triangular(0, 1.5, 6),  1)
    sleep   = round(np.random.triangular(3, 7, 11),   1)
    social  = round(np.random.triangular(0, 2, 8),    1)
    phys    = round(np.random.triangular(0, 1, 4),    1)
    row = dict(
        Student_ID=f"S{i:04d}",
        Study_Hours_Per_Day=study,
        Extracurricular_Hours_Per_Day=extra,
        Sleep_Hours_Per_Day=sleep,
        Social_Hours_Per_Day=social,
        Physical_Activity_Hours_Per_Day=phys,
    )
    row["GPA"] = compute_gpa(row)
    row["Stress_Level"] = assign_stress(row)
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv("models/student_habits.csv", index=False)
print("Dataset shape:", df.shape)
print(df["Stress_Level"].value_counts())
print(df.describe())

# ── 2. FEATURE ENGINEERING ────────────────────────────────────
FEATURES = [
    "Study_Hours_Per_Day",
    "Extracurricular_Hours_Per_Day",
    "Sleep_Hours_Per_Day",
    "Social_Hours_Per_Day",
    "Physical_Activity_Hours_Per_Day",
    "GPA",
]

X = df[FEATURES].values
y_stress = df["Stress_Level"].values
y_gpa    = df["GPA"].values

le = LabelEncoder()
y_enc = le.fit_transform(y_stress)   # High=0, Low=1, Medium=2 (alphabetical)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_tr, X_te, ys_tr, ys_te, yg_tr, yg_te = train_test_split(
    X_scaled, y_enc, y_gpa, test_size=0.2, random_state=42, stratify=y_enc
)

# ── 3. STRESS CLASSIFIER ──────────────────────────────────────
print("\n─── Stress Classifier ───")
rf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
rf.fit(X_tr, ys_tr)
pred = rf.predict(X_te)
print(classification_report(ys_te, pred, target_names=le.classes_))

dt = DecisionTreeClassifier(max_depth=6, random_state=42)
dt.fit(X_tr, ys_tr)

lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_tr, ys_tr)

# ── 4. GPA REGRESSOR ──────────────────────────────────────────
print("\n─── GPA Regressor ───")
# Use only non-GPA features for GPA prediction
FEAT_GPA = [
    "Study_Hours_Per_Day",
    "Extracurricular_Hours_Per_Day",
    "Sleep_Hours_Per_Day",
    "Social_Hours_Per_Day",
    "Physical_Activity_Hours_Per_Day",
]
X_gpa = df[FEAT_GPA].values
sc_gpa = StandardScaler()
Xg_sc  = sc_gpa.fit_transform(X_gpa)
Xg_tr, Xg_te, yg_tr2, yg_te2 = train_test_split(Xg_sc, y_gpa, test_size=0.2, random_state=42)

gbr = GradientBoostingRegressor(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42)
gbr.fit(Xg_tr, yg_tr2)
gpa_pred = gbr.predict(Xg_te)
print(f"MAE: {mean_absolute_error(yg_te2, gpa_pred):.3f}  R²: {r2_score(yg_te2, gpa_pred):.3f}")

# ── 5. FEATURE IMPORTANCES ────────────────────────────────────
importances = dict(zip(FEATURES, rf.feature_importances_.tolist()))
print("\nFeature importances:", importances)

# ── 6. SAVE ───────────────────────────────────────────────────
joblib.dump(rf,      "models/stress_rf.pkl")
joblib.dump(dt,      "models/stress_dt.pkl")
joblib.dump(lr,      "models/stress_lr.pkl")
joblib.dump(scaler,  "models/scaler.pkl")
joblib.dump(le,      "models/label_encoder.pkl")
joblib.dump(gbr,     "models/gpa_gbr.pkl")
joblib.dump(sc_gpa,  "models/scaler_gpa.pkl")

meta = {
    "features": FEATURES,
    "gpa_features": FEAT_GPA,
    "stress_classes": le.classes_.tolist(),
    "feature_importances": importances,
    "rf_accuracy": float((rf.predict(X_te) == ys_te).mean()),
    "gpa_mae": float(mean_absolute_error(yg_te2, gpa_pred)),
    "gpa_r2": float(r2_score(yg_te2, gpa_pred)),
}
with open("models/meta.json", "w") as f:
    json.dump(meta, f, indent=2)

print("\n✅ All models saved to models/")
print(f"   RF Accuracy: {meta['rf_accuracy']:.3f}")
print(f"   GPA MAE: {meta['gpa_mae']:.3f}  R²: {meta['gpa_r2']:.3f}")
