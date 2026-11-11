import html
import math
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from main import findAnomalies

st.set_page_config(page_title="Sentinel", page_icon=":material/shield_lock:", layout="wide")

SAMPLE_FILE = Path(__file__).resolve().parent.parent / "sample_data.json"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Each reason a login can be flagged for, with its Material icon
REASONS = {
    "Impossible travel": "flight_takeoff",
    "Failed attempts": "lock_reset",
    "Risky device": "devices_other",
    "Off-hours": "dark_mode",
    "Unusual pattern": "query_stats",
}
DETECTORS = [
    ("flight_takeoff", "Impossible travel", "Two logins too far apart to travel between in time."),
    ("lock_reset", "Failed attempts", "Repeated wrong passwords before getting in."),
    ("devices_other", "Risky devices", "Tor browsers, scripts and unknown machines."),
    ("dark_mode", "Off-hours", "Logins between midnight and 6 am."),
]

# ---------------------------------------------------------------- styles

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..500,0..1,0');

:root {
  --bg: #FFFFFF;
  --surface: #F6F7F9;
  --line: #E4E7EC;
  --ink: #16181D;
  --muted: #667085;
  --threat: #D92D20;
  --amber: #B54708;
  --ok: #067647;
  --mono: 'IBM Plex Mono', ui-monospace, monospace;
  --ease: cubic-bezier(.2, .7, .2, 1);
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1000px; margin: 0 auto; }
.hdr [data-testid="stHeaderActionElements"], .readout [data-testid="stHeaderActionElements"] { display: none; }

.ms {
  font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal;
  font-size: 1.2em; line-height: 1; vertical-align: -.2em; letter-spacing: normal;
  display: inline-block; white-space: nowrap; direction: ltr; -webkit-font-smoothing: antialiased;
  font-feature-settings: 'liga';
}

/* ---------- Header ---------- */
.hdr { display: flex; align-items: center; gap: 12px; margin-top: .5rem; }
.hdr .badge { color: var(--ink); font-size: 1.9rem; }
.wm { margin: 0 !important; padding: 0 !important; font-size: 2.2rem !important; font-weight: 600 !important; line-height: 1.1 !important; }
.hdr p { margin: 4px 0 0; color: var(--muted); font-size: .95rem; }

/* ---------- Status line ---------- */
.status { display: inline-flex; align-items: center; gap: 8px; margin: 4px 0; font-size: .875rem; color: var(--muted); }
.status b { color: var(--ink); font-weight: 600; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #98A2B3; flex: none; }
.dot.low { background: var(--ok); }
.dot.elevated { background: var(--amber); }
.dot.critical { background: var(--threat); }

/* ---------- Upload box ---------- */
[data-testid="stFileUploaderDropzone"] {
  border: 1px dashed #C9CED6; border-radius: 10px; background: var(--surface);
  transition: border-color .2s var(--ease);
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--ink); }

/* ---------- Detector list (empty state) ---------- */
.detectors { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px 32px; margin: 12px 0 16px; }
.det { display: flex; gap: 12px; }
.det .ms { color: var(--muted); font-size: 1.3rem; }
.det b { display: block; font-weight: 600; color: var(--ink); }
.det span.d { color: var(--muted); font-size: .88rem; line-height: 1.45; }

/* ---------- Live scan list ---------- */
.term { border: 1px solid var(--line); border-radius: 10px; background: var(--bg); font-family: var(--mono); font-size: .8rem; }
.term-hd { display: flex; align-items: center; gap: 8px; padding: 10px 14px; color: var(--ink); }
.term-hd .pct { margin-left: auto; color: var(--muted); }
.bar { height: 2px; background: var(--line); }
.bar i { display: block; height: 100%; background: var(--ink); transition: width .4s var(--ease); }
.feed { list-style: none; margin: 0; padding: 10px 14px 12px; max-height: 260px; overflow: hidden; display: flex; flex-direction: column; justify-content: flex-end; }
.feed li { display: grid; grid-template-columns: 52px 78px 1fr auto; gap: 10px; padding: 2px 0; color: var(--muted); white-space: nowrap; }
.feed li .u { color: var(--ink); }
.feed li .loc { overflow: hidden; text-overflow: ellipsis; }
.feed li .ok { color: var(--muted); }
.feed li .bad { color: var(--threat); }
.feed li.new { animation: lineIn .3s var(--ease) both; }
@keyframes lineIn { from { opacity: 0; } }

/* ---------- Results readout ---------- */
.readout { margin: 8px 0 2px; }
.readout h3 { font-size: 1.5rem !important; font-weight: 600 !important; margin: 0 0 4px !important; padding: 0 !important; }
.readout p { color: var(--muted); margin: 0 0 14px; }
.strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(10px, 1fr)); gap: 3px; }
.strip i { height: 24px; border-radius: 2px; background: var(--line); animation: cellOn .4s var(--ease) both; animation-delay: var(--d); }
.strip i.f { background: var(--threat); }
@keyframes cellOn { from { opacity: 0; } }
.legend { display: flex; gap: 18px; margin: 10px 0 6px; font-size: .78rem; color: var(--muted); }
.legend span::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; background: var(--line); }
.legend span.f::before { background: var(--threat); }

/* ---------- User timeline (detail) ---------- */
.tl { border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; animation: fadeIn .3s var(--ease) both; }
.tl h4 { margin: 0 0 12px !important; padding: 0 !important; font-size: 1.05rem !important; font-weight: 600 !important; }
.tl ol { list-style: none; margin: 0; padding: 0; position: relative; }
.tl ol::before { content: ""; position: absolute; left: 4px; top: 6px; bottom: 6px; width: 1px; background: var(--line); }
.tl li { position: relative; padding: 0 0 14px 22px; }
.tl li::before { content: ""; position: absolute; left: 0; top: 5px; width: 9px; height: 9px; border-radius: 50%; background: var(--bg); border: 1.5px solid #98A2B3; }
.tl li.f::before { border-color: var(--threat); background: var(--threat); }
.tl .when { font-family: var(--mono); font-size: .76rem; color: var(--muted); }
.tl .where { color: var(--ink); font-weight: 500; }
.tl .hop { font-size: .8rem; color: var(--muted); margin-top: 2px; }
.tl .hop.bad { color: var(--threat); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.chip { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 999px; font-size: .75rem; color: var(--threat); background: #FEF3F2; }
.hint { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: .9rem; padding: 10px 0; }
@keyframes fadeIn { from { opacity: 0; } }

[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
button:focus-visible, [role="tab"]:focus-visible { outline: 2px solid var(--ink) !important; outline-offset: 2px; }

@media (max-width: 640px) {
  .detectors { grid-template-columns: 1fr; }
  .wm { font-size: 1.8rem !important; }
  .feed li { grid-template-columns: 44px 70px 1fr; }
  .feed li .r { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers

def icon(name):
    return f'<span class="ms" aria-hidden="true">{name}</span>'


def fmt_speed(mph):
    if mph is None or (isinstance(mph, float) and math.isnan(mph)):
        return "—"
    if math.isinf(mph):
        return "instant"
    # main.py caps speeds at 1,000 mph, so anything at the cap is really "at least" that
    return "over 1,000 mph" if mph >= 1000 else f"{mph:,.0f} mph"


def threat_level(rate):
    if rate < 0.10:
        return "low", "Low"
    if rate < 0.30:
        return "elevated", "Elevated"
    return "critical", "Critical"


def risk_score(category):
    found = [c for c in category.split(", ") if c != "Unusual pattern"]
    return max(len(found), 1)


def feed_html(lines, done, total, label):
    pct = round(100 * done / total) if total else 0
    rows = "".join(lines[-14:])
    return f"""
    <div class="term" role="status" aria-live="polite">
      <div class="term-hd"><span class="dot live"></span>{html.escape(label)}<span class="pct">{pct}%</span></div>
      <div class="bar"><i style="width:{pct}%"></i></div>
      <ol class="feed">{rows}</ol>
    </div>"""


def feed_line(done, total, user_id, table, new=True):
    places = list(dict.fromkeys(table["location"]))
    route = " → ".join(places)
    fast = table["impossible_travel_anomaly"].any()
    if fast:
        top = table["speed_mph"].max()
        result = f'<span class="r bad">{fmt_speed(top)}</span>'
    else:
        result = '<span class="r ok">clear</span>'
    return (
        f'<li class="{"new" if new else ""}"><span>{done:02d}/{total:02d}</span>'
        f'<span class="u">{html.escape(str(user_id))}</span>'
        f'<span class="loc">{html.escape(route)}</span>{result}</li>'
    )


def run_scan(path):
    holder = st.empty()
    lines = []
    started = time.perf_counter()
    holder.markdown(feed_html(lines, 0, 1, "Reading log file…"), unsafe_allow_html=True)

    def on_progress(done, total, user_id, table):
        lines[:] = [l.replace('class="new"', 'class=""') for l in lines]
        lines.append(feed_line(done, total, user_id, table))
        holder.markdown(feed_html(lines, done, total, f"Checking {total} users"), unsafe_allow_html=True)

    try:
        results = findAnomalies(str(path), on_progress=on_progress)
    except Exception as error:
        holder.empty()
        st.error(
            "Couldn't scan this file. Check that it's a JSON list of logins with timestamp, user_id, "
            "location, device_type and failed_attempts, and that you're online — locations are looked up on the internet.",
            icon=":material/error:",
        )
        with st.expander("Error details"):
            st.code(str(error))
        st.stop()

    holder.empty()
    st.session_state["scan_lines"] = [l.replace('class="new"', 'class=""') for l in lines]
    st.session_state["scan_seconds"] = time.perf_counter() - started
    return results


def timeline_html(user_rows):
    items = []
    previous = None
    for row in user_rows.to_dict("records"):
        hop = ""
        if previous is not None and previous["location"] != row["location"]:
            bad = bool(row.get("impossible_travel_anomaly"))
            hop = (f'<div class="hop {"bad" if bad else ""}">{icon("flight_takeoff")} from {html.escape(previous["location"])} '
                   f'at {fmt_speed(row["speed_mph"])}{" — not physically possible" if bad else ""}</div>')
        chips = ""
        if row["flagged"] == 1:
            chips = '<div class="chips">' + "".join(
                f'<span class="chip">{icon(REASONS.get(c, "flag"))}{html.escape(c)}</span>' for c in row["category"].split(", ")
            ) + "</div>"
        when = pd.Timestamp(row["timestamp"]).strftime("%b %d, %Y %I:%M %p")
        items.append(
            f'<li class="{"f" if row["flagged"] == 1 else ""}"><div class="when">{when}</div>'
            f'<div class="where">{html.escape(row["location"])} <span class="when">on {html.escape(row["device_type"])}'
            f'{f", {row["failed_attempts"]} failed attempts" if row["failed_attempts"] else ""}</span></div>{hop}{chips}</li>'
        )
        previous = row
    user = html.escape(str(user_rows["user_id"].iloc[0]))
    return f'<div class="tl"><h4>{icon("person_search")} {user} login history</h4><ol>{"".join(items)}</ol></div>'


# ---------------------------------------------------------------- header

st.markdown(f"""
<div class="hdr">
  <div class="badge">{icon("shield_lock")}</div>
  <div><h1 class="wm">Sentinel</h1><p>Finds suspicious logins in your access logs.</p></div>
</div>
""", unsafe_allow_html=True)

status_slot = st.empty()

uploaded = st.file_uploader("Drop a login log file (JSON)", type=["json"])

# Work out which file to scan: an upload wins over the sample
source = None
if uploaded is not None:
    st.session_state.pop("use_sample", None)
    save_path = UPLOAD_DIR / Path(uploaded.name).name
    source = (save_path, (uploaded.name, uploaded.size))
    if st.session_state.get("results_key") != source[1]:
        save_path.write_bytes(uploaded.getbuffer())
elif st.session_state.get("use_sample"):
    source = (SAMPLE_FILE, ("sample", SAMPLE_FILE.stat().st_size))

if source is None:
    for key in ("results", "results_key", "scan_lines"):
        st.session_state.pop(key, None)
    status_slot.markdown('<div class="status"><span class="dot live"></span><b>Ready</b> upload a log file to start</div>',
                         unsafe_allow_html=True)
    st.markdown('<div class="detectors">' + "".join(
        f'<div class="det">{icon(i)}<div><b>{t}</b><span class="d">{d}</span></div></div>' for i, t, d in DETECTORS
    ) + "</div>", unsafe_allow_html=True)
    if st.button("Try the sample log", icon=":material/play_arrow:"):
        st.session_state["use_sample"] = True
        st.rerun()
    st.stop()

path, file_key = source
if st.session_state.get("results_key") != file_key:
    status_slot.markdown('<div class="status"><span class="dot live"></span><b>Scanning</b> checking every login</div>',
                         unsafe_allow_html=True)
    results = run_scan(path)
    st.session_state["results"] = results
    st.session_state["results_key"] = file_key
    st.session_state.pop("picked_user", None)

results = st.session_state["results"]
flagged = results[results["flagged"] == 1].copy()
total = len(results)
rate = len(flagged) / total if total else 0
level_class, level_name = threat_level(rate)

status_slot.markdown(
    f'<div class="status"><span class="dot {level_class}"></span><b>Threat level {level_name}</b> '
    f'scan finished in {st.session_state.get("scan_seconds", 0):.1f}s</div>',
    unsafe_allow_html=True,
)

if st.session_state.get("use_sample"):
    if st.button("Clear sample", icon=":material/close:", type="tertiary"):
        st.session_state.pop("use_sample", None)
        st.rerun()

# ---------------------------------------------------------------- readout

timeline = results.sort_values("timestamp").reset_index(drop=True)
cells = "".join(
    f'<i class="{"f" if r["flagged"] == 1 else ""}" style="--d:{min(i * 0.03, 1.2):.2f}s" '
    f'title="{html.escape(str(r["user_id"]))} — {html.escape(r["location"])}, {pd.Timestamp(r["timestamp"]).strftime("%b %d %I:%M %p")}"></i>'
    for i, r in timeline.iterrows()
)
users = results["user_id"].nunique()
headline = "No suspicious logins found" if flagged.empty else f"{len(flagged)} of {total} logins look suspicious"
st.markdown(f"""
<div class="readout">
  <h3>{headline}</h3>
  <p>{total} logins from {users} users, oldest to newest. Hover a cell for details.</p>
  <div class="strip" role="img" aria-label="{len(flagged)} flagged logins out of {total}">{cells}</div>
  <div class="legend"><span>Normal</span><span class="f">Flagged</span></div>
</div>
""", unsafe_allow_html=True)

with st.expander(f"Scan log ({len(st.session_state.get('scan_lines', []))} users checked)", icon=":material/terminal:"):
    st.markdown(f'<div class="term"><ol class="feed" style="max-height:none">{"".join(st.session_state.get("scan_lines", []))}</ol></div>',
                unsafe_allow_html=True)

# ---------------------------------------------------------------- tabs

tab_threats, tab_all = st.tabs([":material/gpp_maybe: Threats", ":material/list: All logins"])

with tab_threats:
    if flagged.empty:
        st.success("Every login in this file looks normal.", icon=":material/verified_user:")
    else:
        flagged["risk"] = flagged["category"].apply(risk_score)
        present = [r for r in REASONS if flagged["category"].str.contains(r, regex=False).any()]
        picked = st.pills(
            "Filter by reason", present, selection_mode="multi",
            format_func=lambda r: f":material/{REASONS[r]}: {r}",
        )
        shown = flagged
        if picked:
            shown = flagged[flagged["category"].apply(lambda c: any(p in c for p in picked))]
        shown = shown.sort_values(["risk", "timestamp"], ascending=[False, True]).reset_index(drop=True)

        event = st.dataframe(
            shown[["risk", "user_id", "timestamp", "location", "device_type", "failed_attempts", "category"]],
            hide_index=True, use_container_width=True, on_select="rerun", selection_mode="single-row",
            key="threat_table",
            column_config={
                "risk": st.column_config.ProgressColumn("Risk", min_value=0, max_value=4, format="%d / 4", width="small"),
                "user_id": "User",
                "timestamp": st.column_config.DatetimeColumn("Time", format="MMM D, h:mm a"),
                "location": "Location",
                "device_type": "Device",
                "failed_attempts": st.column_config.NumberColumn("Failed", width="small"),
                "category": st.column_config.TextColumn("Why it was flagged", width="large"),
            },
        )
        rows = event.selection.rows
        if rows:
            user = shown.iloc[rows[0]]["user_id"]
            history = results[results["user_id"] == user].sort_values("timestamp")
            st.markdown(timeline_html(history), unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="hint">{icon("touch_app")} Select a row to see that user\'s full login history.</div>',
                        unsafe_allow_html=True)

with tab_all:
    view = results.sort_values("timestamp").copy()
    view["status"] = view["flagged"].map({1: "Flagged", 0: "Clear"})
    export = view.drop(columns=["coords"], errors="ignore").to_csv(index=False).encode()
    view["speed_mph"] = view["speed_mph"].apply(fmt_speed)
    st.dataframe(
        view[["status", "user_id", "timestamp", "location", "device_type", "failed_attempts", "speed_mph"]],
        hide_index=True, use_container_width=True,
        column_config={
            "status": "Status",
            "user_id": "User",
            "timestamp": st.column_config.DatetimeColumn("Time", format="MMM D, YYYY h:mm a"),
            "location": "Location",
            "device_type": "Device",
            "failed_attempts": st.column_config.NumberColumn("Failed", width="small"),
            "speed_mph": st.column_config.TextColumn("Travel speed"),
        },
    )
    st.download_button("Download results (CSV)", export, file_name="sentinel_results.csv", mime="text/csv",
                       icon=":material/download:")
