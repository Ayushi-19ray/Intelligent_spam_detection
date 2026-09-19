
try:
    import gradio as gr
except ImportError:
    raise SystemExit(
        "Gradio isn't installed. Run:  pip install gradio\n"
        "Or just use the CLI instead:  python main.py interactive"
    )

import json

import db
import config
from agents import manager, reporter_agent
import adaptation

db.init_db()

LAST_DECISION_ID = {"value": None}


def analyze(text, sender, channel, account_age_days, send_rate_per_hour):
    if not text or not text.strip():
        return "Please enter a message to analyze.", "", ""

    metadata = {}
    if account_age_days:
        metadata["account_age_days"] = account_age_days
    if send_rate_per_hour:
        metadata["send_rate_per_hour"] = send_rate_per_hour

    report = manager.analyze_message(
        text=text, sender=sender or None, channel=channel or "email", metadata=metadata
    )
    LAST_DECISION_ID["value"] = report["decision_id"]

    label = report["label"].upper()
    emoji = {"SPAM": "!", "SUSPICIOUS": "⚠️", "HAM": "✅"}.get(label, "")
    headline = (
        f"### {emoji} {label}  —  risk {report['risk_score']:.2f} "
        f"(confidence {report['confidence']:.2f})\n"
        f"**Recommended action:** `{report['recommended_action'].upper()}`"
    )
    reasons_md = "\n".join(f"- {r}" for r in report["top_reasons"]) or "- No strong risk signals found"
    raw_json = json.dumps(report, indent=2)
    return headline, reasons_md, raw_json


def give_feedback(feedback_type, comment):
    decision_id = LAST_DECISION_ID["value"]
    if decision_id is None:
        return "Analyze a message first before giving feedback."
    result = adaptation.record_feedback(decision_id, feedback_type, comment or "")
    return f"Feedback recorded for decision #{decision_id}. Thresholds: {result['updated_thresholds']}"


with gr.Blocks(title="Intelligent Spam Detection Agent") as demo:
    gr.Markdown("Intelligent Spam Detection Agent")
    gr.Markdown(
        f"LLM content analysis: **{'ON' if config.HAS_LLM else 'OFF (heuristic mode)'}** · "
        f"Web evidence search: **{'ON' if config.HAS_TAVILY else 'OFF (heuristic mode)'}**"
    )

    with gr.Row():
        with gr.Column(scale=2):
            text_in = gr.Textbox(label="Message text", lines=6, placeholder="Paste an email / SMS / chat message...")
            with gr.Row():
                sender_in = gr.Textbox(label="Sender (optional)", placeholder="promo@example.tk")
                channel_in = gr.Dropdown(["email", "sms", "chat"], value="email", label="Channel")
            with gr.Row():
                age_in = gr.Number(label="Sender account age (days, optional)", value=None)
                rate_in = gr.Number(label="Send rate / hour (optional)", value=None)
            analyze_btn = gr.Button("Analyze", variant="primary")

        with gr.Column(scale=2):
            headline_out = gr.Markdown()
            reasons_out = gr.Markdown()
            with gr.Row():
                correct_btn = gr.Button("Correct")
                fp_btn = gr.Button("False Positive")
                fn_btn = gr.Button("False Negative")
            comment_in = gr.Textbox(label="Feedback comment (optional)")
            feedback_status = gr.Markdown()
            with gr.Accordion("Raw report (JSON)", open=False):
                json_out = gr.Code(language="json")

    analyze_btn.click(
        analyze,
        inputs=[text_in, sender_in, channel_in, age_in, rate_in],
        outputs=[headline_out, reasons_out, json_out],
    )
    correct_btn.click(lambda c: give_feedback("correct", c), inputs=comment_in, outputs=feedback_status)
    fp_btn.click(lambda c: give_feedback("false_positive", c), inputs=comment_in, outputs=feedback_status)
    fn_btn.click(lambda c: give_feedback("false_negative", c), inputs=comment_in, outputs=feedback_status)

if __name__ == "__main__":
    demo.launch(share=True)
