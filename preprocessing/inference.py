import joblib
import os
from sklearn.preprocessing import LabelEncoder


svm_model = None
scaler = None
encoder = None

def initialize():
    global svm_model, scaler, encoder
    if svm_model is None:
        svm_model = joblib.load(os.path.join(os.getcwd(), '../model/svm/svm_model.joblib'))
    if scaler is None:
        scaler = joblib.load(os.path.join(os.getcwd(), '../model/svm/scaler.joblib'))
    if encoder is None:
        encoder = LabelEncoder() 

def svm(df):
    initialize()

 
    for col in ('hostname', 'service', 'fault_type'):
        df[col] = encoder.fit_transform(df[col])

    df.drop(columns=['timestamp', 'message', 'matched_patterns', 'is_kernel_related', 'is_failure'], inplace=True)

    
    scaled = scaler.transform(df)
    preds = svm_model.predict(scaled)

  
    failure_ratio = preds.mean()
    if failure_ratio > 0.2:
        print(f"⚠️  Warning: High predicted failure rate ({failure_ratio:.2f})")

    return preds
def test():
    print("hello")
    print("test")