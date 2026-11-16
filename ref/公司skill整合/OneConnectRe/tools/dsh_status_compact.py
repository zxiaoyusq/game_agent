"""Inspect the two authorized DSH sessions without printing their full histories."""
import json
import argparse
import subprocess
import sys
from pathlib import Path

# DSH public messages may contain emoji, which the Windows legacy console
# encoding cannot represent. Emit UTF-8 consistently even without -X utf8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
HANDOFF = ROOT / "analysis" / "dsh_handoff"
INSPECT = Path.home() / ".codex/skills/dsh-guidance/scripts/dsh_session.py"
SESSIONS = {
    "reverse": "session-f2e79f49-7150-4f0c-88ae-8d7f9a34b729",
    "art": "session-2c2bed39-0b88-42d9-8df8-6224aa2df638",
}
REVIEWED = HANDOFF / "reviewed.json"
OBSERVED = HANDOFF / "observed-status.json"


def reviewed_state():
    if not REVIEWED.exists():
        return {}
    data = json.loads(REVIEWED.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("invalid review state")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true', help='Include latest message excerpt for investigation')
    parser.add_argument('--session', choices=SESSIONS, help='Inspect only one session')
    parser.add_argument('--unread', action='store_true', help='Show bounded excerpts since the reviewed cursor')
    parser.add_argument('--changes', action='store_true', help='Only show meaningful changes since the previous successful check')
    parser.add_argument('--ack', choices=SESSIONS, help='Mark an explicitly reviewed message sequence')
    parser.add_argument('--seq', type=int, help='Exact sequence reviewed in the latest snapshot')
    args = parser.parse_args()
    HANDOFF.mkdir(parents=True, exist_ok=True)
    if bool(args.ack) != (args.seq is not None):
        parser.error('--ack and --seq must be used together')
    if args.changes and (args.full or args.unread or args.ack):
        parser.error('--changes cannot be combined with --full, --unread or --ack')
    try:
        reviewed = reviewed_state()
        observed = json.loads(OBSERVED.read_text(encoding='utf-8-sig')) if args.changes and OBSERVED.exists() else {}
        if not isinstance(observed, dict):
            raise ValueError('invalid observed status')
        if args.ack:
            snapshot = json.loads((HANDOFF / (args.ack + '-latest.json')).read_text(encoding='utf-8-sig'))
            messages = snapshot.get('publicMessages') or []
            if snapshot.get('sessionId') != SESSIONS[args.ack] or not messages or messages[-1].get('seq') != args.seq:
                raise ValueError('sequence does not match latest snapshot')
            if args.seq < reviewed.get(args.ack, -1):
                raise ValueError('review cursor cannot move backwards')
            reviewed[args.ack] = args.seq
            tmp = REVIEWED.with_suffix('.tmp')
            tmp.write_text(json.dumps(reviewed, ensure_ascii=False) + '\n', encoding='utf-8')
            tmp.replace(REVIEWED)
            print(json.dumps({'session': args.ack, 'reviewed_seq': args.seq}, ensure_ascii=False))
            return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 1
    failed = False
    for name, session in SESSIONS.items():
        if args.session and name != args.session:
            continue
        path = HANDOFF / (name + ("-unread.json" if args.unread else "-latest.json"))
        inspect_args = ["--after-seq", str(reviewed.get(name, 0)), "--last-messages", "12"] if args.unread else ["--last-messages", "1"]
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(INSPECT), "inspect", "--session-id",
             session, *inspect_args, "--out", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            failed = True
            print(json.dumps({"session": name, "error": result.stderr[-500:] or
                              result.stdout[-500:], "exit": result.returncode}, ensure_ascii=False))
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if data.get("sessionId") != session:
                raise ValueError("snapshot session ID mismatch")
            live = data.get("live") or {}
            goal = data.get("goal") or {}
            messages = data.get("publicMessages") or []
            latest = messages[-1] if messages else {}
            out = {"session": name, "running": live.get("running"),
                   "available": live.get("agentAvailable"), "queue": live.get("inboxCounts"),
                   "goal_phase": goal.get("phase"), "last_seq": (data.get("lastRecord") or {}).get("seq"),
                   "goal_activation": goal.get("activation"),
                   "message_seq": latest.get("seq"),
                   "reviewed_seq": reviewed.get(name),
                   "new_message": latest.get("seq") is not None and latest.get("seq") > reviewed.get(name, 0)}
            if args.full:
                out["message"] = (latest.get("text") or "")[:300]
            if args.unread:
                out["unread_may_be_truncated"] = len(messages) >= 12
                out["unread"] = [{"seq": m.get("seq"), "role": m.get("role"),
                                  "text": (m.get("text") or "")[:300],
                                  "truncated": bool(m.get("truncated")) or len(m.get("text") or "") > 300}
                                 for m in messages]
            if args.changes:
                # lastRecord advances during ordinary work; track only actionable state.
                current = {key: out[key] for key in ('running', 'available', 'queue',
                           'goal_phase', 'goal_activation', 'message_seq', 'reviewed_seq')}
                previous = observed.get(name)
                changes = current if previous is None else {
                    key: value for key, value in current.items() if previous.get(key) != value}
                if changes:
                    print(json.dumps({'session': name, 'changes': changes,
                                      'new_message': out['new_message']}, ensure_ascii=False))
                observed[name] = current
                tmp = OBSERVED.with_suffix('.tmp')
                tmp.write_text(json.dumps(observed, ensure_ascii=False) + '\n', encoding='utf-8')
                tmp.replace(OBSERVED)
            else:
                print(json.dumps(out, ensure_ascii=False))
        except (OSError, ValueError, TypeError) as exc:
            failed = True
            print(json.dumps({"session": name, "error": str(exc)}, ensure_ascii=False))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
