"""
IKIGAI Flask Backend API
Endpoints:
  POST /api/predict        — full prediction pipeline
  POST /api/auth/register  — user registration
  POST /api/auth/login     — user login
  GET  /api/history/<uid>  — get user history
  GET  /api/stats          — model meta
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib, json, os, hashlib, time, uuid
import numpy as np

app = Flask(__name__, template_folder="../frontend/templates",
            static_folder="../frontend/static")
CORS(app)

BASE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE, "models")

rf     = joblib.load(os.path.join(MODEL_DIR, "stress_rf.pkl"))
dt     = joblib.load(os.path.join(MODEL_DIR, "stress_dt.pkl"))
lr     = joblib.load(os.path.join(MODEL_DIR, "stress_lr.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
le     = joblib.load(os.path.join(MODEL_DIR, "label_encoder.pkl"))
gbr    = joblib.load(os.path.join(MODEL_DIR, "gpa_gbr.pkl"))
sc_gpa = joblib.load(os.path.join(MODEL_DIR, "scaler_gpa.pkl"))

with open(os.path.join(MODEL_DIR, "meta.json")) as f:
    META = json.load(f)

USERS   = {}
HISTORY = {}

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def clamp(v, lo, hi): return max(lo, min(hi, v))

def normalize_sleep(h):
    if h <= 7.5:  return clamp(h / 7.5 * 100, 0, 100)
    else:         return clamp((12 - h) / (12 - 7.5) * 100, 0, 100)

def normalize_study(h):
    if h <= 5:   return clamp(h / 5 * 100, 0, 100)
    elif h <= 8: return clamp((8 - h) / 3 * 60 + 40, 0, 100)
    else:        return clamp(100 - (h - 8) * 12, 0, 100)

def normalize_physical(h):
    if h <= 1.5: return clamp(h / 1.5 * 100, 0, 100)
    else:        return clamp((4 - h) / 2.5 * 100, 0, 100)

def normalize_social(h):
    if h <= 2:   return clamp(h / 2 * 100, 0, 100)
    elif h <= 4: return 100
    else:        return clamp((8 - h) / 4 * 100, 0, 100)

def normalize_extracurricular(h):
    if h <= 2:   return clamp(h / 2 * 100, 0, 100)
    elif h <= 3: return 100
    else:        return clamp((6 - h) / 3 * 70 + 30, 0, 100)

def layer1_normalize(data):
    return {
        "sleep_score":    round(normalize_sleep(data["sleep"]), 1),
        "study_score":    round(normalize_study(data["study"]), 1),
        "physical_score": round(normalize_physical(data["physical"]), 1),
        "social_score":   round(normalize_social(data["social"]), 1),
        "extra_score":    round(normalize_extracurricular(data["extracurricular"]), 1),
    }

def layer2_stress_productivity(scores, data):
    stress_raw = (
        (100 - scores["sleep_score"])    * 0.30 +
        (100 - scores["physical_score"]) * 0.18 +
        (100 - scores["social_score"])   * 0.12 +
        (100 - scores["extra_score"])    * 0.10 +
        clamp(data["study"] * 6, 0, 100) * 0.30
    )
    stress_score = clamp(round(stress_raw, 1), 0, 100)
    productivity = clamp(round(
        scores["study_score"]    * 0.38 +
        scores["physical_score"] * 0.22 +
        scores["sleep_score"]    * 0.25 +
        scores["social_score"]   * 0.15, 1), 0, 100)
    if stress_score >= 60:   stress_level = "High"
    elif stress_score >= 35: stress_level = "Medium"
    else:                    stress_level = "Low"
    return stress_score, stress_level, productivity

def layer3_ml_and_overrides(data, scores, stress_score):
    feat_vec = np.array([[data["study"], data["extracurricular"],
                          data["sleep"], data["social"], data["physical"], data.get("gpa", 3.0)]])
    feat_scaled = scaler.transform(feat_vec)
    rf_proba = rf.predict_proba(feat_scaled)[0]
    dt_proba = dt.predict_proba(feat_scaled)[0]
    lr_proba = lr.predict_proba(feat_scaled)[0]
    ensemble_proba = 0.6 * rf_proba + 0.25 * dt_proba + 0.15 * lr_proba
    ml_idx   = int(np.argmax(ensemble_proba))
    ml_level = le.classes_[ml_idx]
    ml_conf  = round(float(ensemble_proba[ml_idx]) * 100, 1)
    class_proba = {le.classes_[i]: round(float(ensemble_proba[i]) * 100, 1) for i in range(len(le.classes_))}
    override_reason = None
    final_level = ml_level
    if data["sleep"] <= 4:
        final_level = "High"; override_reason = "Sleep ≤ 4 hrs — safety override."
    elif data["sleep"] <= 5 and ml_level == "Low":
        final_level = "Medium"; override_reason = "Sleep ≤ 5 hrs: elevated to Medium."
    elif data["study"] >= 10 and ml_level == "Low":
        final_level = "Medium"; override_reason = "Study ≥ 10 hrs/day — overwork risk."
    elif stress_score >= 70 and ml_level == "Low":
        final_level = "High"; override_reason = "Behavioral score extreme — override to High."
    elif stress_score >= 55 and ml_level == "Low":
        final_level = "Medium"; override_reason = "Score conflict — elevated to Medium."
    return final_level, ml_level, ml_conf, class_proba, override_reason

def compute_ikigai(scores, productivity, stress_score, data):
    love    = clamp(scores["physical_score"] * 0.6 + scores["social_score"] * 0.4, 0, 100)
    good_at = scores["study_score"]
    need    = clamp(scores["sleep_score"] * 0.55 + (100 - stress_score) * 0.45, 0, 100)
    value   = productivity
    ikigai_score = round((love + good_at + need + value) / 4, 1)
    return {"love": round(love,1), "good_at": round(good_at,1),
            "need": round(need,1), "value": round(value,1), "ikigai_score": ikigai_score}

def generate_recommendations(stress_level, ikigai, scores, data):
    recs = []
    if data["sleep"] < 6:
        recs.append({"pillar":"need","icon":"🌙","title":"Urgently Improve Sleep","priority":"high",
            "body":f"You're sleeping only {data['sleep']} hrs. Aim for 7–8 hrs. Set a consistent bedtime, avoid screens 30 min before sleep."})
    elif data["sleep"] < 7:
        recs.append({"pillar":"need","icon":"🌙","title":"Improve Sleep Quality","priority":"medium",
            "body":f"Increase sleep to 7–8 hrs from {data['sleep']} hrs. Even 30 extra minutes can significantly reduce stress."})
    if data["study"] > 9:
        recs.append({"pillar":"good_at","icon":"📚","title":"Reduce Study Overload","priority":"high",
            "body":f"Studying {data['study']} hrs/day risks burnout. Use Pomodoro (25/5 min). Aim for focused 5–7 hr sessions."})
    elif data["study"] < 2:
        recs.append({"pillar":"good_at","icon":"📚","title":"Increase Study Consistency","priority":"medium",
            "body":f"Only {data['study']} hrs study may impact performance. Build a routine: 3–5 focused hours daily."})
    if data["physical"] < 0.5:
        recs.append({"pillar":"love","icon":"🏃","title":"Add Daily Movement","priority":"high",
            "body":"Even a 20-minute walk daily reduces cortisol and improves focus. Start small — stairs, a walk between classes."})
    elif data["physical"] < 1:
        recs.append({"pillar":"love","icon":"🏃","title":"Increase Physical Activity","priority":"medium",
            "body":f"{data['physical']} hrs is below optimal. Aim for 1–1.5 hrs. Try yoga, gym, or a brisk walk."})
    if data["social"] < 0.5:
        recs.append({"pillar":"love","icon":"🤝","title":"Reconnect Socially","priority":"medium",
            "body":"Social isolation amplifies stress. Schedule ≥1 hr of meaningful social interaction daily."})
    elif data["social"] > 5:
        recs.append({"pillar":"value","icon":"⏱️","title":"Rebalance Social Time","priority":"low",
            "body":f"{data['social']} hrs of social time may crowd out rest. Aim for 1.5–3 hrs for a sustainable balance."})
    if data["extracurricular"] > 4:
        recs.append({"pillar":"value","icon":"🎯","title":"Simplify Commitments","priority":"medium",
            "body":f"{data['extracurricular']} hrs extracurriculars is high. Focus on 1–2 meaningful activities."})
    if stress_level == "High":
        recs.insert(0, {"pillar":"need","icon":"⚠️","title":"High Stress — Act Now","priority":"high",
            "body":"Your pattern indicates high burnout risk. Prioritise sleep, reduce obligations, and speak with a counselor if needed."})
    weakest = min([("love", ikigai["love"]),("good_at", ikigai["good_at"]),
                   ("need", ikigai["need"]),("value", ikigai["value"])], key=lambda x: x[1])
    padvice = {
        "love":    ("💚 Boost Your Love Pillar","Physical activity + social connection scores are low. Schedule one enjoyable physical activity per week."),
        "good_at": ("📖 Strengthen Good At Pillar","Study consistency needs work. Try time-blocking with clear daily goals."),
        "need":    ("😴 Restore Your Need Pillar","Prioritise sleep and protect rest time — recovery is not optional."),
        "value":   ("🚀 Elevate Your Value Pillar","Set 3 small achievable goals each morning. Track completion to build momentum."),
    }
    if weakest[1] < 50:
        t, b = padvice[weakest[0]]
        recs.append({"pillar":weakest[0],"icon":t.split()[0],"title":t[2:],"body":b,"priority":"medium"})
    if ikigai["ikigai_score"] >= 70:
        recs.append({"pillar":"ikigai","icon":"🌸","title":"Maintain Your Balance","priority":"low",
            "body":"Excellent Ikigai balance! Journal what's working to build lasting resilience."})
    order = {"high":0,"medium":1,"low":2}
    recs.sort(key=lambda r: order.get(r.get("priority","low"),2))
    return recs[:6]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.json or {}
    name  = d.get("name","").strip()
    email = d.get("email","").strip().lower()
    pw    = d.get("password","")
    if not name or not email or not pw:
        return jsonify({"error":"All fields required."}), 400
    if "@" not in email:
        return jsonify({"error":"Invalid email."}), 400
    if len(pw) < 6:
        return jsonify({"error":"Password must be ≥ 6 characters."}), 400
    if email in USERS:
        return jsonify({"error":"Account already exists."}), 409
    uid = str(uuid.uuid4())[:8]
    USERS[email] = {"id":uid,"name":name,"email":email,"password_hash":hash_pw(pw),"created_at":time.time()}
    HISTORY[uid] = []
    return jsonify({"message":"Account created.","user":{"id":uid,"name":name,"email":email}}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.json or {}
    email = d.get("email","").strip().lower()
    pw    = d.get("password","")
    user  = USERS.get(email)
    if not user or user["password_hash"] != hash_pw(pw):
        return jsonify({"error":"Invalid credentials."}), 401
    return jsonify({"message":"Login successful.",
                    "user":{"id":user["id"],"name":user["name"],"email":user["email"]}}), 200

@app.route("/api/predict", methods=["POST"])
def predict():
    d = request.json or {}
    try:
        data = {
            "sleep":           float(d["sleep"]),
            "study":           float(d["study"]),
            "extracurricular": float(d.get("extracurricular", 1.5)),
            "social":          float(d.get("social", 2.0)),
            "physical":        float(d["physical"]),
            "gpa":             float(d.get("gpa", 3.0)),
        }
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    scores                         = layer1_normalize(data)
    stress_score, _, productivity  = layer2_stress_productivity(scores, data)
    final_level, ml_level, ml_conf, class_proba, override = layer3_ml_and_overrides(data, scores, stress_score)
    ikigai                         = compute_ikigai(scores, productivity, stress_score, data)
    recommendations                = generate_recommendations(final_level, ikigai, scores, data)
    gpa_feat = np.array([[data["study"], data["extracurricular"],
                          data["sleep"], data["social"], data["physical"]]])
    gpa_pred = round(float(gbr.predict(sc_gpa.transform(gpa_feat))[0]), 2)
    gpa_pred = clamp(gpa_pred, 1.0, 4.0)
    result = {
        "input": data, "layer1_scores": scores,
        "layer2": {"stress_score": stress_score, "productivity": productivity},
        "layer3": {"final_stress_level": final_level, "ml_stress_level": ml_level,
                   "ml_confidence": ml_conf, "class_probabilities": class_proba,
                   "override_applied": override is not None, "override_reason": override},
        "ikigai": ikigai, "gpa_prediction": gpa_pred,
        "recommendations": recommendations, "timestamp": time.time(),
    }
    uid = d.get("user_id")
    if uid and uid in HISTORY:
        HISTORY[uid].append(result)
    return jsonify(result), 200

@app.route("/api/history/<uid>", methods=["GET"])
def history(uid):
    entries = HISTORY.get(uid, [])
    return jsonify({"entries": entries, "count": len(entries)}), 200

@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(META), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
