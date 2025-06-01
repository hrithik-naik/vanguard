import joblib
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from collections import Counter

# Globals for models and mappings
svm_model = None
scaler = None
encoder = LabelEncoder()
rf_model = None
feature_map = None
label_mapping = None

def initialize():
    global svm_model, scaler, encoder, rf_model, feature_map, label_mapping

    base_path = os.path.dirname(__file__)  # Safer than os.getcwd()

    if svm_model is None:
        svm_model = joblib.load(os.path.join(base_path, '../model/svm/svm_model.joblib'))
    if scaler is None:
        scaler = joblib.load(os.path.join(base_path, '../model/svm/scaler.joblib'))
    if rf_model is None:
        rf_model = joblib.load(os.path.join(base_path, '../model/randomforest/random_forest_fault_detector.pkl'))
    if feature_map is None:
        feature_map = joblib.load(os.path.join(base_path, '../model/randomforest/feature_names.pkl'))
    if label_mapping is None:
        label_mapping = joblib.load(os.path.join(base_path, '../model/randomforest/label_mapping.pkl'))
def preprocess_batch_records(df: pd.DataFrame) -> pd.DataFrame:
    

  
    try:
        df['matched_patterns'] = df['matched_patterns'].fillna('none')

   
        pattern_dummies = df['matched_patterns'].str.get_dummies(sep='|')
        df = pd.concat([df, pattern_dummies], axis=1)
        df.drop(columns=['timestamp', 'hostname', 'service', 'message', 'matched_patterns'], inplace=True)

    except KeyError as e:
        print(f"⚠️ Warning: Tried to drop missing columns. Details: {e}")
        drop_cols = ['timestamp', 'hostname', 'service', 'message', 'matched_patterns']
        df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)

 
    for col in feature_map:
        if col not in df.columns:
            df[col] = 0

   
    df = df[feature_map]

    return df




def predict_batch(log_records_df: pd.DataFrame):
    initialize()
    processed = preprocess_batch_records(log_records_df)
    pred_codes = rf_model.predict(processed)
    pred_labels = [label_mapping[code] for code in pred_codes]

    most_common = Counter(pred_labels).most_common(1)
    if most_common:
        label, count = most_common[0]
        display_label = "normal" if label.lower() == "other" else label
        print(f"Most frequent predicted fault type: {display_label} ({count} occurrences)")
    else:
        print("No predictions were made.")



def svm(df):
    initialize()
    df_original = df.copy()
    for col in ('hostname', 'service', 'fault_type'):
        df[col] = encoder.fit_transform(df[col])  # Warning: Fitting on inference data is incorrect for production

    df.drop(columns=['timestamp', 'message', 'matched_patterns', 'is_kernel_related', 'is_failure'], inplace=True)
    scaled = scaler.transform(df)
    preds = svm_model.predict(scaled)

    failure_rows = df_original[preds == 1]
    if not failure_rows.empty:
        print(f"⚠️  Predicted failure on the following rows:\n{failure_rows}")
    failure_ratio = preds.mean()
    if failure_ratio > 0.2:
        print(f"⚠️  Warning: High predicted failure rate ({failure_ratio:.2f})")
    print("Predictions:", preds)
