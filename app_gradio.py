try:
    import gradio as gr
except ImportError:
    raise SystemExit(
        "Gradio isn't installed. Run:  pip install gradio\n"
        "Or just use the CLI instead:  python main.py interactive"
    )

import db
import config
from agents import manager

db.init_db()

BRAND_GREEN = "#22C55E"
BRAND_GREEN_SOFT = "#12271B"
BG = "#0B0F14"
SURFACE = "#111823"
SURFACE_RAISED = "#151E2A"
BORDER = "#1E2A36"
TEXT = "#E7ECF1"
TEXT_MUTED = "#8B99A8"
DANGER = "#EF4444"
DANGER_SOFT = "#2A1416"
DANGER_BORDER = "#4A1F22"
WARNING = "#F5A524"
WARNING_SOFT = "#2B2312"
WARNING_BORDER = "#4A3B18"
SAFE_SOFT = "#12251A"
SAFE_BORDER = "#1D4B33"
ACCENT_BLUE = "#3B82F6"

theme = gr.themes.Base(
    primary_hue=gr.themes.colors.emerald,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill=BG,
    body_background_fill_dark=BG,
    background_fill_primary=SURFACE,
    background_fill_primary_dark=SURFACE,
    background_fill_secondary=BG,
    background_fill_secondary_dark=BG,
    border_color_primary=BORDER,
    border_color_primary_dark=BORDER,
    block_background_fill=SURFACE,
    block_background_fill_dark=SURFACE,
    block_border_color=BORDER,
    block_border_color_dark=BORDER,
    block_label_text_color=TEXT_MUTED,
    block_label_text_color_dark=TEXT_MUTED,
    block_title_text_color=TEXT,
    block_title_text_color_dark=TEXT,
    body_text_color=TEXT,
    body_text_color_dark=TEXT,
    body_text_color_subdued=TEXT_MUTED,
    body_text_color_subdued_dark=TEXT_MUTED,
    input_background_fill=BG,
    input_background_fill_dark=BG,
    input_border_color=BORDER,
    input_border_color_dark=BORDER,
    button_primary_background_fill=BRAND_GREEN,
    button_primary_background_fill_dark=BRAND_GREEN,
    button_primary_background_fill_hover="#1CA750",
    button_primary_background_fill_hover_dark="#1CA750",
    button_primary_text_color="#06170D",
    button_primary_text_color_dark="#06170D",
    button_secondary_background_fill=SURFACE_RAISED,
    button_secondary_background_fill_dark=SURFACE_RAISED,
    button_secondary_border_color=BORDER,
    button_secondary_border_color_dark=BORDER,
    button_secondary_text_color=TEXT,
    button_secondary_text_color_dark=TEXT,
    shadow_drop="none",
)

CUSTOM_CSS = f"""
.gradio-container {{ max-width: 1180px !important; margin: 0 auto !important; }}

#app-header {{
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 10px; padding: 6px 2px 18px 2px;
    border-bottom: 1px solid {BORDER}; margin-bottom: 18px;
}}
#app-header h1 {{ font-size: 1.35rem; font-weight: 700; letter-spacing: -0.01em; margin: 0; color: {TEXT}; }}

.status-row {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.status-pill {{
    display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
    border-radius: 999px; font-size: 0.78rem; font-weight: 500;
    border: 1px solid {BORDER}; background: {BG}; color: {TEXT_MUTED}; white-space: nowrap;
}}
.status-pill.on {{ color: {BRAND_GREEN}; border-color: {SAFE_BORDER}; background: {BRAND_GREEN_SOFT}; }}

.section-label {{ font-size: 0.8rem; font-weight: 600; color: {TEXT_MUTED}; margin: 2px 0 8px 2px; }}

.verdict-card {{
    border-radius: 14px; padding: 20px 22px; border: 1px solid {BORDER};
    background: {SURFACE_RAISED}; margin-bottom: 4px;
}}
.verdict-card.spam {{ background: {DANGER_SOFT}; border-color: {DANGER_BORDER}; }}
.verdict-card.suspicious {{ background: {WARNING_SOFT}; border-color: {WARNING_BORDER}; }}
.verdict-card.ham {{ background: {SAFE_SOFT}; border-color: {SAFE_BORDER}; }}

.verdict-title {{ font-size: 1.3rem; font-weight: 700; margin: 0 0 6px 0; color: {TEXT}; }}
.verdict-title.spam {{ color: {DANGER}; }}
.verdict-title.suspicious {{ color: {WARNING}; }}
.verdict-title.ham {{ color: {BRAND_GREEN}; }}

.verdict-meta {{ color: {TEXT_MUTED}; font-size: 0.9rem; margin-bottom: 12px; }}
.risk-meter {{ margin: 10px 0 14px 0; }}
.risk-meter-label {{ margin-top: 6px; font-size: 0.85rem; color: {TEXT_MUTED}; }}
.verdict-action {{ font-size: 0.98rem; font-weight: 500; color: {TEXT}; }}

.score-track {{ flex: 1; height: 6px; border-radius: 999px; background: {BORDER}; overflow: hidden; }}
.score-fill {{ height: 100%; border-radius: 999px; background: {BRAND_GREEN}; }}
.score-fill.med {{ background: {WARNING}; }}
.score-fill.high {{ background: {DANGER}; }}

/* --- Step-by-step workflow --- */
.step-list {{ display: flex; flex-direction: column; gap: 10px; margin-top: 6px; }}
.step-card {{
    display: flex; align-items: flex-start; gap: 14px;
    padding: 14px 16px; border-radius: 12px;
    background: {SURFACE_RAISED}; border: 1px solid {BORDER};
}}
.step-icon {{
    width: 30px; height: 30px; border-radius: 999px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.95rem; background: {BG}; border: 1px solid {BORDER};
}}
.step-icon.ok {{ background: {SAFE_SOFT}; border-color: {SAFE_BORDER}; }}
.step-icon.warn {{ background: {WARNING_SOFT}; border-color: {WARNING_BORDER}; }}
.step-icon.bad {{ background: {DANGER_SOFT}; border-color: {DANGER_BORDER}; }}
.step-body {{ flex: 1; }}
.step-title {{ font-weight: 600; font-size: 0.92rem; color: {TEXT}; margin-bottom: 2px; }}
.step-desc {{ font-size: 0.85rem; color: {TEXT_MUTED}; line-height: 1.5; }}
.step-desc b {{ color: {TEXT}; font-weight: 600; }}

.reason-chip {{
    display: inline-block; padding: 5px 12px; margin: 3px 6px 3px 0;
    border-radius: 8px; background: {SURFACE_RAISED}; border: 1px solid {BORDER};
    font-size: 0.85rem; color: {TEXT};
}}
.link-chip {{
    display: inline-block; padding: 4px 10px; margin: 3px 6px 3px 0;
    border-radius: 6px; background: {SURFACE}; border: 1px solid {BORDER};
    font-size: 0.8rem; font-family: "JetBrains Mono", ui-monospace, monospace; color: {TEXT};
}}

.hero-section {{ padding: 44px 4px 36px 4px; border-bottom: 1px solid {BORDER}; margin-bottom: 28px; }}
.hero-icon {{
    width: 56px; height: 56px; border-radius: 14px; background: {BRAND_GREEN};
    display: flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-bottom: 20px;
}}
.hero-badge {{
    display: inline-block; padding: 6px 14px; border-radius: 999px; font-size: 0.82rem;
    font-weight: 600; color: {ACCENT_BLUE}; background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.35); margin-bottom: 18px;
}}
.hero-title {{ font-size: 2.5rem; line-height: 1.18; font-weight: 800; letter-spacing: -0.01em; margin: 0 0 16px 0; color: {TEXT}; }}
.hero-title .accent {{ color: {BRAND_GREEN}; }}
.hero-subtitle {{ font-size: 1.05rem; line-height: 1.55; color: {TEXT_MUTED}; max-width: 640px; margin: 0 0 22px 0; }}
.hero-checks {{ display: flex; gap: 26px; flex-wrap: wrap; margin-bottom: 28px; font-size: 0.92rem; color: {TEXT}; }}
.hero-checks span {{ color: {BRAND_GREEN}; margin-right: 4px; }}
.hero-cta {{
    display: inline-flex; align-items: center; gap: 8px; padding: 12px 22px; border-radius: 10px;
    background: {BRAND_GREEN}; color: #06170D; font-weight: 700; font-size: 0.95rem; text-decoration: none;
}}
.hero-cta:hover {{ background: #1CA750; }}
"""

LABEL_CLASS = {"SPAM": "spam", "SUSPICIOUS": "suspicious", "HAM": "ham"}
LABEL_ICON = {"SPAM": "\u26d4", "SUSPICIOUS": "\u26a0\ufe0f", "HAM": "\u2705"}
LABEL_TEXT = {"SPAM": "This looks like spam", "SUSPICIOUS": "This looks suspicious", "HAM": "This looks safe"}

ACTION_COPY = {
    "block": "We recommend blocking this sender.",
    "quarantine": "We recommend holding this message for review before it reaches you.",
    "warn": "Proceed with caution \u2014 double check before clicking anything or replying.",
    "allow": "No action needed \u2014 this message looks fine.",
}


def _clean_reason(text):
    """Strip internal source tags so wording stays plain and customer-facing."""
    text = str(text)
    if text.startswith("LLM:"):
        text = text[4:].strip()
        text = text[0].upper() + text[1:] if text else text
    return text


def _level(score):
    if score >= 0.66:
        return "bad", "high"
    if score >= 0.33:
        return "warn", "med"
    return "ok", "low"


def confidence_label(value):
    if value >= 0.8:
        return "High"
    if value >= 0.5:
        return "Medium"
    return "Low"


def render_verdict(report):
    label = str(report.get("label", "")).upper()
    css_class = LABEL_CLASS.get(label, "suspicious")
    icon = LABEL_ICON.get(label, "\u2022")
    display_label = LABEL_TEXT.get(label, "Result unclear")

    risk = max(0.0, min(1.0, float(report.get("risk_score", 0.0) or 0.0)))
    pct = round(risk * 100)
    _, level = _level(risk)
    confidence = confidence_label(float(report.get("confidence", 0.0) or 0.0))

    action = str(report.get("recommended_action", "")).lower()
    action_text = ACTION_COPY.get(action, "We recommend reviewing this message.")

    return f"""
<div class="verdict-card {css_class}">
    <div class="verdict-title {css_class}">{icon} {display_label}</div>
    <div class="risk-meter">
        <div class="score-track"><div class="score-fill {level}" style="width:{pct}%"></div></div>
        <div class="risk-meter-label">{pct}% risk &middot; {confidence} confidence in this result</div>
    </div>
    <div class="verdict-action">{action_text}</div>
</div>
"""


def render_workflow(report):
    """Plain-language, step-by-step breakdown of what was checked and why."""
    scores = report.get("agent_scores") or {}
    reasons = [_clean_reason(r) for r in (report.get("top_reasons") or [])]
    links = report.get("links_found") or []
    evidence = report.get("evidence")

    def bullet_list(items):
        if not items:
            return ""
        return "<br>".join(f"&bull; {i}" for i in items[:3])

    steps = []

    # Step 1 - message wording
        # Step 1 - message wording
    c_score = float(scores.get("content", 0.0) or 0.0)
    icon_cls, _ = _level(c_score)
    # Even a low score can carry a real pattern worth flagging - don't hide it behind a green tick.
    if icon_cls == "ok" and reasons:
        icon_cls = "warn"
    icon = {"ok": "\u2713", "warn": "!", "bad": "\u2715"}[icon_cls]
    if icon_cls == "ok":
        desc = "The wording of this message did not raise concerns."
    else:
        desc = "The wording raised some concerns:<br>" + bullet_list(reasons) if reasons else "The wording raised some concerns."
    steps.append(("Reading the message", desc, icon_cls, icon))

    # Step 2 - links
    if links:
        l_score = float(scores.get("link", 0.0) or 0.0)
        icon_cls, _ = _level(l_score)
        icon = {"ok": "\u2713", "warn": "!", "bad": "\u2715"}[icon_cls]
        chips = "".join(f'<span class="link-chip">{l}</span>' for l in links)
        if icon_cls == "ok":
            desc = f"Found a link, but it did not look unusual:<br>{chips}"
        else:
            desc = f"Found a link that looked unusual:<br>{chips}"
        steps.append(("Checking links", desc, icon_cls, icon))
    else:
        steps.append(("Checking links", "No links were found in this message.", "ok", "\u2713"))

    # Step 3 - sender
    b_score = float(scores.get("behavior", 0.0) or 0.0)
    icon_cls, _ = _level(b_score)
    icon = {"ok": "\u2713", "warn": "!", "bad": "\u2715"}[icon_cls]
    if icon_cls == "ok":
        desc = "The sender did not show any unusual patterns."
    else:
        desc = "The sender showed patterns that are often seen with unwanted messages."
    steps.append(("Checking the sender", desc, icon_cls, icon))

    # Step 4 - online cross-check (only if it actually ran)
    if evidence and evidence.get("available"):
        e_reasons = evidence.get("reasons") or []
        if e_reasons:
            steps.append((
                "Cross-checking online",
                "We searched online and found similar reports:<br>" + bullet_list(e_reasons),
                "bad", "\u2715",
            ))
        else:
            steps.append((
                "Cross-checking online",
                "We searched online and found nothing matching this message.",
                "ok", "\u2713",
            ))

    cards = "".join(
        f"""
        <div class="step-card">
            <div class="step-icon {cls}">{icon}</div>
            <div class="step-body">
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
        </div>
        """
        for title, desc, cls, icon in steps
    )
    return f'<div class="section-label">How we checked this message</div><div class="step-list">{cards}</div>'


def analyze(text, sender, channel, account_age_days, send_rate_per_hour):
    if not text or not text.strip():
        empty = '<div class="verdict-card"><div class="verdict-meta">Please enter a message to check.</div></div>'
        return empty, ""

    metadata = {}
    if account_age_days:
        metadata["account_age_days"] = account_age_days
    if send_rate_per_hour:
        metadata["send_rate_per_hour"] = send_rate_per_hour

    report = manager.analyze_message(
        text=text, sender=sender or None, channel=channel or "email", metadata=metadata
    )

    headline_html = render_verdict(report)
    workflow_html = render_workflow(report)
    return headline_html, workflow_html


with gr.Blocks(title="Message Safety Check", theme=theme, css=CUSTOM_CSS) as demo:
    gr.HTML(
        """
        <div class="hero-section">
            <div class="hero-icon">\U0001F6E1\uFE0F</div>
            <div class="hero-badge">Layered Protection</div>
            <h1 class="hero-title">Message safety check<br>
                <span class="accent">that explains every decision</span></h1>
            <p class="hero-subtitle">
                Every message is checked step by step &mdash; its wording, its links,
                who sent it, and whether it matches known scams online &mdash;
                so you get a clear reason, not just a label.
            </p>
            <div class="hero-checks">
                <span>&#10003;</span>Multiple layers of checking
                <span style="margin-left:26px;">&#10003;</span>Real-time online verification
                <span style="margin-left:26px;">&#10003;</span>Plain-language explanations
            </div>
            <a href="#analyzer" class="hero-cta">\U0001F50D Check a message</a>
        </div>
        """
    )

    llm_on = "on" if config.HAS_LLM else ""
    tavily_on = "on" if config.HAS_TAVILY else ""
    gr.HTML(
        f"""
        <div id="app-header">
            <h1>\U0001F6E1\uFE0F Message Safety Check</h1>
            <div class="status-row">
                <span class="status-pill {llm_on}">{"Deep analysis active" if config.HAS_LLM else "Standard analysis mode"}</span>
                <span class="status-pill {tavily_on}">{"Live web verification active" if config.HAS_TAVILY else "Offline verification mode"}</span>
            </div>
        </div>
        """
    )

    with gr.Row(elem_id="analyzer"):
        with gr.Column(scale=2):
            gr.Markdown('<div class="section-label">Check a message</div>')
            text_in = gr.Textbox(
                label="Message text", lines=6, placeholder="Paste an email / SMS / chat message..."
            )
            with gr.Row():
                sender_in = gr.Textbox(label="Sender (optional)", placeholder="promo@example.tk")
                channel_in = gr.Dropdown(["email", "sms", "chat"], value="email", label="Channel")

            with gr.Accordion("Advanced options (optional)", open=False):
                age_in = gr.Number(label="Sender account age (days)", value=None)
                rate_in = gr.Number(label="Messages sent per hour", value=None)

            analyze_btn = gr.Button("\U0001F50D Check message", variant="primary")

        with gr.Column(scale=3):
            gr.Markdown('<div class="section-label">Result</div>')
            headline_out = gr.HTML()
            workflow_out = gr.HTML()

    analyze_btn.click(
        analyze,
        inputs=[text_in, sender_in, channel_in, age_in, rate_in],
        outputs=[headline_out, workflow_out],
    )

import os

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )