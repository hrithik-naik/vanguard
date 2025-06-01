import joblib
import threading
import os
from sklearn.preprocessing import LabelEncoder


svm_model = None
scaler = None
encoder = None
rf_model=None

def initialize():
    global svm_model, scaler, encoder,rf_model
    if svm_model is None:
        svm_model = joblib.load(os.path.join(os.getcwd(), '../model/svm/svm_model.joblib'))
    if scaler is None:
        scaler = joblib.load(os.path.join(os.getcwd(), '../model/svm/scaler.joblib'))
    if encoder is None:
        encoder = LabelEncoder()
    if rf_model is None:
        rf_model=joblib.load(os.path.join(os.getcwd(), '../model/randomforest/random_forestscikit1.6.0.joblib'))
    

def svm(df):
    initialize()
    df_original = df.copy()

    for col in ('hostname', 'service', 'fault_type'):
        df[col] = encoder.fit_transform(df[col])

    
    df.drop(columns=['timestamp', 'message', 'matched_patterns', 'is_kernel_related', 'is_failure'], inplace=True)


    

 
    scaled = scaler.transform(df)
    preds = svm_model.predict(scaled)

   
    failure_rows = df_original[preds == 1]

    if not failure_rows.empty:
        print(f"⚠️  Predicted failure on the following rows:\n{failure_rows}")
    else:
        print("✅ No failures predicted.")

    print("Random Forest Model Loaded:", rf_model.__class__)
    failure_ratio = preds.mean()
    if failure_ratio > 0.2:
        print(f"⚠️  Warning: High predicted failure rate ({failure_ratio:.2f})")

    print("Predictions:", preds)


def test():
    print("Hello World")