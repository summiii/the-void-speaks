# THE VOID SPEAKS — Streamlit App (6dainn mystical, offline/local)
import os, json, random
from pathlib import Path
import pandas as pd
from mutagen import File as MF
import streamlit as st

# ----- Paths -----
ROOT = Path.cwd()
ASSETS = ROOT / "assets"                 # put your audio files here
ASSETS.mkdir(exist_ok=True)
LIB_JSON = ROOT / "library.json"         # lightweight index of local files

# ----- Logo (optional: THE VOID SPEAKS.png next to app.py) -----
LOGO_PATH = ROOT / "THE VOID SPEAKS.png"
LOGO_TAG = ""
if LOGO_PATH.exists():
    import base64
    b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    LOGO_TAG = f"<img class='logo' src='data:image/png;base64,{b64}'/>"

# ----- Palette / CSS -----
PALETTE = ["#0a0a0d","#15131b","#231b2b","#3e1a4a","#5c2d91","#8b4aff","#b68cff","#d8bfff"]
FOG_CSS = f"""
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
@keyframes fogflow {{ 0%{{background-position:0% 50%}} 100%{{background-position:100% 50%}} }}
.logo-wrap {{ text-align:center; margin-top: .5rem; }}
.logo {{ width: 360px; max-width: 72vw; filter: drop-shadow(0 0 14px rgba(139,74,255,.5)); animation: breathe 5.5s ease-in-out infinite; }}
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
.stButton>button {{ width: 100%; }}
</style>
"""

# ----- Supported file extensions -----
EXTS = {".mp3",".wav",".flac",".aac",".m4a",".ogg"}

def _safe_text(x):
    try:
        return str(x)
    except Exception:
        return ""

def scan_assets():
    rows = []
    for p in ASSETS.rglob("*"):
        if p.suffix.lower() in EXTS:
            title, artist, album, dur = p.stem, "Unknown", "Unknown", 0.0
            try:
                # easy tags
                mfe = MF(p, easy=True)
                if mfe:
                    title  = (mfe.get("title",  [title])   or [title])[0]
                    artist = (mfe.get("artist", ["Unknown"]) or ["Unknown"])[0]
                    album  = (mfe.get("album",  ["Unknown"]) or ["Unknown"])[0]
                # duration
                mff = MF(p)
                if mff and getattr(mff, "info", None):
                    dur = float(getattr(mff.info, "length", 0) or 0)
            except Exception:
                pass
            rows.append({
                "title": _safe_text(title),
                "artist": _safe_text(artist),
                "album": _safe_text(album),
                "duration": dur,
                "path": str(p)
            })
    return rows

def load_index():
    if LIB_JSON.exists():
        try:
            data = json.loads(LIB_JSON.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    rows = scan_assets()
    LIB_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return rows

def save_index(rows):
    LIB_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

def filter_rows(rows, q):
    q = (q or "").strip().lower()
    if not q: return rows
    out = []
    for r in rows:
        blob = f"{r['title']} {r['artist']} {r['album']}".lower()
        if q in blob: out.append(r)
    return out

def fmt_time(sec):
    try:
        sec = int(sec)
        return f"{sec//60:02d}:{sec%60:02d}"
    except Exception:
        return "00:00"

# ----- UI -----
st.set_page_config(page_title="THE VOID SPEAKS", page_icon="💜", layout="wide", initial_sidebar_state="expanded")
st.markdown(FOG_CSS, unsafe_allow_html=True)
st.markdown("<div class='logo-wrap'>"+LOGO_TAG+"</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Library")
    st.caption("Place your audio files in: `./assets/`")
    if st.button("🔄 Rescan"):
        rows = scan_assets()
        save_index(rows)
        st.session_state["rows"] = rows
        st.success("Library updated.", icon="✨")
    st.markdown("---")
    st.markdown("### Queue")
    st.session_state.setdefault("queue", [])
    if st.button("🧹 Clear Queue"):
        st.session_state["queue"].clear()
    st.checkbox("Shuffle", key="shuffle")
    st.selectbox("Loop", ["none","one","all"], key="loop")

# Build/Load index
rows = st.session_state.setdefault("rows", load_index())

# If you want to hard-check the demo file exists, uncomment:
# demo_file = ASSETS / "@FORCEPARKBOISWORLDWIDE - LOTUS.mp3"
# st.sidebar.write("Demo file exists:", demo_file.exists())

query = st.text_input("", placeholder="Search title / artist / album")
filtered = filter_rows(rows, query)

# Grid of cards
cols = st.columns(3)
for i, r in enumerate(filtered):
    with cols[i % 3]:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown(
            f"**{_safe_text(r['title'])}**  \n"
            f"<span class='small'>{_safe_text(r['artist'])} • {_safe_text(r['album'])} • {fmt_time(r['duration'])}</span>",
            unsafe_allow_html=True
        )
        c1, c2 = st.columns([1,1])
        if c1.button("▶ Play", key=f"play_{i}"):
            st.session_state["current_idx"] = i
            st.session_state["current_list"] = [rr["path"] for rr in filtered]
            st.session_state["now"] = r
        if c2.button("➕ Queue", key=f"queue_{i}"):
            st.session_state["queue"].append(r["path"])
        st.markdown("</div>", unsafe_allow_html=True)

# Initialize player state
st.session_state.setdefault("current_idx", 0)
st.session_state.setdefault("current_list", [rr["path"] for rr in filtered] if filtered else [])
if "now" not in st.session_state and filtered:
    st.session_state["now"] = filtered[0]

# Player
st.markdown("<div class='player'>", unsafe_allow_html=True)
left, mid, right = st.columns([3,4,3])

with left:
    now = st.session_state.get("now")
    if now:
        st.markdown(
            f"<div class='title'>{_safe_text(now['title'])}</div>"
            f"<div class='small'>{_safe_text(now['artist'])}</div>", 
            unsafe_allow_html=True
        )
    else:
        st.markdown("<div class='small'>Nothing playing</div>", unsafe_allow_html=True)

with mid:
    c1, c2, c3, c4 = st.columns([1,1,1,8])
    if c1.button("⏮", key="prev"):
        if st.session_state.get("shuffle"):
            st.session_state["current_idx"] = random.randint(0, max(0, len(st.session_state["current_list"])-1))
        else:
            st.session_state["current_idx"] = max(0, st.session_state["current_idx"]-1)
        try:
            path = st.session_state["current_list"][st.session_state["current_idx"]]
            for r in rows:
                if r["path"] == path:
                    st.session_state["now"] = r
                    break
        except Exception:
            pass
    if c2.button("⏯", key="playpause"):
        pass  # Streamlit's audio widget is always "play on demand"
    if c3.button("⏭", key="next"):
        if st.session_state.get("shuffle"):
            st.session_state["current_idx"] = random.randint(0, max(0, len(st.session_state["current_list"])-1))
        else:
            st.session_state["current_idx"] = min(len(st.session_state["current_list"])-1, st.session_state["current_idx"]+1)
        try:
            path = st.session_state["current_list"][st.session_state["current_idx"]]
            for r in rows:
                if r["path"] == path:
                    st.session_state["now"] = r
                    break
        except Exception:
            pass

with right:
    now = st.session_state.get("now")
    if now and now.get("path") and os.path.exists(now["path"]):
        st.audio(now["path"])
    else:
        st.markdown("<div class='small'>No file selected or missing on disk.</div>", unsafe_allow_html=True)
