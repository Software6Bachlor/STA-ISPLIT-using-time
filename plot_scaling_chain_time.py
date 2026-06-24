import os
import glob
import json
import re
import numpy as np
import matplotlib.pyplot as plt

# 1. Configuration
RESULTS_DIR = "./results/scalingChain"
TARGET_MODEL = "chain-sta"  # <--- Dedicated script target

data = {
    "mc": {},       
    "restart": {}   
}

print(f"Scanning for {TARGET_MODEL} data...")

# 2. Parse and Pool the Data
for filepath in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            res = json.load(f)
        except json.JSONDecodeError:
            continue
            
    method = res.get("method")
    model_name = res.get("modelName", "")
    num_trials = res.get("numTrials", 0)
    
    # --- MODEL ISOLATION FILTER ---
    # If the file isn't our target model, skip it entirely
    if TARGET_MODEL not in model_name.lower():
        continue
        
    if method not in data or num_trials == 0:
        continue

    # Extract N exactly for the chain model
    match = re.search(r'[nN](\d+)', model_name)
    if not match:
        continue
    N = int(match.group(1))

    # --- POOLING MONTE CARLO ---
    if method == "mc":
        time = res.get("simElapsedSeconds", 0.0)
        if N not in data["mc"]:
            data["mc"][N] = {"time": 0.0}
        data["mc"][N]["time"] += time

    # --- POOLING RESTART ---
    elif method == "restart":
        time = res.get("simElapsedSeconds", 0.0)
        if N not in data["restart"]:
            data["restart"][N] = {"time": 0.0}
        data["restart"][N]["time"] += time

print("Calculating pooled global variances...")
x_vals = []
for N in sorted(data["mc"].keys()):
    x_vals.append(N)

plt.figure(figsize=(10, 6))

width = 0.4

plt.bar(
    [v - width/2 for v in x_vals], [data["restart"][N]["time"] for N in x_vals],
    color="#ff7f0e", label="RESTART Splitting", width=width
)

plt.bar(
    [v + width/2 for v in x_vals], [data["mc"][N]["time"] for N in x_vals],
    color="#1f77b4", label="Standard Monte Carlo", width=width
)

plt.yscale('log')
plt.xticks(range(1, 22))

plt.xlabel('Chain Length (N)', fontsize=12, fontweight='bold')
plt.ylabel('Elapsed Time (Seconds, Log Scale)', fontsize=12, fontweight='bold')
plt.title(f'Scaling Performance: {TARGET_MODEL.upper()} (Elapsed Time)', fontsize=14, fontweight='bold')

plt.grid(True, which="both", ls="--", alpha=0.4)
plt.legend(loc='upper left') 
plt.tight_layout()

# Save with a specific Chain filename
plt.savefig(f"{TARGET_MODEL}_scaling_simtime_plot.svg")
print(f"Success! Saved plot to '{TARGET_MODEL}_scaling_simtime_plot.svg'")
plt.show()
