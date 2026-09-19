import argparse
import json
import sys

import db
import config
import adaptation
from agents import manager, reporter_agent


def cmd_analyze(args):
    metadata = json.loads(args.metadata) if args.metadata else {}
    report = manager.analyze_message(
        text=args.text, sender=args.sender, channel=args.channel, metadata=metadata
    )
    print(reporter_agent.pretty_print(report))
    if args.json:
        print("\nJSON:\n" + json.dumps(report, indent=2))
    return report


def cmd_interactive(args):
    print("Intelligent Spam Detection Agent - interactive mode. Ctrl+C to quit.\n")
    print(f"LLM content analysis : {'ON' if config.HAS_LLM else 'OFF (heuristic only)'}")
    print(f"Web evidence search   : {'ON' if config.HAS_TAVILY else 'OFF (heuristic only)'}\n")
    while True:
        try:
            text = input("\nMessage text> ").strip()
            if not text:
                continue
            sender = input("Sender (optional)> ").strip() or None
            channel = input("Channel [email]> ").strip() or "email"
            report = manager.analyze_message(text=text, sender=sender, channel=channel)
            print("\n" + reporter_agent.pretty_print(report))

            fb = input(
                "\nFeedback? [c=correct / p=false_positive / n=false_negative / enter=skip]> "
            ).strip().lower()
            fb_map = {"c": "correct", "p": "false_positive", "n": "false_negative"}
            if fb in fb_map:
                comment = input("Comment (optional)> ").strip()
                result = adaptation.record_feedback(report["decision_id"], fb_map[fb], comment)
                print(f"Feedback recorded. Thresholds now: {result['updated_thresholds']}")
        except KeyboardInterrupt:
            print("\nBye.")
            sys.exit(0)


def cmd_feedback(args):
    result = adaptation.record_feedback(args.decision_id, args.type, args.comment or "")
    print(json.dumps(result, indent=2))


def cmd_stats(args):
    print("Current thresholds:")
    print(json.dumps(db.get_thresholds(), indent=2))
    print("\nTop risky senders:")
    for p in db.all_sender_profiles()[:10]:
        print(f"  {p['sender']:<35} risk={p['risk_score']:.2f}  "
              f"({p['spam_count']}/{p['message_count']} flagged)")
    print("\nTop risky domains:")
    for p in db.all_domain_profiles()[:10]:
        print(f"  {p['domain']:<35} risk={p['risk_score']:.2f}  "
              f"({p['spam_count']}/{p['seen_count']} flagged)")
    print("\nFeedback tally:")
    print(json.dumps(db.feedback_stats(), indent=2))
    print("\nRecent decisions:")
    for d in db.recent_decisions(10):
        print(f"  #{d['id']:<4} {d['label']:<10} risk={d['risk_score']:.2f} "
              f"action={d['action']:<12} sender={d['sender']}")


def build_parser():
    p = argparse.ArgumentParser(description="Intelligent Spam Detection Agent")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="Analyze a single message")
    a.add_argument("--text", required=True)
    a.add_argument("--sender", default=None)
    a.add_argument("--channel", default="email")
    a.add_argument("--metadata", default=None, help="JSON string of extra metadata")
    a.add_argument("--json", action="store_true", help="Also print raw JSON report")
    a.set_defaults(func=cmd_analyze)

    i = sub.add_parser("interactive", help="Interactive REPL mode")
    i.set_defaults(func=cmd_interactive)

    f = sub.add_parser("feedback", help="Record feedback on a past decision")
    f.add_argument("--decision-id", type=int, required=True)
    f.add_argument("--type", required=True, choices=["correct", "false_positive", "false_negative"])
    f.add_argument("--comment", default=None)
    f.set_defaults(func=cmd_feedback)

    s = sub.add_parser("stats", help="Show thresholds, profiles, and recent decisions")
    s.set_defaults(func=cmd_stats)

    return p


def main():
    db.init_db()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
