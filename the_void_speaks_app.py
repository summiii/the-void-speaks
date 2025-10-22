# app.py
# THE VOID SPEAKS — 6dainn-themed local music player (Windows-friendly, MP3-only)

import os, json, random
from pathlib import Path
import streamlit as st
import pandas as pd  # used for convenience; no heavy use

# ------------------ Paths (Windows & cross-platform safe) ------------------
BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
ASSETS.mkdir(exist_ok=True)
IDX_JSON = BASE / "library.json"
LOGO_PNG = BASE / "THE VOID SPEAKS.png"

AUDIO_EXTS = {".mp3"}  # MP3 only, per your request

# ------------------ Optional tag reader (mutagen) ------------------
def _try_read_tags(p: Path):
    title = p.stem
    artist = "Unknown"
    album = "Unknown"
    duration = 0.0
    try:
        from mutagen import File as MF  # optional dependency
        mfe = MF(p, easy=True)
        if mfe:
            title  = (mfe.get("title",  [title])     or [title])[0]
            artist = (mfe.get("artist", ["Unknown"]) or ["Unknown"])[0]
            album  = (mfe.get("album",  ["Unknown"]) or ["Unknown"])[0]
        mf = MF(p)
        if mf and getattr(mf, "info", None):
            length = getattr(mf.info, "length", 0) or 0
            duration = float(length)
    except Exception:
        # No mutagen or unreadable metadata: keep defaults
        pass
    # Normalize to plain strings to avoid unicode edge-cases
    return {
        "title": str(title),
        "artist": str(artist),
        "album": str(album),
        "duration": float(duration),
        "path": str(p),
    }

# ------------------ Library (file scan + lightweight cache) ------------------
def scan_assets():
    rows = []
    for p in ASSETS.rglob("*"):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
            rows.append(_try_read_tags(p))
    return rows

def save_index(rows):
    try:
        IDX_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def load_index():
    if IDX_JSON.exists():
        try:
            data = json.loads(IDX_JSON.read_text(encoding="utf-8"))
            if isinstance(data, list):
                # filter out missing files
                data = [r for r in data if r.get("path") and Path(r["path"]).exists()]
                return data
        except Exception:
            pass
    rows = scan_assets()
    save_index(rows)
    return rows

def filter_rows(rows, q):
    q = (q or "").strip().lower()
    if not q:
        return rows
    out = []
    for r in rows:
        blob = f"{r.get('title','')} {r.get('artist','')} {r.get('album','')}".lower()
        if q in blob:
            out.append(r)
    return out

def fmt_time(sec):
    try:
        sec = int(float(sec))
        return f"{sec//60:02d}:{sec%60:02d}"
    except Exception:
        return "00:00"

# ------------------ Theme (6dainn neon purple / dark gray) ------------------
PALETTE = ["#0a0a0d","#15131b","#231b2b","#3e1a4a","#5c2d91","#8b4aff","#b68cff","#d8bfff"]
LOGO_TAG = ""
if LOGO_PNG.exists():
    import base64
    b64 = base64.b64encode(LOGO_PNG.read_bytes()).decode("utf-8")
    LOGO_TAG = f"<img class='logo' src='data:image/png;base64,{b64}'/>"

CSS = f"""
<style>
:root {{
  --p0: {PALETTE[0]}; --p1: {PALETTE[1]}; --p2: {PALETTE[2]}; --p3: {PALETTE[3]};
  --p4: {PALETTE[4]}; --p5: {PALETTE[5]}; --p6: {PALETTE[6]}; --p7: {PALETTE[7]};
  --txt: #f4f0ff; --muted:#c9c2db;
}}
html, body, .stApp {{
  background: radial-gradient(1200px 800px at 20% 30%, var(--p2), var(--p0)) fixed;
  background-size: 400% 400%;
  animation: fogflow 60s ease-in-out infinite alternate;
  color: var(--txt);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}}
@keyframes fogflow {{
  0% {{ background-position: 0% 50% }}
  100% {{ background-position: 100% 50% }}
}}
.logo-wrap {{ text-align:center; margin: .25rem 0 0.75rem 0; }}
.logo {{
  width: 360px; max-width: 72vw;
  filter: drop-shadow(0 0 14px rgba(139,74,255,.5));
  animation: breathe 5.5s ease-in-out infinite;
}}
@keyframes breathe {{
  0%,100% {{ filter: drop-shadow(0 0 12px rgba(139,74,255,.35)) brightness(1.05); }}
  50%     {{ filter: drop-shadow(0 0 28px rgba(182,140,255,.55)) brightness(1.12); }}
}}
.glass {{
  background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 18px;
  box-shadow: 0 6px 28px rgba(0,0,0,.45), inset 0 0 0 1px rgba(139,74,255,.12);
  padding: 12px 14px;
  margin-bottom: 10px;
}}
.player {{
  position: sticky; bottom: 0; left:0; right:0;
  background: linear-gradient(90deg, rgba(32,26,44,.70), rgba(20,16,28,.70));
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 16px;
  padding: 10px 14px; margin-top: 10px;
  box-shadow: 0 -10px 28px rgba(0,0,0,.45), inset 0 0 0 1px rgba(139,74,255,.22);
}}
.small {{ color: var(--muted); font-size: 12px; }}
.title {{ font-weight:600; letter-spacing:.3px; }}
.card-title {{ font-weight:600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.stButton>button {{ width: 100%; }}
</style>
"""

# ------------------ Page ------------------
st.set_page_config(page_title="THE VOID SPEAKS", page_icon="💜", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='logo-wrap'>"+LOGO_TAG+"</div>", unsafe_allow_html=True)

# ------------------ Sidebar ------------------
with st.sidebar:
    st.markdown("### Library")
    st.caption(f"Drop your .mp3 files in:\n`{ASSETS}`")

    uploaded = st.file_uploader("Upload MP3s", type=["mp3"], accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            # Save uploaded files into assets (overwrite same name safely)
            out_path = ASSETS / Path(f.name).name
            with open(out_path, "wb") as w:
                w.write(f.getbuffer())
        # Rescan after upload
        st.session_state["rows"] = scan_assets()
        save_index(st.session_state["rows"])
        st.success(f"Uploaded {len(uploaded)} file(s) and refreshed library.")

    if st.button("🔄 Rescan"):
        st.session_state["rows"] = scan_assets()
        save_index(st.session_state["rows"])
        st.success("Library updated.")

    st.markdown("---")
    st.markdown("### Player")
    st.checkbox("Shuffle", key="shuffle", value=st.session_state.get("shuffle", False))
    st.selectbox("Loop", ["none","one","all"], key="loop", index=["none","one","all"].index(st.session_state.get("loop","none")))

# ------------------ Load & Search ------------------
rows = st.session_state.setdefault("rows", load_index())
query = st.text_input("Search title / artist / album", "", placeholder="Type to filter your MP3 library…")
rows = filter_rows(rows, query)

# ------------------ Cards Grid ------------------
if not rows:
    st.warning("🎵 No MP3 tracks found. Add files to the `assets` folder or use the uploader in the sidebar.")
else:
    cols = st.columns(3)
    for i, r in enumerate(rows):
        with cols[i % 3]:
            st.markdown("<div class='glass'>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='card-title'>{r.get('title','')}</div>"
                f"<div class='small'>{r.get('artist','Unknown')} • {r.get('album','Unknown')} • {fmt_time(r.get('duration',0))}</div>",
                unsafe_allow_html=True
            )
            c1, c2 = st.columns([1,1])
            # Use stable, unique keys (path-based)
            kbase = r.get("path","") + f"_{i}"
            if c1.button("▶ Play", key="play_"+kbase):
                st.session_state["current_idx"]  = i
                st.session_state["current_list"] = [x.get("path","") for x in rows]
                st.session_state["now"] = r
            if c2.button("➕ Queue", key="queue_"+kbase):
                st.session_state.setdefault("queue", [])
                st.session_state["queue"].append(r.get("path",""))
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------ Player State ------------------
st.session_state.setdefault("current_idx", 0)
st.session_state.setdefault("current_list", [x.get("path","") for x in rows] if rows else [])
if "now" not in st.session_state and rows:
    st.session_state["now"] = rows[0]

# ------------------ Player UI ------------------
st.markdown("<div class='player'>", unsafe_allow_html=True)
left, mid, right = st.columns([3,4,3])

with left:
    now = st.session_state.get("now")
    if now:
        st.markdown(
            f"<div class='title'>{now.get('title','')}</div>"
            f"<div class='small'>{now.get('artist','')}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown("<div class='small'>Nothing playing</div>", unsafe_allow_html=True)

with mid:
    c1, c2, c3, _ = st.columns([1,1,1,8])
    if c1.button("⏮ Prev", key="prev_btn"):
        if st.session_state.get("shuffle"):
            st.session_state["current_idx"] = random.randint(0, max(0, len(st.session_state["current_list"])-1))
        else:
            st.session_state["current_idx"] = max(0, st.session_state["current_idx"] - 1)
        try:
            path = st.session_state["current_list"][st.session_state["current_idx"]]
            for r in rows:
                if r.get("path","") == path:
                    st.session_state["now"] = r
                    break
        except Exception:
            pass
    if c2.button("⏯ Play/Pause", key="playpause_btn"):
        # Streamlit's audio widget is user-controlled; we maintain state only
        pass
    if c3.button("⏭ Next", key="next_btn"):
        if st.session_state.get("shuffle"):
            st.session_state["current_idx"] = random.randint(0, max(0, len(st.session_state["current_list"])-1))
        else:
            st.session_state["current_idx"] = min(len(st.session_state["current_list"])-1, st.session_state["current_idx"] + 1)
        try:
            path = st.session_state["current_list"][st.session_state["current_idx"]]
            for r in rows:
                if r.get("path","") == path:
                    st.session_state["now"] = r
                    break
        except Exception:
            pass

with right:
    now = st.session_state.get("now")
    path = (now or {}).get("path","")
    if path and Path(path).exists():
        st.audio(str(path))
    else:
        st.markdown("<div class='small'>No file selected or file missing.</div>", unsafe_allow_html=True)
