
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load trained model
model = joblib.load(
    os.path.join(BASE_DIR, "best_air_quality_model.pkl")
)

features = joblib.load(
    os.path.join(BASE_DIR, "model_features.pkl")
)

with open(os.path.join(BASE_DIR, "model_info.json")) as f:
    model_info = json.load(f)

model_name = model_info["model_name"]

DB_PATH = os.path.join(BASE_DIR, "predictions.db")


# Create database
def create_database():

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_date TEXT,
            pm25_prediction REAL,
            model_name TEXT
        )
    """)

    conn.commit()
    conn.close()


create_database()


# Home page
@app.route("/")
def home():

    return render_template(
        "index.html",
        features=features,
        model_name=model_name
    )


# Prediction API
@app.route("/api/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid input"}), 400

        # Validate input fields
        missing = [
            feature for feature in features
            if feature not in data or data[feature] in (None, "")
        ]

        if missing:
            return jsonify({
                "error": "Missing input fields",
                "fields": missing
            }), 400

        input_data = {}

        for feature in features:

            value = float(data[feature])

            if not np.isfinite(value):
                return jsonify({
                    "error": f"Invalid value for {feature}"
                }), 400

            input_data[feature] = value

        input_df = pd.DataFrame(
            [input_data],
            columns=features
        )

        prediction = float(model.predict(input_df)[0])

        if not np.isfinite(prediction):
            raise ValueError("Model returned an invalid prediction")

        # Save prediction in database
        conn = sqlite3.connect(DB_PATH)

        conn.execute("""
            INSERT INTO predictions
            (prediction_date, pm25_prediction, model_name)
            VALUES (?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            prediction,
            model_name
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "prediction": round(prediction, 2),
            "unit": "µg/m³",
            "model": model_name,
            "message": "Prediction generated successfully"
        })

    except (ValueError, TypeError) as e:

        return jsonify({"error": str(e)}), 400

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# Dashboard API
@app.route("/api/dashboard")
def dashboard():

    try:

        results_path = os.path.join(
            BASE_DIR,
            "model_comparison.csv"
        )

        results = pd.read_csv(results_path)

        results = results.replace(
            [np.inf, -np.inf], np.nan
        ).fillna(0)

        conn = sqlite3.connect(DB_PATH)

        history = pd.read_sql_query(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT 10",
            conn
        )

        total = pd.read_sql_query(
            "SELECT COUNT(*) AS total FROM predictions",
            conn
        )["total"].iloc[0]

        conn.close()

        return jsonify({
            "model_results": results.to_dict(orient="records"),
            "history": history.to_dict(orient="records"),
            "total_predictions": int(total),
            "best_model": model_name
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
