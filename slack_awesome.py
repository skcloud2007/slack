# slack_awesome.py
# Usage examples:
#   python slack_awesome.py -m "Hello from Jenkins"
#   python slack_awesome.py --tile --status FAILURE -m "Unit tests failed"
#   python slack_awesome.py --file build.log -m "Uploading build log"
#
# Env (choose ONE method):
#   1) Incoming Webhook:
#      SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"
#   2) Bot Token API:
#      SLACK_BOT_TOKEN="xoxb-..."  and  SLACK_CHANNEL="C0123456789" (or #name)
#
# Optional env Jenkins picks:
#   JOB_NAME, BUILD_NUMBER, BUILD_URL, GIT_BRANCH, GIT_COMMIT

import os, sys, time, json, argparse
import requests

class Slack:
    def __init__(self, webhook=None, token=None, default_channel=None, timeout=12, retries=3):
        self.webhook = webhook
        self.token = token
        self.default_channel = default_channel
        self.timeout = timeout
        self.retries = retries

    # ---------- Low-level ----------
    def _post(self, url, payload, headers=None):
        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                r = requests.post(url, json=payload, headers=headers or {}, timeout=self.timeout)
                if r.status_code == 429:
                    wait = int(r.headers.get("Retry-After", "1"))
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                return r
            except requests.RequestException as e:
                last_err = e
                time.sleep(0.8 * attempt)
        raise SystemExit(f"[Slack] POST failed after {self.retries} retries: {last_err}")

    def _api(self, method, payload):
        if not self.token:
            raise SystemExit("[Slack] SLACK_BOT_TOKEN not set for API call.")
        url = f"https://hooks.slack.com/services/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XXXXXXXXXXXXXXXXXXXXX{method}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        r = self._post(url, payload, headers)
        data = r.json()
        if not data.get("ok"):
            raise SystemExit(f"[Slack] API error: {data.get('error')} | payload={payload}")
        return data

    # ---------- High-level ----------
    def send(self, text=None, channel=None, blocks=None, attachments=None, thread_ts=None, mention=None):
        # mention: None | 'here' | 'channel'
        mention_text = {"here": "<!here> ", "channel": "<!channel> "}.get((mention or "").lower(), "")
        text = (mention_text + (text or "")).strip()

        if self.webhook:
            payload = {}
            if text: payload["text"] = text
            if blocks: payload["blocks"] = blocks
            if attachments: payload["attachments"] = attachments
            # channel override via webhooks depends on your Slack webhook configuration
            self._post(self.webhook, payload)
            return {"ok": True}

        # Bot token path
        ch = channel or self.default_channel
        if not ch:
            raise SystemExit("[Slack] channel not set. Provide --channel or SLACK_CHANNEL.")
        payload = {"channel": ch}
        if text: payload["text"] = text
        if blocks: payload["blocks"] = blocks
        if attachments: payload["attachments"] = attachments
        if thread_ts: payload["thread_ts"] = thread_ts
        return self._api("chat.postMessage", payload)

    def upload_file(self, file_path, channel=None, initial_comment=None, thread_ts=None):
        if not self.token:
            raise SystemExit("[Slack] File upload requires SLACK_BOT_TOKEN.")
        ch = channel or self.default_channel
        if not ch:
            raise SystemExit("[Slack] channel not set for file upload.")
        url = "https://slack.com/api/files.upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        files = {"file": open(file_path, "rb")}
        data = {"channels": ch}
        if initial_comment: data["initial_comment"] = initial_comment
        if thread_ts: data["thread_ts"] = thread_ts

        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                r = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
                if r.status_code == 429:
                    wait = int(r.headers.get("Retry-After", "1"))
                    time.sleep(wait); continue
                r.raise_for_status()
                j = r.json()
                if not j.get("ok"):
                    raise SystemExit(f"[Slack] Upload error: {j.get('error')}")
                return j
            except requests.RequestException as e:
                last_err = e
                time.sleep(0.8 * attempt)
        raise SystemExit(f"[Slack] Upload failed after {self.retries} retries: {last_err}")

# ---------- Helpers ----------
STATUS_COLOR = {
    "SUCCESS": "good",
    "FAILURE": "#e01e5a",
    "UNSTABLE": "#ffcc00",
    "ABORTED": "#9e9e9e",
    "INFO": "#4a154b",
}

def build_tile(title, fields_map, context_lines=None):
    fields = []
    for k, v in fields_map.items():
        if v is None: v = "N/A"
        fields.append({"type": "mrkdwn", "text": f"*{k}:*\n{v}"})
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": title, "emoji": True}},
        {"type": "section", "fields": fields[:10]},  # Slack shows up to 10 fields nicely
    ]
    if context_lines:
        blocks += [{"type": "divider"},
                   {"type": "context", "elements": [{"type": "mrkdwn", "text": line} for line in context_lines]}]
    return blocks

def jenkins_info():
    return {
        "Job": os.getenv("JOB_NAME"),
        "Build": f"#{os.getenv('BUILD_NUMBER')}" if os.getenv("BUILD_NUMBER") else None,
        "Status": os.getenv("BUILD_STATUS") or os.getenv("CURRENT_RESULT") or None,
        "Branch": os.getenv("GIT_BRANCH"),
        "Commit": os.getenv("GIT_COMMIT")[:8] if os.getenv("GIT_COMMIT") else None,
        "Link": f"<{os.getenv('BUILD_URL')}|Open>" if os.getenv("BUILD_URL") else None,
    }

def main():
    ap = argparse.ArgumentParser(description="Send rich Slack messages (tiles/text) and files.")
    ap.add_argument("-m", "--message", default="Hello from Jenkins!")
    ap.add_argument("--channel", help="Channel ID or #name (Bot token route).")
    ap.add_argument("--tile", action="store_true", help="Send a Block Kit tile.")
    ap.add_argument("--status", default="INFO",
                    choices=["SUCCESS","FAILURE","UNSTABLE","ABORTED","INFO"],
                    help="Status to color the card.")
    ap.add_argument("--mention", choices=["here","channel","none"], default="none")
    ap.add_argument("--file", help="Upload a file after sending the message.")
    ap.add_argument("--title", default="🔔 Jenkins Notification")
    args = ap.parse_args()

    slack = Slack(
        webhook=os.getenv("SLACK_WEBHOOK_URL"),
        token=os.getenv("SLACK_BOT_TOKEN"),
        default_channel=os.getenv("SLACK_CHANNEL"),
        timeout=15, retries=4
    )

    color = STATUS_COLOR.get(args.status.upper(), STATUS_COLOR["INFO"])

    # Build payload
    blocks = attachments = None
    if args.tile:
        info = jenkins_info()
        # Override/status source of truth for the tile
        if args.status and args.status != "INFO":
            info["Status"] = args.status
        blocks = build_tile(
            title=args.title,
            fields_map=info,
            context_lines=[args.message] if args.message else None
        )
        # Colored sidebar via attachment (Slack's color is via attachments)
        attachments = [{"color": color}]

    # Send message
    res = slack.send(
        text=None if args.tile else args.message,
        blocks=blocks,
        attachments=attachments,
        channel=args.channel,
        mention=None if args.mention == "none" else args.mention
    )
    ts = res.get("ts") if isinstance(res, dict) else None

    # Optional file upload
    if args.file:
        slack.upload_file(args.file, channel=args.channel, initial_comment="↗️ Attached file", thread_ts=ts)

if __name__ == "__main__":
    main()
