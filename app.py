"""
ClausePlain — upload a legal document, get a plain-English briefing, then ask questions.

    streamlit run app.py
"""
from __future__ import annotations

import html
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.limits import (  # noqa: E402
    DocumentTooLongError,
    FileTooLargeError,
    NotLegalDocumentError,
    UploadRejectedError,
    max_file_bytes,
)
from src.product.schemas import ChatTurn, DocumentAnalysis  # noqa: E402
from src.ui.loaders import llm_status, load_config_dict  # noqa: E402
from src.ui.theme import CSS  # noqa: E402
from src.utils.config import load_config  # noqa: E402
from src.utils.ssl_certs import configure_ssl_for_corporate_proxy  # noqa: E402

configure_ssl_for_corporate_proxy()

st.set_page_config(
    page_title="ClausePlain",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading reading models…")
def get_workspace():
    from src.product.workspace import DocumentWorkspace

    return DocumentWorkspace(load_config("configs/config.yaml"))


def _upload_limits():
    cfg = load_config_dict()
    upload = cfg.get("upload") or {}
    from src.utils.config import UploadConfig

    return UploadConfig(**upload)


def _init_state() -> None:
    st.session_state.setdefault("contract_id", None)
    st.session_state.setdefault("doc_title", None)
    st.session_state.setdefault("word_count", 0)
    st.session_state.setdefault("analysis", None)
    st.session_state.setdefault("chat", [])
    st.session_state.setdefault("model_used", "")
    st.session_state.setdefault("analyze_seconds", 0.0)
    st.session_state.setdefault("rejected", False)
    st.session_state.setdefault("rejection_reason", "")


def _analysis() -> DocumentAnalysis | None:
    data = st.session_state.get("analysis")
    if data is None:
        return None
    if isinstance(data, DocumentAnalysis):
        return data
    return DocumentAnalysis.model_validate(data)


def _clear_session() -> None:
    for key in ("contract_id", "doc_title", "analysis", "chat", "model_used"):
        st.session_state[key] = None if key != "chat" else []
    st.session_state.word_count = 0
    st.session_state.rejected = False
    st.session_state.rejection_reason = ""
    st.session_state.nav = "Upload"


def _render_sidebar() -> None:
    cfg = load_config_dict()
    llm_name = (cfg.get("llm") or {}).get("model_name", "openai/gpt-oss-20b")
    ok, detail = llm_status()
    limits = _upload_limits()

    st.sidebar.markdown("### ClausePlain")
    st.sidebar.caption("See what your legal document actually says.")
    st.sidebar.divider()
    st.sidebar.markdown(f"**Status:** {'Ready' if ok else 'Needs API key'}")
    st.sidebar.caption(detail)
    st.sidebar.markdown(f"**Model:** `{llm_name}`")
    st.sidebar.caption(
        f"Max upload: {limits.max_file_mb:g} MB · {limits.max_pages} pages · "
        f"{limits.max_words:,} words"
    )
    st.sidebar.divider()
    st.sidebar.markdown(
        "Your file is processed on this app. Text excerpts are sent to Groq "
        "to generate the briefing and chat answers. We do not sell your documents."
    )
    if st.session_state.contract_id:
        st.sidebar.divider()
        st.sidebar.caption("Current document")
        st.sidebar.write(st.session_state.doc_title)
        st.sidebar.caption(f"{st.session_state.word_count:,} words")
        if st.sidebar.button("Start over"):
            _clear_session()
            st.rerun()


def _hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1>Read any legal document in plain English</h1>
          <p>
            Upload a contract, offer letter, NDA, or court paper. ClausePlain finds the
            important numbers, deadlines, obligations, and conditions, explains the jargon,
            then lets you ask questions grounded in your file.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="privacy-strip">
          <strong>Your documents stay with you.</strong>
          Files are processed in this session. We send only retrieved excerpts to Groq
          for analysis — never to train a public model on our side. This is an explainer,
          not a lawyer. Do not treat it as legal advice.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _run_upload(uploaded) -> None:
    limits = _upload_limits()
    if uploaded.size > max_file_bytes(limits):
        st.error(
            f"This file is {uploaded.size / (1024 * 1024):.1f} MB. "
            f"The limit is {limits.max_file_mb:g} MB."
        )
        return

    suffix = Path(uploaded.name).suffix.lower() or ".pdf"
    status = st.status("Reading your document…", expanded=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name

        workspace = get_workspace()
        status.write("Checking that this is a legal document…")
        result = workspace.analyze_file(tmp_path, size_bytes=uploaded.size)
        if result.rejected:
            st.session_state.rejected = True
            st.session_state.rejection_reason = result.rejection_reason
            st.session_state.contract_id = None
            st.session_state.analysis = None
            status.update(label="Not a legal document", state="error")
            st.error(result.rejection_reason or "Not a legal document.")
            return

        contract = result.contract
        analysis = result.analysis
        st.session_state.rejected = False
        st.session_state.rejection_reason = ""
        st.session_state.contract_id = contract.contract_id
        st.session_state.doc_title = contract.title
        st.session_state.word_count = contract.word_count
        st.session_state.analysis = analysis.model_dump()
        st.session_state.chat = []
        st.session_state.model_used = result.model_name
        st.session_state.analyze_seconds = result.latency_seconds
        st.session_state.nav = "Briefing"
        status.update(label="Briefing ready", state="complete")
        st.rerun()
    except NotLegalDocumentError as exc:
        status.update(label="Not a legal document", state="error")
        st.session_state.rejected = True
        st.session_state.rejection_reason = exc.reason
        st.error(str(exc))
    except (FileTooLargeError, DocumentTooLongError, UploadRejectedError) as exc:
        status.update(label="Upload rejected", state="error")
        st.error(str(exc))
    except Exception as exc:
        status.update(label="Could not read this file", state="error")
        st.error(str(exc))
        st.caption("Use a text-based PDF (not a scanned image) or a .txt file.")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def page_upload() -> None:
    _hero()
    limits = _upload_limits()
    if st.session_state.rejected and st.session_state.rejection_reason:
        st.error(st.session_state.rejection_reason)

    col_left, col_right = st.columns([1.15, 0.85], gap="large")
    with col_left:
        st.subheader("Upload")
        uploaded = st.file_uploader(
            "PDF or text file",
            type=["pdf", "txt"],
            label_visibility="collapsed",
        )
        st.caption(
            f"Legal PDFs and .txt only. Limit {limits.max_file_mb:g} MB, "
            f"{limits.max_pages} pages, {limits.max_words:,} words. "
            "Scanned image PDFs are not supported."
        )
        if uploaded is not None:
            if st.button("Explain this document", type="primary"):
                _run_upload(uploaded)
        else:
            st.info("Drop a file to begin. Typical briefing time is under a minute.")

    with col_right:
        st.subheader("What you get")
        st.markdown(
            """
            1. **Overview** — who, what, money, and how it ends  
            2. **Clauses** — important terms with why they matter  
            3. **Money & dates** — amounts, caps, notice, deadlines  
            4. **Obligations & conditions** — who must do what, and when  
            5. **Ask** — chat that answers only from your document
            """
        )


def _clause_html(clause) -> str:
    who_line = f"<p><em>{html.escape(clause.who_it_affects)}</em></p>" if clause.who_it_affects else ""
    why = f"<p><strong>Why it matters:</strong> {html.escape(clause.why_it_matters)}</p>" if clause.why_it_matters else ""
    nums = ""
    if clause.numbers:
        nums = "<p>" + " · ".join(html.escape(n) for n in clause.numbers) + "</p>"
    quote = f"<blockquote>{html.escape(clause.excerpt)}</blockquote>" if clause.excerpt else ""
    return (
        f'<div class="clause-card"><div class="badge">{html.escape(clause.category)}</div>'
        f"<h4>{html.escape(clause.title)}</h4><p>{html.escape(clause.explanation)}</p>"
        f"{why}{who_line}{nums}{quote}</div>"
    )


def page_briefing() -> None:
    analysis = _analysis()
    if analysis is None:
        st.info("Upload a document first.")
        return

    st.title(analysis.title or st.session_state.doc_title or "Document briefing")
    st.caption(
        f"{analysis.document_type} · analyzed in {st.session_state.analyze_seconds:.1f}s "
        f"with `{st.session_state.model_used or 'Groq'}`"
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clauses", len(analysis.clauses))
    m2.metric("Money terms", len(analysis.money_and_numbers))
    m3.metric("Deadlines", len(analysis.timelines))
    m4.metric("Terms explained", len(analysis.legal_terms))

    st.subheader("In plain English")
    st.write(analysis.overview)

    meta_cols = st.columns(2)
    with meta_cols[0]:
        st.markdown("**Parties**")
        st.write(", ".join(analysis.parties) if analysis.parties else "Not stated in the excerpts.")
        if analysis.governing_law:
            st.markdown("**Governing law**")
            st.write(analysis.governing_law)
    with meta_cols[1]:
        st.markdown("**Key dates**")
        if analysis.key_dates:
            for item in analysis.key_dates:
                st.write(f"- {item}")
        else:
            st.write("Not stated in the excerpts.")
        if analysis.dispute_resolution:
            st.markdown("**Disputes**")
            st.write(analysis.dispute_resolution)

    if analysis.watch_outs:
        st.markdown("**Things to notice**")
        for item in analysis.watch_outs:
            st.write(f"- {item}")

    tabs = st.tabs(["Clauses", "Money & dates", "Obligations", "Restrictions", "Glossary"])
    with tabs[0]:
        if not analysis.clauses:
            st.write("No standout clauses were extracted. Try asking in chat.")
        for clause in analysis.clauses:
            st.markdown(_clause_html(clause), unsafe_allow_html=True)
    with tabs[1]:
        if not analysis.money_and_numbers and not analysis.timelines:
            st.write("No amounts or deadlines were extracted. Try asking in chat.")
        for row in analysis.money_and_numbers:
            st.markdown(f"**{row.label}:** {row.amount} — {row.explanation}")
            if row.excerpt:
                st.caption(row.excerpt)
        for row in analysis.timelines:
            st.markdown(f"**{row.label}:** {row.when} — {row.explanation}")
            if row.excerpt:
                st.caption(row.excerpt)
    with tabs[2]:
        if not analysis.obligations and not analysis.conditions:
            st.write("No explicit obligations or conditions were listed.")
        for row in analysis.obligations:
            extra = []
            if row.when_or_how:
                extra.append(row.when_or_how)
            if row.if_they_dont:
                extra.append(f"If they don't: {row.if_they_dont}")
            suffix = f" ({'; '.join(extra)})" if extra else ""
            st.markdown(f"**{row.party}** — {row.must_do}{suffix}")
            if row.excerpt:
                st.caption(row.excerpt)
        for row in analysis.conditions:
            st.markdown(
                f"**{row.title}** — {row.explanation} "
                f"{'Trigger: ' + row.trigger if row.trigger else ''} "
                f"{'Then: ' + row.consequence if row.consequence else ''}"
            )
            if row.excerpt:
                st.caption(row.excerpt)
    with tabs[3]:
        if not analysis.rights_and_restrictions:
            st.write("No explicit rights or restrictions were listed.")
        for row in analysis.rights_and_restrictions:
            st.markdown(f"**{row.kind.title()} · {row.party}** — {row.detail}")
            if row.excerpt:
                st.caption(row.excerpt)
    with tabs[4]:
        if not analysis.legal_terms:
            st.write("No glossary terms were returned.")
        for term in analysis.legal_terms:
            extra = f" *{term.why_it_matters}*" if term.why_it_matters else ""
            st.markdown(f"**{term.term}** — {term.plain_english}{extra}")


def page_ask() -> None:
    if not st.session_state.contract_id:
        if st.session_state.rejected:
            st.error(st.session_state.rejection_reason or "Not a legal document.")
            return
        st.info("Upload a document first, then ask questions about it.")
        return

    st.title("Ask about this document")
    st.caption("Answers are retrieved from your file. If it is not in the text, the assistant will say so.")

    for turn in st.session_state.chat:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])

    question = st.chat_input("Ask anything about this document…")
    if not question:
        return

    st.session_state.chat.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    history = [
        ChatTurn(role=t["role"], content=t["content"])
        for t in st.session_state.chat[:-1]
    ]
    with st.chat_message("assistant"):
        with st.spinner("Looking in the document…"):
            try:
                workspace = get_workspace()
                answer, _ = workspace.ask(
                    st.session_state.contract_id,
                    st.session_state.doc_title or "document",
                    question,
                    history,
                )
            except Exception as exc:
                answer = f"I could not answer just now: {exc}"
        st.write(answer)
    st.session_state.chat.append({"role": "assistant", "content": answer})


def main() -> None:
    _init_state()
    _render_sidebar()
    page = st.sidebar.radio(
        "Navigate",
        ["Upload", "Briefing", "Ask"],
        key="nav",
        label_visibility="collapsed",
    )
    if page == "Upload":
        page_upload()
    elif page == "Briefing":
        page_briefing()
    else:
        page_ask()


main()
