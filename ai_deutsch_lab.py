import re
import html
import streamlit as st

# Install:
#   python -m pip install --upgrade streamlit google-genai
# Run:
#   python -m streamlit run ai_deutsch_lab.py

st.set_page_config(
    page_title="AI LAB | Wie entsteht eine KI-Antwort?",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------- DESIGN -----------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --yellow:#ffd400; --black:#08090b; --panel:#131519; --line:#34373d; --muted:#b5b8bf; }
.stApp { background:var(--black); color:#f5f5f5; font-family:'Manrope',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1200px; padding-top:2rem; padding-bottom:3rem; }
h1,h2,h3 { color:var(--yellow)!important; letter-spacing:-.03em; }
p,li { line-height:1.65; }
.stCaption, [data-testid="stCaptionContainer"] { color:var(--muted)!important; }
div.stButton > button, div.stDownloadButton > button {
  background:var(--yellow); color:#08090b; border:0; border-radius:10px;
  font-weight:800; min-height:2.8rem; width:100%;
}
div.stButton > button:hover, div.stDownloadButton > button:hover { background:#ffe45c; color:#08090b; }
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
  background:#17191e; color:white; border:1px solid #555; border-radius:10px;
}
.lab-card { background:linear-gradient(145deg,#17191e,#101115); border:1px solid var(--line);
  border-radius:18px; padding:22px 24px; margin:10px 0 18px; }
.eyebrow { color:var(--yellow); font-family:'DM Mono',monospace; font-size:.78rem;
  letter-spacing:.14em; font-weight:500; }
.hero { font-size:clamp(2rem,4vw,3.5rem); font-weight:800; line-height:1.12; margin:.5rem 0; }
.muted { color:var(--muted); }
.yellow { color:var(--yellow); }
.stepnum { display:inline-block; color:#090a0c; background:var(--yellow); border-radius:8px;
  padding:5px 10px; font-weight:900; margin-right:8px; }
.token { display:inline-block; background:#292b31; color:var(--yellow); border:1px solid #555;
  border-radius:8px; padding:8px 11px; margin:4px; font-family:'DM Mono',monospace; }
.flow { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin:14px 0; }
.flowbox { border:1px solid #555; background:#1a1c21; padding:12px 15px; border-radius:10px; text-align:center; }
.arrow { color:var(--yellow); font-size:1.5rem; font-weight:900; }
.callout { border-left:4px solid var(--yellow); padding:12px 16px; background:#1b1c1e; border-radius:5px; }
.metric { background:#1b1d22; border:1px solid #3a3d43; padding:15px; border-radius:12px; }
.metric strong { display:block; color:var(--yellow); font-size:1.5rem; }
.small { font-size:.9rem; color:var(--muted); }
.stProgress > div > div > div > div { background:var(--yellow); }
hr { border-color:#333!important; }
</style>
""", unsafe_allow_html=True)

# --------------------------- SESSION STATE ---------------------------------
defaults = {
    "stage": 0,
    "question": "",
    "answer": "",
    "usage": None,
    "model_used": "",
    "error": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

STAGES = [
    "START", "FRAGE", "TOKENS", "ZAHLEN & VEKTOREN",
    "NEURONALES NETZ", "WISSEN", "GENERIERUNG", "ERGEBNIS"
]
stage = st.session_state.stage
question = st.session_state.question.strip()

# A simple, visible approximation for teaching. This is NOT Gemini's tokenizer.
def illustrative_tokens(text):
    return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)

# --------------------------- HEADER / NAV ----------------------------------
st.markdown('<div class="eyebrow">⚡ AI LAB · DEUTSCH · LIVE-EXPERIMENT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero">Wie entsteht eine Antwort<br>in einer künstlichen Intelligenz?</div>', unsafe_allow_html=True)
st.markdown('<p class="muted">Eine Frage. Acht Stationen. Ein Blick hinter die Antwort.</p>', unsafe_allow_html=True)

nav1, nav2, nav3 = st.columns([1, 1, 4])
with nav1:
    if st.button("← Zurück", disabled=(stage == 0), use_container_width=True):
        st.session_state.stage = max(0, stage - 1)
        st.rerun()
with nav2:
    if st.button("Weiter →", disabled=(stage == 7), use_container_width=True):
        st.session_state.stage = min(7, stage + 1)
        st.rerun()
with nav3:
    st.progress((stage + 1) / 8, text=f"STATION {stage + 1}/8  ·  {STAGES[stage]}")
st.markdown("---")


def card(kicker, title, body=""):
    st.markdown(
        f'<div class="lab-card"><div class="eyebrow">{html.escape(kicker)}</div>'
        f'<div style="font-size:1.7rem;font-weight:800;margin:8px 0 10px">{html.escape(title)}</div>'
        f'<div>{body}</div></div>',
        unsafe_allow_html=True,
    )


def diagram_svg(kind):
    if kind == "pipeline":
        labels = ["Frage", "Tokens", "Vektoren", "Modell", "Antwort"]
        x = [25, 205, 385, 565, 745]
        parts = []
        for i, (label, xpos) in enumerate(zip(labels, x)):
            parts.append(f'<rect x="{xpos}" y="55" width="135" height="62" rx="12" fill="#1b1d22" stroke="#ffd400" stroke-width="2"/>')
            parts.append(f'<text x="{xpos+67}" y="92" text-anchor="middle" fill="#fff" font-size="16">{label}</text>')
            if i < 4:
                parts.append(f'<path d="M{xpos+140} 86 H{xpos+174}" stroke="#ffd400" stroke-width="3" fill="none"/><path d="M{xpos+168} 79 L{xpos+176} 86 L{xpos+168} 93" stroke="#ffd400" stroke-width="3" fill="none"/>')
        return '<svg viewBox="0 0 900 170" role="img" style="width:100%;height:auto">' + ''.join(parts) + '</svg>'

    if kind == "network":
        layers = [[(100,70),(100,145),(100,220)],[(310,45),(310,105),(310,165),(310,225),(310,285)],[(520,70),(520,145),(520,220)]]
        lines = []
        for a in layers[0]:
            for b in layers[1]:
                lines.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#777" stroke-width="1.5" opacity=".65"/>')
        for a in layers[1]:
            for b in layers[2]:
                lines.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#777" stroke-width="1.5" opacity=".65"/>')
        nodes = []
        for layer in layers:
            for cx, cy in layer:
                nodes.append(f'<circle cx="{cx}" cy="{cy}" r="18" fill="#24262c" stroke="#ffd400" stroke-width="3"/>')
        return '<svg viewBox="0 0 620 330" style="width:100%;height:auto">' + ''.join(lines+nodes) + '<text x="100" y="315" fill="#ffd400" text-anchor="middle" font-size="14">Eingabe</text><text x="310" y="315" fill="#ffd400" text-anchor="middle" font-size="14">Verarbeitung</text><text x="520" y="315" fill="#ffd400" text-anchor="middle" font-size="14">Ausgabe</text></svg>'

    if kind == "vectors":
        vals = [0.21, -0.72, 0.48, 0.91, -0.13, 0.36]
        bars = []
        for i, v in enumerate(vals):
            y = 42 + i * 35
            width = abs(v) * 230
            rect_x = 300 - width if v < 0 else 300
            bars.append(f'<text x="20" y="{y+15}" fill="#fff" font-size="14">Dimension {i+1}</text>')
            bars.append(f'<rect x="{rect_x}" y="{y}" width="{width}" height="20" rx="4" fill="#ffd400"/>')
            bars.append(f'<text x="560" y="{y+15}" fill="#bfc1c6" font-size="13">{v:+.2f}</text>')
        return '<svg viewBox="0 0 620 270" style="width:100%;height:auto">' + ''.join(bars) + '<line x1="300" y1="25" x2="300" y2="250" stroke="#aaa" stroke-dasharray="4 4"/></svg>'
    return ""


# --------------------------- STAGE 0: GENERAL INTRO --------------------------
if stage == 0:
    card("WILLKOMMEN IM AI LAB", "Heute schauen wir hinter die Antwort.",
         "Wir stellen einer KI eine Frage zur deutschen Grammatik. Danach verfolgen wir vereinfacht, "
         "wie aus unserer Eingabe eine Antwort wird.")
    st.markdown(diagram_svg("pipeline"), unsafe_allow_html=True)
    st.markdown("""
    <div class="callout"><b>Ein wichtiger Unterschied:</b><br>
    Eine KI versteht Sprache nicht auf dieselbe Weise wie ein Mensch. Menschen haben Erfahrungen,
    Absichten und ein Bewusstsein. Ein Sprachmodell verarbeitet mathematische Darstellungen von Sprache
    und hat während des Trainings statistische Muster gelernt. Menschen haben das System entwickelt
    und trainiert, damit es auf Sprache reagieren kann.</div>
    """, unsafe_allow_html=True)
    st.info("Leitfrage: Woher kommt die Antwort der KI – und wie entsteht sie?")
    st.caption("Sprecher-Notiz: „Die KI wirkt manchmal so, als würde sie wie ein Mensch verstehen. Aber ihr technischer Prozess ist ein anderer.“")

# --------------------------- STAGE 1: QUESTION ------------------------------
elif stage == 1:
    card("STATION 01 · INPUT", "Eine Frage aus dem Kurs",
         "Eine Person aus dem Publikum entscheidet, was die KI erklären soll.")
    entered_question = st.text_input(
        "Frage über die deutsche Sprache",
        value=st.session_state.question,
        placeholder="Zum Beispiel: Wie unterscheidet man Hauptsatz und Nebensatz?",
    )
    if entered_question != st.session_state.question:
        st.session_state.question = entered_question
        st.session_state.answer = ""
        st.session_state.error = ""
        st.session_state.usage = None
    st.markdown('<div class="callout">Was passiert hier? <b>Der Mensch formuliert eine Anfrage.</b> Diese Eingabe nennt man Prompt.</div>', unsafe_allow_html=True)
    st.caption("Sprecher-Notiz: „Die KI beginnt nicht von allein. Sie erhält zuerst eine Eingabe – unseren Prompt.“")
    if not entered_question.strip():
        st.warning("Gib eine Frage ein, bevor du zu den nächsten Stationen gehst.")

# --------------------------- STAGE 2: TOKENIZATION --------------------------
elif stage == 2:
    q = question or "Wie unterscheidet man Hauptsatz und Nebensatz?"
    chunks = illustrative_tokens(q)
    card("STATION 02 · TOKENISIERUNG", "Der Text wird in kleinere Einheiten zerlegt",
         "Ein Sprachmodell verarbeitet Text als Folge von Tokens. Ein Token kann ein ganzes Wort, ein Wortteil oder ein Satzzeichen sein.")
    st.markdown("**Die aktuelle Publikumsfrage als anschauliche Aufteilung:**")
    st.markdown("".join(f'<span class="token">{html.escape(t)}</span>' for t in chunks), unsafe_allow_html=True)
    st.markdown(diagram_svg("pipeline"), unsafe_allow_html=True)
    st.warning("Wichtig: Diese Aufteilung ist eine didaktische Annäherung mit einer einfachen Python-Regel. Sie ist NICHT die echte Token-Aufteilung von Gemini.")
    st.caption("Sprecher-Notiz: „Die Tokenisierung zerlegt die Eingabe in kleinere Einheiten. So wird der Text für die nächsten Rechenschritte vorbereitet.“")

# --------------------------- STAGE 3: NUMERICAL REPRESENTATION --------------
elif stage == 3:
    q = question or "Wie unterscheidet man Hauptsatz und Nebensatz?"
    chunks = illustrative_tokens(q)
    preview = chunks[:4]
    token_html = " ".join(f'<span class="token">{html.escape(t)}</span>' for t in preview)
    card("STATION 03 · ZAHLEN & VEKTOREN", "Tokens werden numerisch dargestellt",
         "Tokens werden zunächst Token-IDs zugeordnet. Diese IDs dienen als Schlüssel, um gelernte Embedding-Vektoren abzurufen.")
    st.markdown("**Einige Tokens aus unserer aktuellen Frage:**")
    st.markdown(token_html, unsafe_allow_html=True)
    st.markdown("""
    <div class="flow">
      <div class="flowbox">Token<br><b class="yellow">Text-Einheit</b></div><div class="arrow">→</div>
      <div class="flowbox">Token-ID<br><b class="yellow">ganze Zahl</b></div><div class="arrow">→</div>
      <div class="flowbox">Embedding<br><b class="yellow">Zahlenvektor</b></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(diagram_svg("vectors"), unsafe_allow_html=True)
    st.caption("Die gezeigten Balken und Zahlen sind erfundene Beispiele. Token-IDs und echte Gemini-Embeddings werden hier nicht ausgelesen.")
    st.markdown('<div class="callout"><b>Einfach gesagt:</b> Der Text wird in mathematische Darstellungen überführt. Ein Vektor ist eine geordnete Liste von Zahlen, mit der das Modell Muster und Beziehungen verarbeiten kann.</div>', unsafe_allow_html=True)
    st.caption("Sprecher-Notiz: „Die Zahlen sind nicht einfach nur eine Übersetzung in Nullen und Einsen. Das Modell verwendet Token-IDs und komplexe Zahlenvektoren.“")

# --------------------------- STAGE 4: NEURAL NETWORK ------------------------
elif stage == 4:
    q = question or "Wie unterscheidet man Hauptsatz und Nebensatz?"
    words = [w for w in illustrative_tokens(q) if re.search(r"\w", w)]
    card("STATION 04 · NEURONALES NETZ", "Das Modell verarbeitet den Zusammenhang",
         "Ein großes Sprachmodell besteht aus vielen trainierten Rechenschichten. Bei Transformer-Modellen hilft insbesondere der Mechanismus Attention, den Kontext zu berücksichtigen.")
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown(diagram_svg("network"), unsafe_allow_html=True)
    with right:
        st.markdown("""
        **Was bedeutet Attention?**

        Das Modell berechnet, welche Teile des bisherigen Textes für die Verarbeitung anderer Teile besonders relevant sind.

        Es berücksichtigt also nicht nur einzelne Wörter isoliert, sondern auch ihre Beziehungen im Kontext.

        **Warum ist das wichtig?**

        Die Bedeutung eines Wortes hängt oft davon ab, welche anderen Wörter im Satz stehen.
        """)
        st.markdown('<div class="callout"><b>Unsere Frage:</b><br>' + html.escape(q) + '</div>', unsafe_allow_html=True)
    st.markdown("**Einige Wörter, deren Zusammenhang die KI berücksichtigen muss:**")
    st.markdown("".join(f'<span class="token">{html.escape(w)}</span>' for w in words[:12]), unsafe_allow_html=True)
    st.warning("Die Grafik ist ein vereinfachtes Schaubild. Sie zeigt nicht die tatsächliche interne Architektur oder Attention-Werte von Gemini.")
    st.caption("Sprecher-Notiz: „Das neuronale Netz verarbeitet die Zahlen in vielen Schichten. Attention hilft, wichtige Beziehungen im gesamten Kontext zu berücksichtigen. Das ist mathematische Verarbeitung, kein menschliches Bewusstsein.“")

# --------------------------- STAGE 5: KNOWLEDGE ------------------------------
elif stage == 5:
    q = question or "Wie unterscheidet man Hauptsatz und Nebensatz?"
    card("STATION 05 · WOHER KOMMT DAS WISSEN?", "Der wichtigste Teil: Training, Wissen und Fehler",
         "Die Antwort entsteht nicht dadurch, dass Gemini in diesem Moment automatisch ein bestimmtes Grammatikbuch aufschlägt.")
    st.markdown("""
    <div class="flow">
      <div class="flowbox">Trainingsdaten<br><span class="small">z. B. Texte und andere Daten</span></div>
      <div class="arrow">→</div>
      <div class="flowbox">Training<br><span class="small">Muster werden gelernt</span></div>
      <div class="arrow">→</div>
      <div class="flowbox">Parameter<br><span class="small">Zahlen / Modellgewichte</span></div>
    </div>
    """, unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        st.markdown("""
        <div class="lab-card"><div class="eyebrow">VOR UNSERER FRAGE</div><h3>Training</h3>
        <p>Während des Trainings werden sehr viele Modellparameter angepasst. Das Modell lernt statistische Muster
        aus seinen Trainingsdaten: zum Beispiel sprachliche Strukturen, typische Formulierungen und Zusammenhänge.</p>
        <p>Das Gelernte ist in den trainierten Parametern verteilt gespeichert – nicht als einfache Liste von
        Antworten oder als durchsuchbares Wörterbuch.</p></div>
        """, unsafe_allow_html=True)
    with b:
        st.markdown("""
        <div class="lab-card"><div class="eyebrow">WÄHREND UNSERER ANFRAGE</div><h3>Prompt + Kontext</h3>
        <p>Unsere Frage liefert den aktuellen Kontext. Das Modell verarbeitet diesen Kontext mithilfe seiner
        trainierten Parameter und erzeugt daraus eine passende Fortsetzung.</p>
        <p>Eine zusätzliche Websuche oder ein Nachschlagen in einer bestimmten Quelle passiert nur, wenn ein
        entsprechendes Werkzeug tatsächlich eingebunden und verwendet wird.</p></div>
        """, unsafe_allow_html=True)
    st.markdown('<div class="callout"><b>Die kurze Antwort auf „Woher weiß Gemini das?“</b><br>'
                'Aus Mustern und Zusammenhängen, die das Modell während des Trainings aus großen Datenmengen gelernt hat. '
                'Bei unserer Anfrage nutzt es dieses Gelernte zusammen mit dem Prompt und dem Gesprächskontext.</div>',
                unsafe_allow_html=True)
    st.subheader("Warum kann die Antwort richtig oder falsch sein?")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **Warum eine Antwort richtig sein kann**
        - Trainingsdaten enthalten viele korrekte Beispiele.
        - Das Modell hat wiederkehrende Sprachmuster gelernt.
        - Die Frage liefert einen klaren Kontext.
        """)
    with c2:
        st.markdown("""
        **Warum eine Antwort falsch sein kann**
        - Trainingsdaten können Fehler oder Widersprüche enthalten.
        - Die Frage kann unklar oder mehrdeutig sein.
        - Das Modell kann eine plausible, aber falsche Fortsetzung erzeugen.
        - Wissen kann unvollständig oder veraltet sein.
        """)
    st.warning("Wir können aus einer einzelnen Antwort normalerweise nicht erkennen, welches konkrete Trainingsdokument sie beeinflusst hat. Das Modell zeigt uns auch nicht seine vollständigen internen Berechnungen. Eine überzeugend klingende Antwort ist deshalb nicht automatisch korrekt.")
    st.markdown("**Die Frage aus unserem Experiment:**")
    st.markdown(f'<div class="lab-card">{html.escape(q)}</div>', unsafe_allow_html=True)
    st.caption("Sprecher-Notiz: „Das ist der Kern: Das Modell hat beim Training Muster gelernt. Bei unserer Frage kombiniert es dieses Gelernte mit dem aktuellen Kontext. Es kann trotzdem Fehler machen, weil es keine Garantie auf Wahrheit hat.“")

# --------------------------- STAGE 6: GENERATION ----------------------------
elif stage == 6:
    q = question or "Wie unterscheidet man Hauptsatz und Nebensatz?"
    card("STATION 06 · GENERIERUNG", "Die Antwort entsteht Schritt für Schritt",
         "Das Modell berechnet, welche Tokens als Nächstes zum bisherigen Kontext passen könnten. Dann wird ein Token ausgewählt und der Vorgang wiederholt.")
    st.markdown("""
    <div class="flow">
      <div class="flowbox">Bisheriger Kontext</div><div class="arrow">→</div>
      <div class="flowbox">Mögliche nächste Tokens</div><div class="arrow">→</div>
      <div class="flowbox">Auswahl eines Tokens</div><div class="arrow">↻</div>
      <div class="flowbox">Kontext wird länger</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("**Unser Prompt wird dabei als Kontext verwendet:**")
    st.markdown(f'<div class="lab-card">{html.escape(q)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="callout"><b>Wichtig:</b> Das Modell sagt nicht unbedingt einen vollständigen Satz auf einmal voraus. Es erzeugt eine Folge von Tokens, bis die Antwort beendet ist.</div>', unsafe_allow_html=True)
    st.info("Die konkreten Wahrscheinlichkeiten und internen Auswahlwerte von Gemini werden in dieser Präsentation nicht angezeigt. Eine Zahlenverteilung wäre hier nur ein erfundenes Lehrbeispiel.")
    st.caption("Sprecher-Notiz: „Das Modell erzeugt die Antwort Token für Token. Mit jedem neuen Token verändert sich der Kontext für den nächsten Schritt.“")

# --------------------------- STAGE 7: GEMINI OUTPUT -------------------------
elif stage == 7:
    q = question
    card("STATION 07 · OUTPUT", "Jetzt stellen wir die Frage an Gemini",
         "Die vorherigen Stationen haben die Grundprinzipien erklärt. Jetzt sehen wir die tatsächliche Antwort der API.")
    if not q:
        st.warning("Bitte gehe zuerst zu Station 01 und gib eine Frage ein.")
    else:
        st.markdown(f"**Unsere Frage:** {html.escape(q)}")
        api_key = ""
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
        if not api_key:
            api_key = st.text_input(
                "Gemini API-Key",
                type="password",
                help="Der Schlüssel wird nur für diese Anfrage verwendet. Nicht in den Code schreiben.",
            )
        if st.button("⚡ Gemini-Antwort generieren", use_container_width=True):
            if not api_key:
                st.error("Bitte gib zuerst deinen Gemini API-Key ein.")
            else:
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    model_name = "gemini-2.5-flash"
                    prompt = (
                        "Du bist ein zuverlässiger Deutschlehrer. Beantworte die folgende Frage zur deutschen "
                        "Sprache oder Grammatik auf verständlichem B2-Niveau. "
                        "Strukturiere die Antwort mit einer kurzen Erklärung, den wichtigsten Regeln und "
                        "mindestens einem korrekten Beispiel. Passe den Inhalt genau an die gestellte Frage an. "
                        "Erfinde keine Regeln. Wenn die Frage mehrdeutig ist oder eine falsche Annahme enthält, "
                        "weise ausdrücklich darauf hin. Antworte auf Deutsch.\n\n"
                        "Frage: " + q
                    )
                    st.session_state.answer = ""
                    st.session_state.error = ""
                    st.session_state.usage = None
                    with st.spinner("Gemini verarbeitet den Prompt und generiert Text …"):
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                        )
                    st.session_state.answer = response.text or "Es wurde kein Text zurückgegeben."
                    st.session_state.model_used = model_name
                    usage = getattr(response, "usage_metadata", None)
                    if usage:
                        st.session_state.usage = {
                            "prompt": getattr(usage, "prompt_token_count", None),
                            "output": getattr(usage, "candidates_token_count", None),
                            "total": getattr(usage, "total_token_count", None),
                        }
                except Exception as exc:
                    st.session_state.error = str(exc)

        if st.session_state.error:
            st.error("Die Anfrage ist fehlgeschlagen. Prüfe Internetverbindung, API-Key und Modellzugriff.")
            with st.expander("Technische Details"):
                st.code(st.session_state.error)

        if st.session_state.answer:
            st.markdown('<div class="lab-card"><div class="eyebrow">DIE GENERIERTE ANTWORT</div></div>', unsafe_allow_html=True)
            st.markdown(st.session_state.answer)
            st.markdown("#### Was können wir tatsächlich nachweisen?")
            st.markdown("""
            - **Eingabe:** den Prompt, den wir an Gemini gesendet haben.
            - **Modell:** den verwendeten Modellnamen.
            - **Token-Nutzung:** Die API kann Zähler für Eingabe und Ausgabe zurückgeben.
            - **Nicht sichtbar:** vollständige interne Aktivierungen, Attention-Werte oder die konkrete Herkunft einzelner Trainingsbeispiele.
            """)
            st.caption(f"Verwendetes Modell: {st.session_state.model_used}")
            if st.session_state.usage:
                a, b, c = st.columns(3)
                for col, label, key in [
                    (a, "Eingabe-Tokens", "prompt"),
                    (b, "Ausgabe-Tokens", "output"),
                    (c, "Gesamt", "total"),
                ]:
                    with col:
                        value = st.session_state.usage.get(key)
                        st.markdown(
                            f'<div class="metric"><span class="small">{label}</span>'
                            f'<strong>{value if value is not None else "–"}</strong></div>',
                            unsafe_allow_html=True,
                        )
                st.caption("Diese Zähler stammen aus den API-Metadaten. Sie zeigen Token-Anzahlen, nicht die internen Gedankenschritte des Modells.")
            st.success("Experiment abgeschlossen. Die Antwort wurde von Gemini generiert – nicht aus einer fest eingebauten Musterantwort.")
        elif not st.session_state.error:
            st.info("Gib deinen API-Key ein und klicke auf „Gemini-Antwort generieren“.")

# --------------------------- FOOTER -----------------------------------------
st.markdown("---")
st.caption("AI LAB · Didaktische Vereinfachung. Die Diagramme erklären Prinzipien und zeigen keine internen Live-Daten von Gemini.")
st.caption("Für maximal 15 Minuten: kurze Einführung; besonders viel Zeit für Station 04 (neuronales Netz) und Station 05 (Herkunft des Wissens) einplanen.")
