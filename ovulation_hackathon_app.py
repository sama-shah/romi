import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta
import json

st.set_page_config(page_title="Romi Cycle Visualization", layout="wide")
st.title("Romi Cycle Visualization")

# ---------------- Helpers ----------------
def extract_trend_first(df: pd.DataFrame, smooth_win: int = 5) -> pd.Series:
    lc_map = {c.lower().strip(): c for c in df.columns}
    # 1) Preferred: temperature_trend_deviation
    for key in ["temperature_trend_deviation", "temp_trend_deviation", "temp_trend"]:
        if key in lc_map:
            return pd.to_numeric(df[lc_map[key]], errors="coerce")
    for lc_name, orig in lc_map.items():
        if "temperature_trend_deviation" in lc_name or "temp_trend_deviation" in lc_name:
            return pd.to_numeric(df[orig], errors="coerce")
    # 2) Readiness JSON blob with contributors.temperature_trend_deviation
    for rc in [c for c in df.columns if c.lower().strip() in ["readiness", "readiness_json", "readiness_data"]]:
        try:
            if isinstance(df[rc].iloc[0], dict):
                series = df[rc].apply(lambda x: x.get("contributors", {}).get("temperature_trend_deviation", np.nan) if isinstance(x, dict) else np.nan)
                if series.notna().sum() > 0:
                    return pd.to_numeric(series, errors="coerce")
            else:
                parsed = df[rc].apply(lambda s: json.loads(s) if isinstance(s, str) and s.strip().startswith("{") else {})
                series = parsed.apply(lambda x: x.get("contributors", {}).get("temperature_trend_deviation", np.nan) if isinstance(x, dict) else np.nan)
                if series.notna().sum() > 0:
                    return pd.to_numeric(series, errors="coerce")
        except Exception:
            pass
    # 3) Fallback to temperature_deviation (smoothed)
    for key in ["temperature_deviation", "temp_deviation"]:
        if key in lc_map:
            s = pd.to_numeric(df[lc_map[key]], errors="coerce")
            return s.rolling(smooth_win, min_periods=1, center=True).mean()
    for lc_name, orig in lc_map.items():
        if "temperature_deviation" in lc_name:
            s = pd.to_numeric(df[orig], errors="coerce")
            return s.rolling(smooth_win, min_periods=1, center=True).mean()
    # 4) Last resort: raw temperature columns → deviation vs 7d median baseline
    for key in ["skin_temp", "skin_temperature", "body_temp", "body_temperature", "temperature", "temperature_c", "temp_c"]:
        if key in lc_map:
            s = pd.to_numeric(df[lc_map[key]], errors="coerce")
            base = s.rolling(7, min_periods=3).median()
            return s - base
    for lc_name, orig in lc_map.items():
        if any(k in lc_name for k in ["skin_temp","skin_temperature","body_temp","body_temperature","temperature"]):
            s = pd.to_numeric(df[orig], errors="coerce")
            base = s.rolling(7, min_periods=3).median()
            return s - base
    return pd.Series([np.nan] * len(df))

def prepare_df(raw: pd.DataFrame) -> pd.DataFrame:
    # Find date column
    date_col = None
    for c in raw.columns:
        if c.lower().strip() in ["date","summary_date","day"] or "date" in c.lower():
            date_col = c
            break
    if date_col is None:
        raise ValueError("CSV must include a date-like column (date/summary_date/day).")
    df = raw.rename(columns={date_col: "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    temp = extract_trend_first(df, smooth_win=5)
    temp = pd.to_numeric(temp, errors="coerce").replace([np.inf, -np.inf], np.nan).interpolate(limit_direction="both")
    df["temp_signal_c"] = temp

    if df["temp_signal_c"].notna().sum() == 0:
        raise ValueError("No usable temperature signal found (trend/deviation/raw). Check your column names.")

    # Optional helpers
    for opt, cands in {
        "rhr": ["resting_heart_rate","rhr","average_resting_heart_rate"],
        "hrv": ["hrv","rmssd"],
    }.items():
        for c in raw.columns:
            if c.lower().strip() in cands:
                df = df.rename(columns={c: opt})
                df[opt] = pd.to_numeric(df[opt], errors="coerce").interpolate(limit_direction="both")
                break
    return df

def find_nadir_then_rise(sig_c, idx, rise_min=0.25, rise_days=3):
    n = len(sig_c)
    if idx + rise_days >= n:
        return False, None, 0.0
    base = sig_c.iloc[idx]
    window = sig_c.iloc[idx+1: idx+1+rise_days]
    cond = (window - base) >= rise_min
    if cond.all():
        return True, idx+1, float((window - base).mean())
    return False, None, float((window - base).clip(lower=0).mean())

# -------- Strong detector (nadir + sustained rise) --------
def detect_ovulation_candidates(df: pd.DataFrame, rise_min=0.25, rise_days=3, search_start=None, search_end=None):
    sig_c = df["temp_signal_c"].reset_index(drop=True)
    dates = pd.Series(df["date"]).reset_index(drop=True)
    candidates = []
    for i in range(1, len(sig_c)-1):
        d_i = dates[i].date()
        if search_start is not None and d_i < search_start:
            continue
        if search_end is not None and d_i > search_end:
            continue
        if pd.isna(sig_c.iloc[i-1]) or pd.isna(sig_c.iloc[i]) or pd.isna(sig_c.iloc[i+1]):
            continue
        if sig_c.iloc[i] < sig_c.iloc[i-1] and sig_c.iloc[i] < sig_c.iloc[i+1]:
            ok, rise_idx, mean_rise = find_nadir_then_rise(sig_c, i, rise_min, rise_days)
            if ok:
                candidates.append({
                    "ovulation_date": dates[rise_idx].date(),
                    "nadir_date": dates[i].date(),
                    "rise_mean_c": float(mean_rise),
                    "confidence": "high" if mean_rise >= 0.30 and rise_days >= 3 else "medium",
                })
    return candidates

# -------- Fallback: pick best-scoring day even if below threshold --------
def pick_best_fallback(df: pd.DataFrame, win_start, win_end, rise_days=3):
    seg = df[df["date"].between(pd.to_datetime(win_start), pd.to_datetime(win_end))].copy()
    seg = seg.sort_values("date").reset_index(drop=True)
    if len(seg) < rise_days + 2:
        return None, None, None
    best = None
    for i in range(1, len(seg) - rise_days):
        s_i = seg.loc[i, "temp_signal_c"]
        if pd.isna(s_i): continue
        window = seg.loc[i+1:i+rise_days, "temp_signal_c"]
        if window.isna().any(): continue
        score = float((window - s_i).mean())
        # small bonus if local nadir
        if i > 0 and i < len(seg)-1:
            if s_i < seg.loc[i-1, "temp_signal_c"] and s_i < seg.loc[i+1, "temp_signal_c"]:
                score += 0.05
        if best is None or score > best["score"]:
            best = {"ovulation_date": seg.loc[i+1, "date"].date(), "score": score, "nadir_date": seg.loc[i, "date"].date()}
    if best is None:
        return None, None, None
    return best["ovulation_date"], best["score"], best["nadir_date"]

def choose_best_candidate(cands):
    if not cands:
        return None
    return max(cands, key=lambda c: c["rise_mean_c"])

def infer_menses_starts(df, min_cycle_len=21, max_cycle_len=45):
    temp = df["temp_signal_c"]
    mean = temp.rolling(7, min_periods=3).median()
    dips = (temp < (mean - 0.05)) & (temp.diff() < -0.1)
    dates = df["date"].dt.date
    starts, prev = [], None
    for i, is_dip in enumerate(dips):
        if not is_dip:
            continue
        d = dates.iloc[i]
        if prev and (d - prev).days < min_cycle_len:
            continue
        starts.append(d)
        prev = d
    return starts

# -------- NEW: guarantee one ovulation window per cycle (with fallback) --------
def label_phases(df,
                 menses_starts,
                 rise_min=0.25,
                 rise_days=3,
                 search_days=(8, 24),
                 window_half_width=1,
                 force_one_window_per_cycle=True):
    out = df.copy()
    out["phase"] = "unlabeled"
    out["ovulation_estimate"] = pd.NaT
    out["ovulation_confidence"] = pd.Series([None]*len(out), dtype="object")

    if not menses_starts:
        # No cycle boundaries → treat as one cycle
        start = out["date"].min().date()
        end = out["date"].max().date()
        win_start = start + timedelta(days=search_days[0])
        win_end = min(end, start + timedelta(days=search_days[1]))
        cands = detect_ovulation_candidates(out, rise_min, rise_days, win_start, win_end)
        if cands:
            best = max(cands, key=lambda c: c["rise_mean_c"])
            ovu = best["ovulation_date"]; conf = best["confidence"]
        elif force_one_window_per_cycle:
            ovu, _, _ = pick_best_fallback(out, pd.to_datetime(win_start), pd.to_datetime(win_end), rise_days)
            conf = "low" if ovu else None
        else:
            ovu, conf = None, None

        if ovu:
            out.loc[out["date"].between(pd.to_datetime(ovu)-pd.Timedelta(days=window_half_width),
                                        pd.to_datetime(ovu)+pd.Timedelta(days=window_half_width)), "phase"] = "ovulation_window"
            out.loc[out["date"] == pd.to_datetime(ovu), "ovulation_estimate"] = pd.to_datetime(ovu)
            out.loc[out["date"] == pd.to_datetime(ovu), "ovulation_confidence"] = conf
        # Fill rest by median split
        mid = out["temp_signal_c"].median()
        out.loc[(out["phase"] == "unlabeled") & (out["temp_signal_c"] <= mid), "phase"] = "follicular"
        out.loc[(out["phase"] == "unlabeled") & (out["temp_signal_c"] >  mid), "phase"] = "luteal"
        return out

    dates = out["date"].dt.date
    for i, start in enumerate(menses_starts):
        end = menses_starts[i+1] - timedelta(days=1) if i+1 < len(menses_starts) else dates.max()
        cyc_mask = (dates >= start) & (dates <= end)
        if not cyc_mask.any():
            continue

        # Menstruation: D1–D5
        for d in range(5):
            day = start + timedelta(days=d)
            if day > end: break
            out.loc[out["date"].dt.date == day, "phase"] = "menstruation"

        # Search window (wider by default)
        win_start = start + timedelta(days=search_days[0])
        win_end   = min(end, start + timedelta(days=search_days[1]))

        # Strong detector
        cands = detect_ovulation_candidates(out.loc[cyc_mask], rise_min, rise_days, win_start, win_end)
        if cands:
            best = max(cands, key=lambda c: c["rise_mean_c"])
            ovu = best["ovulation_date"]; conf = best["confidence"]
        else:
            # Fallback to still show one window per cycle
            if force_one_window_per_cycle:
                ovu, _, _ = pick_best_fallback(out, pd.to_datetime(win_start), pd.to_datetime(win_end), rise_days)
                conf = "low" if ovu else None
            else:
                ovu, conf = None, None

        if ovu:
            out.loc[out["date"].between(pd.to_datetime(ovu)-pd.Timedelta(days=window_half_width),
                                        pd.to_datetime(ovu)+pd.Timedelta(days=window_half_width)), "phase"] = "ovulation_window"
            out.loc[out["date"] == pd.to_datetime(ovu), "ovulation_estimate"] = pd.to_datetime(ovu)
            out.loc[out["date"] == pd.to_datetime(ovu), "ovulation_confidence"] = conf

        # Fill remaining days by relative level
        cyc_mid = out.loc[cyc_mask, "temp_signal_c"].median()
        out.loc[cyc_mask & (out["phase"] == "unlabeled") & (out["temp_signal_c"] <= cyc_mid), "phase"] = "follicular"
        out.loc[cyc_mask & (out["phase"] == "unlabeled") & (out["temp_signal_c"] >  cyc_mid), "phase"] = "luteal"

    return out

PHASE_COLORS = {
    "menstruation": "#e74c3c",
    "follicular": "#1abc9c",
    "ovulation_window": "#f1c40f",
    "luteal": "#9b59b6",
    "premenstrual": "#e67e22",
    "unlabeled": "#95a5a6",
}

def plot_static_matplotlib(df_win: pd.DataFrame, title: str = "120-day cycle view"):
    fig, ax = plt.subplots(figsize=(11, 3.8))
    # Base line (gray)
    ax.plot(df_win["date"], df_win["temp_signal_c"], linewidth=1.2, color="#7f8c8d", alpha=0.8, zorder=1)
    # Colored points by phase
    for phase, color in PHASE_COLORS.items():
        sub = df_win[df_win["phase"] == phase]
        if len(sub) == 0:
            continue
        ax.scatter(sub["date"], sub["temp_signal_c"], s=22, label=phase, color=color, zorder=2)
    # Ovulation markers
    ovus = df_win[df_win["ovulation_estimate"].notna()]["ovulation_estimate"].dt.date.unique()
    for d in ovus:
        ax.axvline(pd.to_datetime(d), color="#f39c12", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature deviation (°C)")
    ax.legend(loc="upper left", ncol=3, fontsize=8, frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig

# ---------------- UI ----------------
st.markdown("Drop your Oura **daily** CSV and choose a 120-day window to visualize. We color-code phases using temperature_trend_deviation (or fallbacks).")

with st.sidebar:
    st.header("Detection settings")
    rise_min = st.slider("Rise threshold (°C)", 0.1, 0.6, 0.25, 0.01)
    rise_days = st.slider("Rise persistence (days)", 2, 5, 3, 1)
    min_cycle = st.slider("Min cycle length", 18, 26, 21, 1)
    max_cycle = st.slider("Max cycle length", 30, 60, 45, 1)
    # NEW knobs
    search_days = st.slider("Ovulation search window (cycle day range)", 6, 30, (8, 24))
    window_half_width = st.slider("Ovulation window half-width (days)", 0, 3, 1)
    force_one = st.checkbox("Guarantee one ovulation window per cycle", value=True)

upl = st.file_uploader("Upload Oura CSV", type=["csv"])
use_demo = st.checkbox("No CSV? Use demo data", value=False)

if not use_demo and upl is None:
    st.info("Upload a CSV or enable 'Use demo data'.")
    st.stop()

# Load/prepare data
try:
    if use_demo:
        dates = pd.date_range("2025-01-01", periods=200, freq="D")
        base = np.sin(np.linspace(0, 4*np.pi, len(dates))) * 0.05
        bump = np.zeros_like(base)
        bump[60:63] += np.array([0.1, 0.25, 0.35])
        bump[130:133] += np.array([0.08, 0.22, 0.33])
        noise = np.random.randn(len(dates)) * 0.03
        temp = base + bump + noise
        raw = pd.DataFrame({"date": dates, "temperature_trend_deviation": temp})
    else:
        raw = pd.read_csv(upl)
    full_df = prepare_df(raw)
except Exception as e:
    st.error(f"Failed to process CSV: {e}")
    st.stop()

# Label phases once on the whole dataset, then slice 120-day windows
menses_starts = infer_menses_starts(full_df, min_cycle, max_cycle)
labeled = label_phases(
    full_df,
    menses_starts,
    rise_min=rise_min,
    rise_days=rise_days,
    search_days=search_days,
    window_half_width=window_half_width,
    force_one_window_per_cycle=force_one
)

# Window selection: pick a start date; we display 120 days from there
unique_dates = labeled["date"].dt.date.unique()
if len(unique_dates) < 2:
    st.warning("Not enough data to visualize. Need at least a few days.")
    st.stop()

start_idx = st.slider("Choose start index (0 = first record) → shows 120 consecutive days", 0, max(0, len(unique_dates)-1), 0)
start_date = unique_dates[start_idx]
end_date = unique_dates[min(start_idx + 119, len(unique_dates)-1)]
win_mask = labeled["date"].dt.date.between(start_date, end_date)
df_win = labeled.loc[win_mask].copy()

st.write(f"**Window:** {start_date} → {end_date} ({len(df_win)} days shown)")

if df_win["temp_signal_c"].notna().sum() < 2:
    st.info("Need at least two valid temperature points in this window to plot.")
else:
    fig = plot_static_matplotlib(df_win, title=f"Cycle view: {start_date} → {end_date}")
    st.pyplot(fig, clear_figure=True)

st.dataframe(df_win[["date","temp_signal_c","phase","ovulation_estimate","ovulation_confidence"]].tail(20), use_container_width=True, hide_index=True)
st.caption("Static view only — no Vega-Lite/Altair, just Matplotlib. Not a medical device.")
