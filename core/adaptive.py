# =============================
# ADAPTIVE STATE (GLOBAL)
# =============================
adaptive_state = {
    "score_threshold": 0.8,
    "ml_threshold": 0.65,
    "rr_threshold": 1.8,
    "of_threshold": 0.2
}

# =============================
# CLAMP UTILITY (SAFETY)
# =============================
def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

# =============================
# MAIN ADAPTIVE LOGIC
# =============================
def adjust_parameters(regime, equity_curve):

    global adaptive_state

    # =============================
    # DEFAULT BASELINE RESET
    # (prevents drift over time)
    # =============================
    base = {
        "score_threshold": 0.8,
        "ml_threshold": 0.65,
        "rr_threshold": 1.8,
        "of_threshold": 0.2
    }

    adaptive_state.update(base)

    # =============================
    # PERFORMANCE ANALYSIS
    # =============================
    if len(equity_curve) >= 5:
        recent = equity_curve[-5:]
        performance = recent[-1] - recent[0]
    else:
        performance = 0

    # =============================
    # REGIME-BASED ADAPTATION
    # =============================
    if regime == "TRENDING":
        adaptive_state["score_threshold"] -= 0.05
        adaptive_state["ml_threshold"] -= 0.05
        adaptive_state["rr_threshold"] += 0.2

    elif regime == "RANGING":
        adaptive_state["score_threshold"] += 0.05
        adaptive_state["ml_threshold"] += 0.05
        adaptive_state["rr_threshold"] -= 0.2

    elif regime == "LOW_VOL":
        adaptive_state["score_threshold"] += 0.1
        adaptive_state["ml_threshold"] += 0.1
        adaptive_state["of_threshold"] += 0.1

    # =============================
    # PERFORMANCE FEEDBACK
    # =============================
    if performance < 0:
        # system is losing → become conservative
        adaptive_state["score_threshold"] += 0.05
        adaptive_state["ml_threshold"] += 0.05
        adaptive_state["of_threshold"] += 0.05

    elif performance > 0:
        # system is winning → allow slight flexibility
        adaptive_state["score_threshold"] -= 0.02

    # =============================
    # SAFETY CLAMPS (CRITICAL)
    # =============================
    adaptive_state["score_threshold"] = clamp(adaptive_state["score_threshold"], 0.7, 0.95)
    adaptive_state["ml_threshold"] = clamp(adaptive_state["ml_threshold"], 0.55, 0.85)
    adaptive_state["rr_threshold"] = clamp(adaptive_state["rr_threshold"], 1.2, 2.5)
    adaptive_state["of_threshold"] = clamp(adaptive_state["of_threshold"], 0.1, 0.5)

    return adaptive_state

# =============================
# RL ACTION ADJUSTMENT
# =============================
def apply_rl_action(params, action):

    params = params.copy()

    # =============================
    # RL ACTIONS
    # =============================
    if action == 0:
        # CONSERVATIVE
        params["score_threshold"] += 0.05
        params["ml_threshold"] += 0.05
        params["of_threshold"] += 0.05

    elif action == 1:
        # NEUTRAL
        pass

    elif action == 2:
        # AGGRESSIVE
        params["score_threshold"] -= 0.05
        params["ml_threshold"] -= 0.05
        params["rr_threshold"] += 0.1

    # =============================
    # FINAL SAFETY CLAMP
    # =============================
    params["score_threshold"] = clamp(params["score_threshold"], 0.7, 0.95)
    params["ml_threshold"] = clamp(params["ml_threshold"], 0.55, 0.85)
    params["rr_threshold"] = clamp(params["rr_threshold"], 1.2, 2.5)
    params["of_threshold"] = clamp(params["of_threshold"], 0.1, 0.5)

    return params