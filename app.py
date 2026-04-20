from flask import Flask, render_template, request, redirect, session
import sqlite3
import pickle

app = Flask(__name__)
app.secret_key = "secret123"

MODEL_EVALUATION = {
    "labels": ["Absence", "Presence"],
    "confusion_matrix": [
        {"actual": "Absence", "predicted_absence": 32, "predicted_presence": 1},
        {"actual": "Presence", "predicted_absence": 8, "predicted_presence": 13},
    ],
    "classification_report": [
        {"label": "Absence", "precision": 0.8000, "recall": 0.9697, "f1_score": 0.8767, "support": 33},
        {"label": "Presence", "precision": 0.9286, "recall": 0.6190, "f1_score": 0.7429, "support": 21},
        {"label": "Accuracy", "precision": 0.8333, "recall": 0.8333, "f1_score": 0.8333, "support": 54},
        {"label": "Macro Avg", "precision": 0.8643, "recall": 0.7944, "f1_score": 0.8098, "support": 54},
        {"label": "Weighted Avg", "precision": 0.8500, "recall": 0.8333, "f1_score": 0.8247, "support": 54},
    ],
    "accuracy": 0.8333,
    "test_size": 54,
    "split_note": "Measured on the same test split used in training with test_size=0.2 and random_state=42.",
}

# Load model
model = pickle.load(open("heart_model.pkl", "rb"))

# Initialize database
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
        conn.commit()

        # DEBUG: print to terminal
        print("User registered:", user)

        conn.close()

        return "Registered Successfully!"

    return render_template("register.html")
# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        result = c.fetchone()
        conn.close()

        if result:
            session['user_id'] = result[0]
            return redirect('/dashboard')
        else:
            return "Invalid username or password"

    return render_template("login.html")

# DASHBOARD
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    result = None
    risk = None

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Handle prediction
    if request.method == 'POST':
        values = [
            float(request.form['Age']),
            float(request.form['Sex']),
            float(request.form['Chest pain type']),
            float(request.form['BP']),
            float(request.form['Cholesterol']),
            float(request.form['FBS over 120']),
            float(request.form['EKG results']),
            float(request.form['Max HR']),
            float(request.form['Exercise angina']),
            float(request.form['ST depression']),
            float(request.form['Slope of ST']),
            float(request.form['Number of vessels fluro']),
            float(request.form['Thallium'])
        ]
         # 🔥 Get probability (VERY IMPORTANT)
        probs = model.predict_proba([values])[0]
        risk = round(probs[1] * 100, 2)  # % chance of disease
        prediction = model.predict([values])[0]

        result = "Heart Disease Detected 💔" if prediction == 1 else "No Heart Disease ❤️"

        # (Optional) Save to DB
        c.execute('''
            CREATE TABLE IF NOT EXISTS heart_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                result TEXT
            )
        ''')

        c.execute('''
            INSERT INTO heart_history (user_id, result)
            VALUES (?, ?)
        ''', (session['user_id'], result))

        conn.commit()

    conn.close()

    return render_template("dashboard.html", result=result, risk=risk)
# @app.route('/dashboard', methods=['GET', 'POST'])
# def dashboard():
#     if 'user_id' not in session:
#         return redirect('/')

#     result = None

#     conn = sqlite3.connect("database.db")
#     c = conn.cursor()

#     # Handle prediction
#     if request.method == 'POST':
#         age = float(request.form['age'])
#         weight = float(request.form['weight'])
#         height = float(request.form['height'])
#         duration = float(request.form['duration'])

#         prediction = model.predict([[age, weight, height, duration]])
#         result = round(prediction[0], 2)

#         # Save to DB
#         c.execute('''
#             INSERT INTO history (user_id, age, weight, height, duration, calories)
#             VALUES (?, ?, ?, ?, ?, ?)
#         ''', (session['user_id'], age, weight, height, duration, result))

#         conn.commit()

#     # Get history
#     c.execute("SELECT calories FROM history WHERE user_id=?", (session['user_id'],))
#     data = c.fetchall()

#     conn.close()

#     calories = [row[0] for row in data]

#     return render_template("dashboard.html", result=result, calories=calories)\


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# PROFILE
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect('/')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    message = None
    error = None

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        c.execute("SELECT password FROM users WHERE id=?", (session['user_id'],))
        current_record = c.fetchone()

        if not current_record or current_record[0] != current_password:
            error = "Your current password is incorrect."
        elif len(new_password) < 6:
            error = "Your new password must be at least 6 characters long."
        elif new_password != confirm_password:
            error = "Your new passwords do not match."
        elif new_password == current_password:
            error = "Choose a new password that is different from the current one."
        else:
            c.execute(
                "UPDATE users SET password=? WHERE id=?",
                (new_password, session['user_id'])
            )
            conn.commit()
            message = "Password updated successfully."

    c.execute('''
        CREATE TABLE IF NOT EXISTS heart_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            result TEXT
        )
    ''')

    c.execute("SELECT username FROM users WHERE id=?", (session['user_id'],))
    user = c.fetchone()

    c.execute("SELECT COUNT(*) FROM heart_history WHERE user_id=?", (session['user_id'],))
    history_count = c.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user=user[0],
        history_count=history_count,
        message=message,
        error=error,
    )

# Guide
@app.route('/guide')
def guide():
    return render_template("guide.html", model_evaluation=MODEL_EVALUATION)

if __name__ == "__main__":
    app.run(debug=True)
