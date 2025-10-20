# THE VOID SPEAKS — Streamlit App (6dainn mystical, offline/local)
import os, json, random
from pathlib import Path
import pandas as pd
from mutagen import File as MF
import streamlit as st

ROOT = Path.cwd()
ASSETS = ROOT / "assets"; ASSETS.mkdir(exist_ok=True)
DB = ROOT / "library.json"

# Use local logo file if present
LOGO_PATH = ROOT / "THE VOID SPEAKS.png"
LOGO_TAG = ""
if LOGO_PATH.exists():
    import base64
    b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    LOGO_TAG = f"<img class='logo' src='data:image/png;base64,{b64}'/>"

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
</style>
"""

EXTS = {".mp3",".wav",".flac",".aac",".m4a",".ogg"}

def scan_assets():
    rows = []
    for p in ASSETS.rglob("*"):
        if p.suffix.lower() in EXTS:
            try:
                mf = MF(p, easy=True)
                title  = (mf.get("title",  [p.stem]) or [p.stem])[0]
                artist = (mf.get("artist", ["Unknown"]) or ["Unknown"])[0]
                album  = (mf.get("album",  ["Unknown"]) or ["Unknown"])[0]
                dur    = float(getattr(mf.info, "length", 0.0))
            except Exception:
                title, artist, album, dur = p.stem, "Unknown", "Unknown", 0.0
            rows.append({"title":title,"artist":artist,"album":album,"duration":dur,"path":str(p)})
    return rows

def load_db():
    if DB.exists():
        try: return json.loads(DB.read_text(encoding="utf-8"))
        except: pass
    rows = scan_assets(); DB.write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
    return rows

def save_db(rows): DB.write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")

def filter_rows(rows, q):
    q=(q or "").strip().lower()
    if not q: return rows
    out=[]
    for r in rows:
        blob=f"{r['title']} {r['artist']} {r['album']}".lower()
        if q in blob: out.append(r)
    return out

def fmt_time(sec):
    try: sec=int(sec); return f"{sec//60:02d}:{sec%60:02d}"
    except: return "00:00"

st.set_page_config(page_title="THE VOID SPEAKS", page_icon="💜", layout="wide", initial_sidebar_state="expanded")
st.markdown(FOG_CSS, unsafe_allow_html=True)

st.markdown("<div class='logo-wrap'>"+LOGO_TAG+"</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Library")
    if st.button("🔄 Rescan"):
        rows = scan_assets(); save_db(rows); st.session_state['rows']=rows; st.success("Library updated.", icon="✨")
    st.markdown("---")
    st.markdown("### Queue")
    st.session_state.setdefault("queue", [])
    if st.button("🧹 Clear Queue"):
        st.session_state["queue"].clear()
    st.checkbox("Shuffle", key="shuffle")
    st.selectbox("Loop", ["none","one","all"], key="loop")

rows = st.session_state.setdefault("rows", load_db())
query = st.text_input("", placeholder="Search title / artist / album")
filtered = filter_rows(rows, query)

cols = st.columns(3)
for i, r in enumerate(filtered):
    with cols[i % 3]:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown(
             f"**{r['title']}**  \n"
             f"<span class='small'>{r['artist']} • {r['album']} • {fmt_time(r['duration'])}</span>",
            unsafe_allow_html=True
        )
cols = st.columns(3)
for i, r in enumerate(filtered):
    title  = r.get("title", "")
    artist = r.get("artist", "Unknown")
    album  = r.get("album", "Unknown")
    dur    = fmt_time(r.get("duration", 0))

    with cols[i % 3]:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)

        # No f-strings with dict indexing → use .format() to avoid parser issues
        card_html = (
            "**{title}**  \n"
            "<span class='small'>{artist} &bull; {album} &bull; {dur}</span>"
        ).format(title=title, artist=artist, album=album, dur=dur)
        st.markdown(card_html, unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1])
        if c1.button("Play", key="play_{:d}".format(i)):
            st.session_state["current_idx"]  = i
            st.session_state["current_list"] = [rr["path"] for rr in filtered]
            st.session_state["now"]          = r

        if c2.button("Add to Queue", key="queue_{:d}".format(i)):
            st.session_state.setdefault("queue", []).append(r["path"])

        st.markdown("</div>", unsafe_allow_html=True)


st.session_state.setdefault("current_idx", 0)
st.session_state.setdefault("current_list", [rr["path"] for rr in filtered] if filtered else [])
if "now" not in st.session_state and filtered:
    st.session_state["now"] = filtered[0]

st.markdown("<div class='player'>", unsafe_allow_html=True)
left, mid, right = st.columns([3,4,3])

with left:
    now = st.session_state.get("now")
    if now:
        st.markdown(f"<div class='title'>{now['title']}</div><div class='small'>{now['artist']}</div>", unsafe_allow_html=True)
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
                if r["path"] == path: st.session_state["now"] = r; break
        except: pass
    if c2.button("⏯", key="playpause"):
        pass
    if c3.button("⏭", key="next"):
        if st.session_state.get("shuffle"):
            st.session_state["current_idx"] = random.randint(0, max(0, len(st.session_state["current_list"])-1))
        else:
            st.session_state["current_idx"] = min(len(st.session_state["current_list"])-1, st.session_state["current_idx"]+1)
        try:
            path = st.session_state["current_list"][st.session_state["current_idx"]]
            for r in rows:
                if r["path"] == path: st.session_state["now"] = r; break
        except: pass

with right:
    if now: st.audio(now["path"])
