# 🌸 IKIGAI – Mental Health & Productivity Correlator

> An AI-powered Mental Health & Productivity Correlator inspired by the Japanese philosophy of **Ikigai (生き甲斐)**. The system helps students understand the relationship between their daily habits, productivity, and well-being through explainable machine learning and behavioral analytics.

## ✨ Features

* 🧠 Behavioral habit tracking
* 📊 Stress & productivity analysis
* 🤖 Ensemble Machine Learning prediction
* ⚖️ Ethical rule-based overrides
* 🌸 Ikigai Balance Score (0–100)
* 💡 Personalized recommendations
* 🔐 User authentication system
* 📈 Explainable scoring methodology

---

## 🏗️ Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask

### Machine Learning

* Scikit-learn
* Random Forest
* Decision Tree
* Logistic Regression

### Data Processing

* Pandas
* NumPy

---

## 📂 Project Structure

```text
IKIGAI/
│
├── backend/
│   ├── app.py
│   ├── train_model.py
│   ├── models/
│   ├── data/
│   └── requirements.txt
│
├── frontend/
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── assets/
│
└── README.md
```

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/IKIGAI-project.git
cd IKIGAI-project
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Train the Models

Run once to generate training data and save machine learning models:

```bash
cd ikigai/backend
python train_model.py
```

### 4️⃣ Start the Flask Server

```bash
python app.py
```

The application will start at:

```text
http://localhost:5000
```

---

## 🧮 How It Works

### Layer 1 – Behavioral Normalization

Daily habits are converted into standardized scores (0–100):

* Sleep Hours
* Study Hours
* Physical Activity
* Social Interaction
* Screen Time

### Layer 2 – Stress & Productivity Analysis

Weighted behavioral scoring calculates:

* Stress Risk Score
* Productivity Score

### Layer 3 – ML Prediction & Ethical Overrides

The system uses an ensemble of:

* Random Forest (60%)
* Decision Tree (25%)
* Logistic Regression (15%)

Rule-based safety checks always override machine learning predictions when necessary.

---

## 🌸 Ikigai Framework

The final Ikigai Score is generated using four pillars:

| Pillar  | Meaning                               |
| ------- | ------------------------------------- |
| Love    | Physical Activity + Social Connection |
| Good At | Study Consistency                     |
| Need    | Recovery & Sleep Balance              |
| Value   | Productivity Output                   |

These pillars are combined to create a holistic balance score ranging from 0–100.

---
## Screenshot
<img width="1731" height="6844" alt="image" src="https://github.com/user-attachments/assets/54354a83-fad9-4e4b-99d9-3aa1a10dcba0" />

<img width="1731" height="3885" alt="image" src="https://github.com/user-attachments/assets/2fe6b28c-fd54-41d1-8bcf-4202abfada2f" />


## ⚠️ Disclaimer

This project is **not a medical diagnostic tool**.

It is intended solely for:

* Awareness
* Self-reflection
* Preventive well-being support

For professional mental health concerns, consult a licensed healthcare provider.

---

## 👩‍💻 Author

**Prachi Patil**

B.Tech Information Technology Student | Open Source Contributor | GSSoC Contributor

---

## 📜 License

This project is licensed under the MIT License.
