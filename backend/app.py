import nltk
import os
import sqlite3
import joblib
import numpy as np

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from nltk.stem import WordNetLemmatizer
from werkzeug.utils import secure_filename

from pipeline import process_receipt

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Download NLTK data if not already present
try:
    nltk.data.find('corpora/wordnet')
    nltk.data.find('corpora/omw-1.4') # Ensure omw-1.4 is also checked/downloaded
except LookupError: # Corrected exception type
    print("NLTK resource 'wordnet' or 'omw-1.4' not found. Downloading...")
    nltk.download('wordnet')
    nltk.download('omw-1.4') # Download omw-1.4 as well
    print("NLTK resources downloaded successfully.")

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import joblib 
import numpy as np
from nltk.stem import WordNetLemmatizer
import sqlite3
import os

app = Flask(__name__)
cors = CORS(app) 
app.config['CORS_HEADERS'] = 'Content-Type'

# Database file
DB_FILE = 'database.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    type TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Preprocessing function
def preprocess_text(text):
    return ' '.join([lemmatizer.lemmatize(word) for word in text.lower().split()])

# Load the trained model and vectorizer
model = None
vectorizer = None
CATEGORIES = [] 
TYPES_MAP = {} 

try:
    model = joblib.load('expense_categorization_model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')

    CATEGORIES = list(model.classes_)
    print(f"Loaded Model Categories (from model.classes_): {CATEGORIES}")

    TYPES_MAP = {
        'Food': 'Expense',
        'Shopping': 'Expense',
        'Travel': 'Expense',
        'Entertainment': 'Expense',
        'Health': 'Expense',
        'Utilities': 'Expense',
        'Education': 'Expense',
        'Housing': 'Expense',
        'Insurance': 'Expense',
        'Income': 'Savings'
    }

    TYPES = [TYPES_MAP.get(cat, 'Expense') for cat in CATEGORIES]

    print(f"Mapped Types: {TYPES}")
    print("✅ Model and vectorizer loaded successfully.")

except FileNotFoundError:
    print("❌ Error: expense_categorization_model.pkl or vectorizer.pkl not found.")
except Exception as e:
    print(f"❌ Error loading model or vectorizer: {e}")

def predict_transaction_details(description):
    if model is None or vectorizer is None or not CATEGORIES:
        print("Prediction skipped: Model, vectorizer, or categories not loaded.")
        return "Unknown", "Unknown"
    preprocessed_desc = preprocess_text(description)
    desc_vectorized = vectorizer.transform([preprocessed_desc])
    predicted_category = model.predict(desc_vectorized)[0] 
    predicted_type = TYPES_MAP.get(predicted_category, 'Unknown') 
    return predicted_category, predicted_type

@app.route('/predict_category', methods=['POST'])
@cross_origin()
def predict_category_route():
    data = request.json
    description = data.get('description', '')
    if not description:
        return jsonify({"error": "Description is required"}), 400
    predicted_category, predicted_type = predict_transaction_details(description)
    return jsonify({
        "status": "success",
        "description": description,
        "predicted_category": predicted_category,
        "predicted_type": predicted_type
    })

@app.route('/api/add_transaction', methods=['POST'])
@cross_origin()
def add_transaction():
    data = request.json
    username = data.get('username')
    amount = data.get('amount')
    description = data.get('description')
    if not all([username, amount, description]):
        return jsonify({"status": "error", "message": "Missing transaction data"}), 400
    predicted_category, predicted_type = predict_transaction_details(description)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO transactions (username, amount, description, category, type) VALUES (?, ?, ?, ?, ?)',
              (username, amount, description, predicted_category, predicted_type))
    conn.commit()
    conn.close()
    
    print(f"Adding transaction for {username}: Amount={amount}, Description='{description}', Category={predicted_category}, Type={predicted_type}")
    return jsonify({
        "status": "success",
        "message": "Transaction added successfully.",
        "username": username,
        "amount": amount,
        "description": description,
        "predicted_category": predicted_category,
        "predicted_type": predicted_type
    })

@app.route('/api/get_transactions/<username>', methods=['GET'])
@cross_origin()
def get_transactions(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT amount, description, category, type FROM transactions WHERE username = ?', (username,))
    rows = c.fetchall()
    conn.close()
    transactions = [{"amount": row[0], "description": row[1], "category": row[2], "type": row[3]} for row in rows]
    print(f"Retrieving transactions for {username}: {transactions}")
    return jsonify({"status": "success", "username": username, "transactions": transactions})

@app.route("/api/upload_receipt", methods=["POST"])
@cross_origin()
def upload_receipt():

    if "receipt" not in request.files:
        return jsonify({"error": "Receipt image not found"}), 400

    file = request.files["receipt"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    receipt = process_receipt(filepath)

    if receipt.get("success") is False:
        return jsonify(receipt), 500

    description = receipt.get("description", "")

    category, transaction_type = predict_transaction_details(description)

    receipt["predicted_category"] = category
    receipt["predicted_type"] = transaction_type

    return jsonify(receipt)

if __name__ == '__main__':
    app.run(debug=True)