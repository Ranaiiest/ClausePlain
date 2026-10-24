"""Streamlit visual theme for ClausePlain — light main pane, dark sidebar, high contrast."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Source+Sans+3:wght@400;500;600;700&display=swap');

:root {
  --ink: #1b2430;
  --ink-soft: #3b4450;
  --paper: #f6f1e8;
  --card: #fffcf7;
  --accent: #c45c26;
  --accent-dark: #9a3f12;
  --sage: #2f6f5e;
  --line: #e4d9c8;
  --sidebar-bg: #17202b;
  --sidebar-text: #f4efe6;
  --sidebar-muted: #d4cbc0;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
  background: var(--paper) !important;
  color: var(--ink) !important;
  font-family: "Source Sans 3", sans-serif;
}

[data-testid="stHeader"] { background: transparent; }

.block-container {
  padding-top: 1.4rem;
  max-width: 1180px;
}

/* —— Sidebar (dark) —— */
[data-testid="stSidebar"] {
  background: var(--sidebar-bg) !important;
}
[data-testid="stSidebar"] > div:first-child {
  background: var(--sidebar-bg) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] strong {
  color: var(--sidebar-text) !important;
}
/* Inline `code` (model name) sits on a light chip — use dark ink, not sidebar cream. */
[data-testid="stSidebar"] code {
  color: #1b2430 !important;
  background-color: #f4efe6 !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: var(--sidebar-muted) !important;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: var(--sidebar-text) !important;
  opacity: 1 !important;
}
/* Light Streamlit buttons: dark label (sidebar text rules otherwise paint them white). */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button div {
  color: #1b2430 !important;
}

/* —— Main text (do not force color on every div — that fights .hero) —— */
[data-testid="stMain"] p,
[data-testid="stMain"] span,
[data-testid="stMain"] li,
[data-testid="stMain"] label,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
  color: var(--ink) !important;
}
[data-testid="stMain"] .stCaption,
[data-testid="stMain"] small,
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {
  color: var(--ink-soft) !important;
}

[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
  font-family: Fraunces, Georgia, serif;
  letter-spacing: -0.02em;
  color: var(--ink) !important;
}
/* —— Metrics (were invisible light-on-cream) —— */
[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] * {
  color: var(--ink-soft) !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
  color: var(--ink) !important;
}

/* —— Tabs (inactive were nearly invisible) —— */
button[data-baseweb="tab"] {
  color: var(--ink-soft) !important;
  opacity: 1 !important;
}
button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span,
button[data-baseweb="tab"] * {
  color: inherit !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--accent-dark) !important;
  font-weight: 600 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
  background-color: var(--accent) !important;
}

/* —— Chat messages —— */
[data-testid="stChatMessage"],
.stChatMessage {
  background: var(--card) !important;
  border: 1px solid var(--line);
  border-radius: 14px;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
  color: var(--ink) !important;
}

.hero {
  background: linear-gradient(135deg, #17202b 0%, #243447 58%, #2f6f5e 140%);
  color: #f6f1e8 !important;
  padding: 1.6rem 1.8rem 1.4rem;
  border-radius: 22px;
  margin-bottom: 1.2rem;
  box-shadow: 0 18px 40px rgba(23, 32, 43, 0.18);
}
/* Divs not h1 — Streamlit theme paints all headings with dark textColor. */
.hero .hero-title,
[data-testid="stMain"] .hero .hero-title,
[data-testid="stMarkdownContainer"] .hero .hero-title {
  font-family: Fraunces, Georgia, serif !important;
  font-size: 2.15rem !important;
  font-weight: 650 !important;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: #f6f1e8 !important;
  margin: 0 0 0.45rem 0 !important;
}
.hero .hero-sub,
[data-testid="stMain"] .hero .hero-sub,
[data-testid="stMarkdownContainer"] .hero .hero-sub {
  font-size: 1.05rem !important;
  line-height: 1.45;
  color: #e7ddd0 !important;
  max-width: 48rem;
  margin: 0 !important;
}

.privacy-strip {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.85rem 1.1rem;
  margin: 0.8rem 0 1.2rem;
  color: #3b4450 !important;
}
.privacy-strip strong {
  color: var(--ink) !important;
}

.clause-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-left: 4px solid var(--accent);
  border-radius: 14px;
  padding: 0.95rem 1.05rem 0.85rem;
  margin-bottom: 0.75rem;
  color: var(--ink);
}
.clause-card h4 {
  margin: 0 0 0.2rem;
  font-family: Fraunces, Georgia, serif;
  color: var(--ink) !important;
}
.clause-card p, .clause-card blockquote, .clause-card em {
  color: var(--ink) !important;
}
.badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: #f0e3d4;
  color: var(--accent-dark) !important;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  margin-bottom: 0.35rem;
}

div.stButton > button[kind="primary"] {
  background: var(--accent);
  border: none;
  color: white !important;
  font-weight: 600;
  border-radius: 12px;
}
div.stButton > button[kind="primary"]:hover {
  background: var(--accent-dark);
  color: white !important;
}

[data-testid="stFileUploader"] {
  background: var(--card);
  border: 1px dashed #cbbba3;
  border-radius: 16px;
  padding: 0.6rem 0.8rem;
}
</style>
"""
