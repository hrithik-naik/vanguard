# inference_notebook.py
import os
import joblib
import time
import tensorflow as tf
from typing import List, Dict

# ---------- Config / tweak here ----------
# determine base_path whether running as script or notebook
try:
    base_path = os.path.dirname(__file__)
    if not base_path:
        base_path = os.getcwd()
except NameError:
    base_path = os.getcwd()

# Use relative paths from this file by default
MANIFEST_PATH = os.path.join(base_path, "../model/svm/pipeline_manifest_reg.joblib")
MODEL_PATH_FALLBACK = os.path.join(base_path, "../model/svm/bilstm_regressor.keras")
SEP_TOKEN = " <SEP> "

def _ensure_file(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}")

# ---------- Load pipeline ----------
def load_pipeline_notebook(manifest_path: str = MANIFEST_PATH) -> dict:
    manifest_path = os.path.abspath(manifest_path)
    _ensure_file(manifest_path)
    manifest = joblib.load(manifest_path)

    # prefer manifest['model_path'] if present, otherwise fallback
    model_path =  os.path.join(base_path, "../model/svm/bilstm_regressor.keras")
    if model_path:
        model_path = os.path.abspath(model_path)
    else:
        model_path = os.path.abspath(MODEL_PATH_FALLBACK)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    use_hashing = bool(manifest.get("use_hashing", False))
    context_m = int(10)
    k_next = int(manifest.get("k_next", 10))

    print(f"Loading Keras model from: {model_path} ...")
    model = tf.keras.models.load_model(model_path)
    print("Model loaded:", model.name)

    return {"model": model, "use_hashing": use_hashing, "context_m": context_m, "k_next": k_next}

# ---------- Prepare single input from recent logs ----------
def _prepare_input_from_context_notebook(logs: List[str], context_m: int, sep_token: str = SEP_TOKEN):
    if not isinstance(logs, (list, tuple)):
        raise ValueError("logs must be a list of strings")
    # Keep chronological order (older -> newer). Take last context_m items.
    ctx = logs[-context_m:] if len(logs) >= context_m else list(logs)
    # Ensure all entries are strings
    ctx = ["" if x is None else str(x) for x in ctx]
    # If not enough entries, left-pad with empty strings so model sees consistent positions
    if len(ctx) < context_m:
        ctx = [""] * (context_m - len(ctx)) + ctx
    joined = sep_token.join(ctx)
    t = tf.constant([joined], dtype=tf.string)   # shape (1,)
    t = tf.reshape(t, [-1, 1])                   # shape (1,1)
    return t

# ---------- Predict next K faults ----------
def predict_next_k_notebook(pipeline: dict, current_logs: List[str]) -> Dict:
    model = pipeline["model"]
    context_m = pipeline["context_m"]
    k_next = pipeline["k_next"]
    tf_in = _prepare_input_from_context_notebook(current_logs, context_m)
    #t0 = time.time()
    pred = model(tf_in, training=False).numpy().ravel()[0]
    #latency = time.time() - t0
    return {"predicted_count": float(pred), "k_next": int(k_next), "context_m": int(context_m)}

# ---------- Make pipeline global (load once) ----------
pipeline = load_pipeline_notebook(MANIFEST_PATH)
print("Pipeline loaded. model:", pipeline["model"].name,
      "context_m:", pipeline["context_m"], "k_next:", pipeline["k_next"])

# ---------- Public helper: run_inference ----------
def run_inference(current_context: List[str]) -> Dict:
    """
    Validate input is List[str], run the global pipeline, print and return the result.
    Raises TypeError if validation fails.
    """
    # Type checks
    # if not isinstance(current_context, list):
    #     raise TypeError(f"Expected list, got {type(current_context).__name__}")
    # if not all(isinstance(x, str) for x in current_context):
    #     raise TypeError("All elements of current_context must be str")

    # print("Input context (len={}):".format(len(current_context)))
    # # Optionally print only last N entries to avoid huge logs
    # print(current_context[-pipeline["context_m"] :])

    result = predict_next_k_notebook(pipeline, current_context)
    print("Prediction:", result)
    return result

# ---------- Example usage ----------
if __name__ == "__main__":
    # Example context (older -> newer)
    CURRENT_CONTEXT = [
        "Out of Memory: Killed process 22608 (httpd).",
        "Out of Memory: Killed process 22747 (httpd).",
        "Out of Memory: Killed process 22759 (httpd).",
        "Out of Memory: Killed process 22613 (httpd).",
        "Out of Memory: Killed process 22766 (httpd)."
    ]

    res = run_inference(CURRENT_CONTEXT)
    print("Returned:", res)
