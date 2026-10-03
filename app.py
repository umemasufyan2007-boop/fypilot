import os
import html
import streamlit as st
from dotenv import load_dotenv
from fypilot_crew import generate_plan

load_dotenv()  # Loads the key from the .env file when running locally

st.set_page_config(
    page_title="FYPilot | AI FYP Planner",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Cloud: reads from Streamlit Secrets. Local: reads from the .env file.
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY")


def esc(text):
    # Escapes AI text so it can never break the page layout
    return html.escape(str(text))


def pop_words(text, step=0.07):
    # Wraps each word in a span so the words pop in one after another
    return " ".join(
        f'<span class="pop" style="animation-delay:{i * step:.2f}s">{esc(w)}</span>'
        for i, w in enumerate(text.split())
    )


EXAMPLES = [
    ("🌾 Crop disease detector", "A mobile app that helps farmers detect crop diseases from a photo of a leaf and suggests treatments."),
    ("🎓 Smart attendance", "A classroom attendance system that marks student attendance automatically using face recognition."),
    ("💬 Campus assistant", "A chatbot that answers university students' questions about admissions, fees and schedules using official documents."),
    ("🚦 Traffic monitor", "A computer vision system that detects traffic congestion from camera feeds and suggests alternative routes."),
]


def set_example(text):
    st.session_state["idea"] = text


# ---------- Styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

.stApp div, .stApp p, .stApp label, .stApp button, .stApp textarea, .stApp input,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family: 'Poppins', 'Segoe UI', sans-serif; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes popIn { 0% { opacity: 0; transform: scale(.6) translateY(10px); }
                   70% { transform: scale(1.08); } 100% { opacity: 1; transform: scale(1); } }
.pop { display: inline-block; opacity: 0; animation: popIn .55s cubic-bezier(.34,1.56,.64,1) forwards; }
.nav, .step, .stat, .card, .hero { animation: fadeUp .55s ease backwards; }
.step, .stat, .card { transition: transform .2s ease, box-shadow .2s ease; }
.step:hover, .stat:hover, .card:hover { transform: translateY(-3px); box-shadow: 0 8px 22px rgba(20,184,166,0.18); }

.stApp { background: radial-gradient(circle at top left, #0f2a3d 0%, #07111f 55%); }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stStatusWidget"] { visibility: hidden; }
.block-container { padding-top: 1.2rem; max-width: 1150px; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #0a1626; border-right: 1px solid rgba(255,255,255,0.08); }
.side-brand { font-size: 1.5rem; font-weight: 800; color: #fff; }
.side-brand span { color: #2dd4bf; }
.side-sub { color: #8fa3bd; font-size: .88rem; margin-bottom: .6rem; }
.side-h { color: #5eead4; font-weight: 700; font-size: .95rem; margin: 1.2rem 0 .5rem 0; }
.side-item { color: #c9d6e6; font-size: .88rem; line-height: 1.5; padding: .45rem .7rem; margin-bottom: .4rem;
             background: rgba(255,255,255,0.05); border-left: 3px solid #14b8a6; border-radius: 8px; }
.side-item b { color: #5eead4; }
.side-chip { display: inline-block; padding: .25rem .7rem; margin: 0 .3rem .4rem 0; border-radius: 999px;
             background: rgba(20,184,166,0.15); border: 1px solid rgba(20,184,166,0.4);
             color: #d7f5f2; font-size: .8rem; font-weight: 600; }

/* Navbar and hero */
.nav { display: flex; justify-content: space-between; align-items: center; padding: .8rem 1.2rem;
       margin-bottom: 1.2rem; border-radius: 14px; background: rgba(255,255,255,0.05);
       border: 1px solid rgba(255,255,255,0.1); }
.nav .brand { font-size: 1.35rem; font-weight: 800; color: #fff; }
.nav .brand span { color: #2dd4bf; }
.nav .tag { color: #8fa3bd; font-size: .9rem; }

.hero { padding: 2.6rem 2.2rem; border-radius: 22px; margin-bottom: 1.4rem;
        background: linear-gradient(120deg, #0f766e 0%, #0e7490 55%, #1d4ed8 100%);
        border: 1px solid rgba(255,255,255,0.15); }
.hero h1 { color: #fff; font-size: 2.6rem; font-weight: 800; margin: 0 0 .5rem 0; line-height: 1.2; }
.hero p { color: #d7f5f2; font-size: 1.05rem; margin: 0 0 1rem 0; max-width: 720px; }
.badge { display: inline-block; padding: .3rem .8rem; margin: 0 .4rem .4rem 0; border-radius: 999px;
         background: rgba(255,255,255,0.15); color: #fff; font-size: .85rem; font-weight: 600; }

.steps { display: flex; gap: 1rem; margin-bottom: 1.6rem; flex-wrap: wrap; }
.step { flex: 1; min-width: 220px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px; padding: 1.1rem 1.2rem; }
.step .num { display: inline-block; width: 30px; height: 30px; line-height: 30px; text-align: center;
             border-radius: 50%; background: #14b8a6; color: #04201d; font-weight: 800; margin-bottom: .5rem; }
.step h4 { color: #fff; margin: 0 0 .25rem 0; font-size: 1.05rem; font-weight: 700; }
.step p { color: #a9b8cc; margin: 0; font-size: .92rem; line-height: 1.45; }

.h2 { color: #fff; font-size: 1.35rem; font-weight: 800; margin: 1.2rem 0 .6rem 0; }
.hint { color: #8fa3bd; font-size: .9rem; margin: -.3rem 0 .6rem 0; }

/* Inputs and buttons */
[data-testid="stWidgetLabel"] p { color: #e6edf7 !important; font-weight: 600; font-size: 1rem; }
textarea { background-color: #0e1b2e !important; color: #fff !important;
           border: 1px solid #14b8a6 !important; border-radius: 12px !important; }
textarea::placeholder { color: #8fa3bd !important; }
div[data-baseweb="select"] > div { background-color: #0e1b2e !important; color: #fff !important;
           border: 1px solid #14b8a6 !important; border-radius: 12px !important; }

div.stButton > button, div.stDownloadButton > button { background: linear-gradient(90deg,#0d9488,#0891b2);
           color: #fff; border: none; border-radius: 12px; padding: .7rem 1.8rem; font-weight: 700;
           transition: transform .15s ease; }
div.stButton > button:hover, div.stDownloadButton > button:hover { opacity: .92; color: #fff; border: none;
           transform: translateY(-2px); }
div[class*="st-key-ex_"] button { background: rgba(255,255,255,0.06); border: 1px solid rgba(20,184,166,0.5);
           color: #d7f5f2; font-weight: 600; padding: .55rem .8rem; width: 100%; }
div[class*="st-key-ex_"] button:hover { background: rgba(20,184,166,0.2); }

/* Results */
.stats { display: flex; gap: 1rem; margin: 1rem 0 1.2rem 0; flex-wrap: wrap; }
.stat { flex: 1; min-width: 150px; background: rgba(20,184,166,0.1); border: 1px solid rgba(20,184,166,0.35);
        border-radius: 14px; padding: .9rem 1rem; text-align: center; }
.stat .v { color: #fff; font-size: 1.25rem; font-weight: 800; }
.stat .l { color: #5eead4; font-size: .85rem; font-weight: 600; }

.card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
        border-left: 4px solid #14b8a6; border-radius: 12px; padding: 1rem 1.2rem;
        margin-bottom: .8rem; color: #e6edf7; line-height: 1.55; }
.card .label { color: #5eead4; font-weight: 700; display: block; margin-bottom: .25rem; }
.section-title { color: #5eead4; font-size: 1.15rem; font-weight: 700; margin: 1rem 0 .6rem 0; }
.footer { text-align: center; color: #8fa3bd; font-size: .85rem; margin-top: 2.5rem; padding-bottom: 1rem; }
</style>
""",
    unsafe_allow_html=True,
)


def card(text, icon="", label=None):
    head = f'<span class="label">{esc(label)}</span>' if label else ""
    st.markdown(f'<div class="card">{head}{icon} {esc(text)}</div>', unsafe_allow_html=True)


def title(text):
    st.markdown(f'<div class="section-title">{esc(text)}</div>', unsafe_allow_html=True)


def heading(text):
    st.markdown(f'<div class="h2">{pop_words(text, 0.05)}</div>', unsafe_allow_html=True)


def to_markdown(p):
    md = f"# {p.title}\n\n## Problem Statement\n{p.problem_statement}\n\n## Objectives\n"
    md += "\n".join(f"- {x}" for x in p.objectives)
    md += "\n\n## Key Features\n" + "\n".join(f"- {x}" for x in p.key_features)
    md += "\n\n## Technology Stack\n" + "\n".join(f"- {x}" for x in p.tech_stack)
    md += "\n\n## System Modules\n" + "\n".join(f"- **{m.name}**: {m.description}" for m in p.modules)
    md += "\n\n## Development Roadmap\n"
    for ph in p.roadmap:
        md += f"\n### {ph.phase} ({ph.duration})\n" + "\n".join(f"- {t}" for t in ph.tasks) + "\n"
    md += f"\n## Estimated Timeline\n{p.total_timeline}\n\n## Possible Challenges\n"
    md += "\n".join(f"- {x}" for x in p.challenges)
    return md


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        '<div class="side-brand">🚀 FYP<span>ilot</span></div>'
        '<div class="side-sub">Your AI FYP planning partner</div>'
        '<div class="side-h">💡 Tips for a better plan</div>'
        '<div class="side-item">Mention the <b>problem</b> you want to solve.</div>'
        '<div class="side-item">Say who the <b>users</b> are.</div>'
        '<div class="side-item">Add any <b>technology</b> you already prefer.</div>'
        '<div class="side-h">📦 What you get</div>'
        '<div class="side-item">Refined <b>title</b> and problem statement</div>'
        '<div class="side-item"><b>Objectives</b> and key features</div>'
        '<div class="side-item"><b>Tech stack</b> and system modules</div>'
        '<div class="side-item"><b>Roadmap</b>, timeline and challenges</div>'
        '<div class="side-h">⚙️ Powered by</div>'
        '<span class="side-chip">CrewAI</span><span class="side-chip">Gemini</span>'
        '<span class="side-chip">Streamlit</span>',
        unsafe_allow_html=True,
    )

# ---------- Navbar + Hero ----------
st.markdown(
    '<div class="nav"><div class="brand">🚀 FYP<span>ilot</span></div>'
    '<div class="tag">AI-Powered Final Year Project Planner</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="hero"><h1>{pop_words("Turn your rough FYP idea into a complete project plan")}</h1>'
    '<p>Describe your idea in a sentence or two. FYPilot\'s AI agent builds a refined title, objectives, '
    'tech stack, modules, roadmap and risks in under a minute.</p>'
    '<span class="badge">🤖 CrewAI Agent</span><span class="badge">✨ Gemini</span>'
    '<span class="badge">⚡ Instant Plan</span><span class="badge">⬇️ Downloadable</span></div>',
    unsafe_allow_html=True,
)

# ---------- How it works ----------
heading("How it works")
st.markdown(
    '<div class="steps">'
    '<div class="step"><div class="num">1</div><h4>Enter your idea</h4><p>Write a rough FYP idea and choose your team size and available time.</p></div>'
    '<div class="step"><div class="num">2</div><h4>AI agent plans</h4><p>A CrewAI planning agent analyses the idea and structures a realistic project plan.</p></div>'
    '<div class="step"><div class="num">3</div><h4>Review and download</h4><p>Explore the plan in tabs and download it as a Markdown file.</p></div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------- Input ----------
heading("Plan your project")
st.markdown('<div class="hint">No idea yet? Click an example to try it instantly.</div>', unsafe_allow_html=True)

ex_cols = st.columns(len(EXAMPLES))
for i, (label, text) in enumerate(EXAMPLES):
    ex_cols[i].button(label, key=f"ex_{i}", on_click=set_example, args=(text,))

idea = st.text_area(
    "💡 Enter your FYP idea",
    key="idea",
    placeholder="e.g. A mobile app that helps farmers detect crop diseases from a photo...",
    height=130,
)
col1, col2, _ = st.columns([1, 1, 2])
team_size = col1.selectbox("👥 Team size", [1, 2, 3, 4], index=1)
months = col2.selectbox("⏳ Available months", [3, 4, 6, 8, 10], index=2)

if st.button("✨ Generate Project Plan"):
    api_key = get_api_key()
    if not api_key:
        st.error("API key not found. Check your .env file (local) or Streamlit Secrets (cloud).")
    elif len(idea.strip()) < 15:
        st.warning("Please describe your idea in a bit more detail (at least one or two sentences).")
    else:
        with st.spinner("Your idea is being turned into a project plan... (20-60 seconds)"):
            try:
                st.session_state["plan"] = generate_plan(idea.strip(), api_key, team_size, months)
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ---------- Output ----------
plan = st.session_state.get("plan")
if plan:
    st.success("Your plan is ready! 🎉")
    heading(plan.title)

    stats = [
        ("Timeline", plan.total_timeline),
        ("Phases", len(plan.roadmap)),
        ("Modules", len(plan.modules)),
        ("Features", len(plan.key_features)),
    ]
    stats_html = "".join(f'<div class="stat"><div class="v">{esc(v)}</div><div class="l">{l}</div></div>' for l, v in stats)
    st.markdown(f'<div class="stats">{stats_html}</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📌 Overview", "✅ Requirements", "🛠️ Architecture", "🗺️ Roadmap", "⚠️ Challenges"])

    with tabs[0]:
        card(plan.problem_statement, label="Problem Statement")
        title("Objectives")
        for o in plan.objectives:
            card(o, icon="🎯")

    with tabs[1]:
        title("Key Requirements & Features")
        for f in plan.key_features:
            card(f, icon="✔️")

    with tabs[2]:
        title("Suggested Technology Stack")
        for t in plan.tech_stack:
            card(t, icon="⚙️")
        title("System Modules")
        for m in plan.modules:
            card(m.description, label=m.name)

    with tabs[3]:
        st.info(f"⏱️ Total Estimated Timeline: {plan.total_timeline}")
        for ph in plan.roadmap:
            with st.expander(f"{ph.phase}  •  {ph.duration}", expanded=True):
                for t in ph.tasks:
                    st.markdown(f"- {t}")

    with tabs[4]:
        title("Possible Challenges")
        for c in plan.challenges:
            card(c, icon="⚠️")

    st.download_button("⬇️ Download Plan (Markdown)", to_markdown(plan), file_name="fypilot_plan.md")

st.markdown('<div class="footer">FYPilot • Built with CrewAI, Gemini and Streamlit</div>', unsafe_allow_html=True)