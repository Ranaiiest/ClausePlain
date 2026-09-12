"""Streamlit visual theme for ClausePlain."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Source+Sans+3:wght@400;500;600;700&display=swap');

:root {
  --ink: #1b2430;
  --paper: #f6f1e8;
  --card: #fffcf7;
  --accent: #c45c26;
  --accent-dark: #9a3f12;
  --sage: #2f6f5e;
  --line: #e4d9c8;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--paper);
  color: var(--ink);
  font-family: "Source Sans 3", sans-serif;
}

[data-testid="stHeader"] { background: transparent; }

.block-container {
  padding-top: 1.4rem;
  max-width: 1180px;
}

[data-testid="stSidebar"] {
  background: #17202b;
}
[data-testid="stSidebar"] * {
  color: #f4efe6 !important;
}
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {
  color: #c9c0b2 !important;
}

h1, h2, h3, .hero-title {
  font-family: Fraunces, Georgia, serif;
  letter-spacing: -0.02em;
}

.hero {
  background: linear-gradient(135deg, #17202b 0%, #243447 58%, #2f6f5e 140%);
  color: #f6f1e8;
  padding: 1.6rem 1.8rem 1.4rem;
  border-radius: 22px;
  margin-bottom: 1.2rem;
  box-shadow: 0 18px 40px rgba(23, 32, 43, 0.18);
}
.hero h1 {
  color: #fff;
  font-size: 2.15rem;
  margin-bottom: 0.35rem;
}
.hero p {
  color: #e7ddd0;
  font-size: 1.05rem;
  max-width: 48rem;
  margin-bottom: 0;
}

.privacy-strip {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.85rem 1.1rem;
  margin: 0.8rem 0 1.2rem;
  color: #3b4450;
}

.clause-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-left: 4px solid var(--accent);
  border-radius: 14px;
  padding: 0.95rem 1.05rem 0.85rem;
  margin-bottom: 0.75rem;
}
.clause-card h4 {
  margin: 0 0 0.2rem;
  font-family: Fraunces, Georgia, serif;
}
.badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: #f0e3d4;
  color: var(--accent-dark);
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  margin-bottom: 0.35rem;
}

div.stButton > button[kind="primary"] {
  background: var(--accent);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: 12px;
}
div.stButton > button[kind="primary"]:hover {
  background: var(--accent-dark);
  color: white;
}

[data-testid="stFileUploader"] {
  background: var(--card);
  border: 1px dashed #cbbba3;
  border-radius: 16px;
  padding: 0.6rem 0.8rem;
}

.stChatMessage {
  background: var(--card);
  border-radius: 14px;
}
</style>
"""
