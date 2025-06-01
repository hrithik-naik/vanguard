def preprocess_batch_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess a batch of log records for inference.
    Args:
        df: A pandas DataFrame representing multiple log entries.
    Returns:
        A DataFrame with the preprocessed features.
    """
    df = df.copy()

    # Fill NA in 'matched_patterns'
    df['matched_patterns'] = df['matched_patterns'].fillna('none')

    # One-hot encode matched_patterns
    pattern_dummies = df['matched_patterns'].str.get_dummies(sep='|')
    df = pd.concat([df, pattern_dummies], axis=1)

    # Drop unused columns
    df.drop(columns=['timestamp', 'hostname', 'service', 'message', 'matched_patterns'], inplace=True)

    # Ensure all features from training are present
    for col in feature_names:
        if col not in df.columns:
            df[col] = 0

    # Ensure correct column order
    df = df[feature_names]

    return df


def predict_batch(log_records_df: pd.DataFrame) -> pd.Series:
    """
    Predict fault types for a batch of log records.
    Args:
        log_records_df: DataFrame with raw log records (same schema as training).
    Returns:
        A pandas Series of predicted fault type labels.
    """
    processed = preprocess_batch_records(log_records_df)
    pred_codes = model.predict(processed)
    pred_labels = [label_mapping[code] for code in pred_codes]
    return pd.Series(pred_labels, name="predicted_fault_type")
