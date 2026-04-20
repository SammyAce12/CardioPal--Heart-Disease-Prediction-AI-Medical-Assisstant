import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle

# Load dataset
data = pd.read_csv("Heart_Disease_Prediction.csv")

# Convert target to numbers
le = LabelEncoder()
data['Heart Disease'] = le.fit_transform(data['Heart Disease'])
# Presence = 1, Absence = 0

# Features and target
X = data.drop('Heart Disease', axis=1)
y = data['Heart Disease']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy)

# Save model
with open("heart_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model saved as heart_model.pkl")