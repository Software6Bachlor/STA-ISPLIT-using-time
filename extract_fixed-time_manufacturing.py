import os
import glob
import json
import numpy as np

# --- CONFIGURATION ---
RESULTS_DIR = "./results/FixedTimeManu/FixedTimeManu"
GROUND_TRUTH =  4.896705e-03  # <--- Update this with your true phi for the manufacturing model

data = {
    "mc": {"trials": 0, "hits": 0, "p_estimates": [], "run_amount": 0},
    "restart": {"trials": 0, "Y_list": [], "p_estimates": [], "run_amount": 0}
}

print("Scanning for FIXED TIME manufacturing experiments...")

# 1. Parse files and pool data
for filepath in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
    filename = os.path.basename(filepath)
    
    # Identify method by filename
    if "fixed_time_manufacturing_mc" in filename:
        method = "mc"
    elif "fixed_time_manufacturing_restart" in filename:
        method = "restart"
    else:
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            res = json.load(f)
        except json.JSONDecodeError:
            continue

    num_trials = res.get("numTrials", 0)
    p_est = res.get("probabilityEstimate", 0.0)
    
    if num_trials == 0:
        continue

    # Record individual file stats
    data[method]["run_amount"] += 1
    data[method]["p_estimates"].append(p_est)

    # Pool MC data
    if method == "mc":
        data["mc"]["hits"] += res.get("numHits", 0)
        data["mc"]["trials"] += num_trials

    # Pool RESTART data
    elif method == "restart":
        raw_list = res.get("weightedHitsList") or []
        zeros_to_add = num_trials - len(raw_list)
        if zeros_to_add > 0:
            raw_list.extend([0.0] * zeros_to_add)
            
        data["restart"]["Y_list"].extend(raw_list)
        data["restart"]["trials"] += num_trials

# 2. Calculate Final Metrics
output_json = {}

# --- MC Calculations ---
if data["mc"]["trials"] > 0:
    mc_M = data["mc"]["trials"]
    mc_p_hat = data["mc"]["hits"] / mc_M
    mc_var = mc_p_hat * (1 - mc_p_hat)
    mc_hw = 1.96 * np.sqrt(mc_var / mc_M)
    
    output_json["mc"] = {
        "estimated_probability_average": mc_p_hat,
        "p_min": min(data["mc"]["p_estimates"]),
        "p_max": max(data["mc"]["p_estimates"]),
        "ci_half_width": mc_hw,
        "contains_zero_0?": bool((mc_p_hat - mc_hw) <= 0.0),
        "phi_indicator_?": bool((mc_p_hat - mc_hw) <= GROUND_TRUTH <= (mc_p_hat + mc_hw)),
        "run_amount": data["mc"]["run_amount"],
        "total_pooled_trials": mc_M
    }

# --- RESTART Calculations ---
if data["restart"]["trials"] > 0:
    res_M = data["restart"]["trials"]
    Y_mega = np.array(data["restart"]["Y_list"])
    res_p_hat = np.sum(Y_mega) / res_M
    res_var = np.var(Y_mega, ddof=1) if res_M > 1 else 0
    res_hw = 1.96 * np.sqrt(res_var / res_M)
    
    output_json["restart"] = {
        "estimated_probability_average": res_p_hat,
        "p_min": min(data["restart"]["p_estimates"]),
        "p_max": max(data["restart"]["p_estimates"]),
        "ci_half_width": res_hw,
        "contains_zero_0?": bool((res_p_hat - res_hw) <= 0.0),
        "phi_indicator_?": bool((res_p_hat - res_hw) <= GROUND_TRUTH <= (res_p_hat + res_hw)),
        "run_amount": data["restart"]["run_amount"],
        "total_pooled_trials": res_M
    }

# 3. Write to JSON file
output_filename = "extracted_fixed_time_manufacturing.json"
with open(output_filename, "w", encoding='utf-8') as out_file:
    json.dump(output_json, out_file, indent=4)

print(f"Done. Data extracted to {output_filename}")