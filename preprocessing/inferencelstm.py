# ---------- NOTEBOOK INFERENCE CELL ----------
# inference_notebook.py (paste this cell into the notebook)

import joblib
import tensorflow as tf
from typing import List, Dict
import time

# ---------- Config / tweak here ----------
base_path = os.path.dirname(__file__) 
MANIFEST_PATH = os.path.join(base_path, '../model/svm/pipeline_manifest_reg.joblib') # produced by the training cell
SEP_TOKEN = " <SEP> "

# ---------- Load pipeline ----------
def load_pipeline_notebook(manifest_path=MANIFEST_PATH):
    manifest = joblib.load(manifest_path)
    model_path = manifest["model_path"]
    use_hashing = manifest.get("use_hashing", False)
    context_m = int(manifest.get("context_m", 5))
    k_next = int(manifest.get("k_next", 10))
    model = tf.keras.models.load_model(model_path)
    return {"model": model, "use_hashing": use_hashing, "context_m": context_m, "k_next": k_next}

# ---------- Prepare single input from recent logs ----------
def _prepare_input_from_context_notebook(logs: List[str], context_m: int, sep_token: str = SEP_TOKEN):
    if not isinstance(logs, (list, tuple)):
        raise ValueError("logs must be a list of strings")
    ctx = logs[-context_m:] if len(logs) >= context_m else logs
    ctx = [str(x) for x in ctx]
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
    t0 = time.time()
    pred = model(tf_in, training=False).numpy().ravel()[0]
    latency = time.time() - t0
    return {"predicted_count": float(pred), "k_next": int(k_next), "context_m": int(context_m), "latency_s": latency}

# ---------- Example usage in notebook ----------
print("Loading model from manifest:", MANIFEST_PATH)
pipeline = load_pipeline_notebook(MANIFEST_PATH)
print("Pipeline loaded. model:", pipeline["model"].name, "context_m:", pipeline["context_m"], "k_next:", pipeline["k_next"])

# Provide recent logs as a list (chronological, older -> newer)
CURRENT_CONTEXT = [
     "Out of Memory: Killed process 22608 (httpd).",
        "Out of Memory: Killed process 22747 (httpd).",
        "Out of Memory: Killed process 22759 (httpd).",
        "Out of Memory: Killed process 22613 (httpd).",
        "Out of Memory: Killed process 22766 (httpd).",
        "Out of memory: Kill process simulation - memory exhausted",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4  user=test",
        "authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=211.46.241.200  user=guest",
        "[<02114408>] do_page_fault+0x0/0x446",
        "VM: killing process httpd",
        "Out of Memory: Killed process 1805 (python).",
        "Out of Memory: Killed process 1303 (sendmail).",
        "[<02114408>] do_page_fault+0x0/0x446",
        "Out of Memory: Killed process 5601 (httpd).",
        "[<02114408>] do_page_fault+0x0/0x446",
    
]  # <-- edit this in notebook to try different contexts

res = predict_next_k_notebook(pipeline, CURRENT_CONTEXT)
print("Prediction:", res)