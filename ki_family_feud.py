import streamlit as st
import time

st.set_page_config(page_title="KI-Berufsfelder – Quiz", page_icon="🤖", layout="wide")

# -------------------- Daten --------------------
QUESTION = "In welchen acht Berufsfeldern wird Künstliche Intelligenz (KI) heutzutage am häufigsten eingesetzt?"

ANSWERS = [
    ("kommunikation & IT", "59,5 %"),
    ("Finanz & Versicherungswesen", "50,3 %"),
    ("Unternehmensnahedienstleistungen & Management", "37,1 %"),
    ("Erziehung & Unterricht", "34,3 %"),
    ("Sozialwesen & Forschung", "22,1 %"),
    ("Verarbeitendes Gewerbe", "21,2 %"),
    ("Gesundheitswesen", "15,7 %"),
    ("Baugewerbe", "14,6 %"),
]

# -------------------- Session State --------------------
if "revealed" not in st.session_state:
    st.session_state.revealed = set()
if "scores" not in st.session_state:
    st.session_state.scores = [0, 0]
if "active_team" not in st.session_state:
    st.session_state.active_team = 0

# -------------------- Styling --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;600;800&display=swap');

.stApp {
    background:
      radial-gradient(circle at 15% 10%, rgba(0,245,255,.10), transparent 30%),
      radial-gradient(circle at 85% 15%, rgba(255,0,200,.10), transparent 28%),
      #080b16;
    color: #f4f7ff;
}
.block-container { max-width: 1200px; padding-top: 2rem; }
h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; }
.hero {
    text-align:center; padding: 22px 18px 26px; margin-bottom: 18px;
    border: 1px solid #00eaff55; border-radius: 18px;
    background: linear-gradient(135deg, #10182b, #171025);
    box-shadow: 0 0 25px #00eaff18, inset 0 0 25px #ff00d008;
}
.eyebrow { color:#00eaff; letter-spacing:4px; font:700 12px 'Orbitron'; }
.question { font:700 clamp(20px, 3vw, 30px) 'Inter'; margin-top:12px; }
.tile {
    min-height: 112px; display:flex; flex-direction:column; align-items:center;
    justify-content:center; text-align:center; border-radius:14px;
    border:1px solid #00eaff; background:linear-gradient(145deg,#111d35,#0b1020);
    box-shadow:0 0 13px #00eaff25, inset 0 0 12px #00eaff0a;
    padding:12px; margin-bottom:8px;
}
.tile-number { font:900 32px 'Orbitron'; color:#00eaff; }
.tile-answer { font:700 15px 'Inter'; color:#fff; margin-top:7px; }
.tile-percent { font:900 24px 'Orbitron'; color:#ff39df; margin-top:8px; text-shadow:0 0 12px #ff39df77; }
.score-card {
    background:#10182b; border:1px solid #ff39df66; border-radius:14px;
    text-align:center; padding:15px; box-shadow:0 0 18px #ff39df12;
}
.score-label {font:700 12px 'Orbitron'; color:#aab5d5; letter-spacing:2px;}
.score-number {font:900 34px 'Orbitron'; color:#ff39df;}
div.stButton > button {
    width:100%; min-height:48px; border-radius:12px; font-weight:800;
    border:1px solid #00eaff; background:#101d35; color:#00eaff;
    transition:all .18s ease;
}
div.stButton > button:hover {
    border-color:#ff39df; color:#fff; background:#241333;
    box-shadow:0 0 16px #ff39df44; transform:translateY(-2px);
}
div[data-testid="stRadio"] label { color:#eaf0ff; }
</style>
""", unsafe_allow_html=True)

# -------------------- Header --------------------
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">AI KNOWLEDGE SHOWDOWN</div>
  <div class="question">{QUESTION}</div>
</div>
""", unsafe_allow_html=True)

# -------------------- Scoreboard --------------------
st.subheader("🏆 Spielstand")
score_cols = st.columns(2)
for i, col in enumerate(score_cols):
    with col:
        st.markdown(
            f'<div class="score-card"><div class="score-label">TEAM {i+1}</div>'
            f'<div class="score-number">{st.session_state.scores[i]}</div></div>',
            unsafe_allow_html=True
        )

team_col, point_col, add_col = st.columns([2, 1, 1])
with team_col:
    selected_team = st.radio("Punkte für:", ["Team 1", "Team 2"], horizontal=True,
                             index=st.session_state.active_team)
    st.session_state.active_team = 0 if selected_team == "Team 1" else 1
with point_col:
    points = st.number_input("Punkte", min_value=1, max_value=100, value=1, step=1)
with add_col:
    st.write("")
    st.write("")
    if st.button("➕ Punkte vergeben", key="add_points"):
        st.session_state.scores[st.session_state.active_team] += int(points)
        st.rerun()

st.divider()
st.markdown("### 🔮 Antworttafel")
st.caption("Klicke auf eine Nummer, um die Antwort und ihren Prozentwert aufzudecken.")

# -------------------- Board --------------------
cols = st.columns(4, gap="medium")
for idx, (answer, percentage) in enumerate(ANSWERS):
    with cols[idx % 4]:
        if idx in st.session_state.revealed:
            st.markdown(
                f'<div class="tile"><div class="tile-answer">{answer}</div>'
                f'<div class="tile-percent">{percentage}</div></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="tile"><div class="tile-number">{idx+1}</div>'
                f'<div class="tile-answer">ANTWORT VERDECKT</div></div>',
                unsafe_allow_html=True
            )
            if st.button(f"🔓 Feld {idx+1} aufdecken", key=f"reveal_{idx}"):
                st.session_state.revealed.add(idx)
                st.rerun()

# -------------------- Controls --------------------
st.divider()
left, right = st.columns([3, 1])
with left:
    revealed_count = len(st.session_state.revealed)
    st.progress(revealed_count / len(ANSWERS), text=f"{revealed_count} von 8 Antworten aufgedeckt")
with right:
    if st.button("🔄 Spiel zurücksetzen", type="primary", key="reset"):
        st.session_state.revealed = set()
        st.session_state.scores = [0, 0]
        st.session_state.active_team = 0
        st.rerun()

