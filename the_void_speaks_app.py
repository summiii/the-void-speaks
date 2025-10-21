# app.py
# THE VOID SPEAKS — 6dainn-themed local music player (offline-first)
# - Scans ./assets for audio files (mp3/m4a/ogg/wav/flac/aac)
# - Optional: if music.db exists, loads from SQLite (tracks table) instead
# - Search, shuffle, next/prev, sticky player, neon purple + dark gray UI

import os
import json
import random
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------- Paths ----------
BASE    = Path(__file__).resolve().parent
ASSETS  = BASE / "assets"               # put your audio files here
ASSETS.mkdir(exist_ok=True)
DB_PATH = BASE / "music.db"            # optional sqlite db
IDX_JSON = BASE / "library.json"       # lightweight local index (when not using DB)
LOGO_PNG = BASE / "THE VOID SPEAKS.png"

# ---------- Optional tag reader (mutagen) ----------
def _try_read_tags(p: Path):
    """Try to read tags/duration with mutagen. If not available or fails, return minimal."""
    title = p.stem
    artist = "Unknown"
    album = "Unknown"
    duration = 0.0
    try:
        from mutagen import File as MF  # optional dependency
        mfe = MF(p, easy=True)
        if mfe:
            title  = (mfe.get("title",  [title])    or [title])[0]
            artist = (mfe.get("artist", ["Unknown"]) or ["Unknown"])[0]
            album  = (mfe.get("album",  ["Unknown"]) or ["Unknown"])[0]
        mf = MF(p)
        if mf and getattr(mf, "info", None):
            length = getattr(mf.info, "length", 0) or 0
            duration = float(length)
    except Exception:
        pass
    return {
        "title": str(title),
        "artist": str(artist),
        "album": str(album),
        "duration": float(duration),
        "path": str(p)
    }

# ---------- Library loaders ----------
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".flac"}

def scan_assets():
    rows = []
    for p in ASSETS.rglob("*"):
        if p.suffix.lower() in AUDIO_EXTS:
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
                return data
        except Exception:
            pass
    rows = scan_assets()
    save_index(rows)
    return rows

def load_from_db(q: str = ""):
    con = sqlite3.connect(DB_PATH)
    if q.strip():
        df = pd.read_sql_query(
            """
            SELECT
              COALESCE(title,'')   AS title,
              COALESCE(artist,'')  AS artist,
              COALESCE(album,'')   AS album,
              COALESCE(duration,0) AS duration,
              COALESCE(local_path,'') AS path
            FROM tracks
            WHERE
              title  LIKE ? OR
              artist LIKE ? OR
              album  LIKE ?
            LIMIT 1000
            """,
            con, params=[f"%{q}%", f"%{q}%", f"%{q}%"]
        )
    else:
        df = pd.read_sql_query(
            """
            SELECT
              COALESCE(title,'')   AS title,
              COALESCE(artist,'')  AS artist,
              COALESCE(album,'')   AS album,
              COALESCE(duration,0) AS duration,
              COALESCE(local_path,'') AS path
            FROM tracks
            ORDER BY RANDOM()
            LIMIT 1000
            """,
            con
        )
    con.close()
    return df.to_dict("records")

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

# ---------- Visual theme (6dainn) ----------
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
.logo-wrap {{ text-align:center; margin-top: .25rem; }}
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
.card-title {{ font-weight:600; }}
.stButton>button {{ width: 100%; }}
</style>
"""

# ---------- Page ----------
st.set_page_config(page_title="THE VOID SPEAKS", page_icon="💜", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<div class='logo-wrap'>"+LOGO_TAG+"</div>", unsafe_allow_html=True)

# ---------- Sidebar controls ----------
with st.sidebar:
    st.markdown("### Library")
    st.caption("Place audio files in: ./assets/")
    # choose source mode
    use_db = DB_PATH.exists()
    st.write(f"Source: {'music.db' if use_db else 'assets/ scan'}")
    if not use_db:
        if st.button("Rescan"):
            st.session_state["rows"] = scan_assets()
            save_index(st.session_state["rows"])
            st.success("Library updated.")
    st.markdown("---")
    st.markdown("### Player")
    st.checkbox("Shuffle", key="shuffle", value=st.session_state.get("shuffle", False))
    st.selectbox("Loop", ["none","one","all"], key="loop", index=["none","one","all"].index(st.session_state.get("loop","none")))
    st.markdown("---")
    st.markdown("### Debug")
    st.write("Assets dir:", str(ASSETS))

# ---------- Load library ----------
query = st.text_input("Search title / artist / album", "", placeholder="@FORCEPARKBOISWORLDWIDE - LOTUS")

if DB_PATH.exists():
    rows = load_from_db(query)
else:
    rows = st.session_state.setdefault("rows", load_index())
    rows = filter_rows(rows, query)

# ---------- Cards grid ----------
if not rows:
    st.warning("No tracks found.")
else:
    cols = st.columns(3)
    for i, r in enumerate(rows):
        with cols[i % 3]:
            st.markdown("<div class='glass'>", unsafe_allow_html=True)
            title  = r.get("title","")
            artist = r.get("artist","")
            album  = r.get("album","")
            dur    = fmt_time(r.get("duration",0))
            st.markdown(f"<div class='card-title'>{title}</div><div class='small'>{artist} - {album} - {dur}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns([1,1])
            if c1.button("Play", key=f"play_{i}"):
                st.session_state["current_idx"]  = i
                st.session_state["current_list"] = [x.get("path","") for x in rows]
                st.session_state["now"] = r
            if c2.button("Queue", key=f"queue_{i}"):
                st.session_state.setdefault("queue", [])
                st.session_state["queue"].append(r.get("path",""))
            st.markdown("</div>", unsafe_allow_html=True)

# ---------- Player state ----------
st.session_state.setdefault("current_idx", 0)
st.session_state.setdefault("current_list", [x.get("path","") for x in rows] if rows else [])
if "now" not in st.session_state and rows:
    st.session_state["now"] = rows[0]

# ---------- Player UI ----------
st.markdown("<div class='player'>", unsafe_allow_html=True)
left, mid, right = st.columns([3,4,3])

with left:
    now = st.session_state.get("now")
    if now:
        st.markdown(f"<div class='title'>{now.get('title','')}</div><div class='small'>{now.get('artist','')}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='small'>Nothing playing</div>", unsafe_allow_html=True)

with mid:
    c1, c2, c3, _ = st.columns([1,1,1,8])
    if c1.button("Prev", key="prev"):
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
    if c2.button("Play/Pause", key="playpause"):
        pass  # Streamlit audio widget is user-controlled; we keep state-only.
    if c3.button("Next", key="next"):
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
    if path and os.path.exists(path):
        st.audio(path)
    else:
        if path:
            st.markdown("<div class='small'>File not found on disk.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='small'>No file selected.</div>", unsafe_allow_html=True)
