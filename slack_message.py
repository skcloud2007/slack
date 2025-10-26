import requests
import sys
import getopt

# Function to send a message to a Slack channel

def send_slack_message(message):
  # simple color based on message keywords
  m = message.lower()
  color = "#36a64f" if any(w in m for w in ["success", "succeeded", "ok", "okay", "passed"]) \
      else "#e01e5a" if any(w in m for w in ["fail", "failed", "error", "critical"]) \
      else "#ffcc00" if any(w in m for w in ["warn", "warning"]) \
      else "#4a154b"  # default Slack purple

  payload = {
    # fallback text (shown in notifications / clients that don't render blocks)
    "text": message,
    # use attachment to get a colored sidebar
    "attachments": [
      {
        "color": color,
        "blocks": [
          {
            "type": "header",
            "text": { "type": "plain_text", "text": "🔔 Notification", "emoji": True }
          },
          {
            "type": "section",
            "fields": [
              { "type": "mrkdwn", "text": "*Status:*\nAuto" },
              { "type": "mrkdwn", "text": "*Environment:*\nDEV" },
              { "type": "mrkdwn", "text": "*Service:*\nslack_message.py" },
              { "type": "mrkdwn", "text": "*Channel:*\n#skm_alerts" }
            ]
          },
          {
            "type": "section",
            "text": { "type": "mrkdwn", "text": f"*Message:*\n{message}" }
          },
          { "type": "divider" },
          {
            "type": "context",
            "elements": [
              { "type": "mrkdwn", "text": "🚀 Sent via Python webhook" }
            ]
          }
        ]
      }
    ]
  }
  response = requests.post(
    "XXXXXXXXXXXXXXXXXXhttps://hooks.slack.com/services/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XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    # headers={"Authorization": "Bearer YOUR_SLACK_BOT_TOKEN"},
    json=payload
  )
  if response.status_code != 200:
    print(f"Error sending message: {response.text}")

def main(argv):

  message = ''

  try:
    opts, args = getopt.getopt(argv, "hm:", ["message="])
  except getopt.GetoptError:
    print('slack_message.py -m <message>')
    sys.exit(2)

  if len(opts) == 0:
    message = 'Hello, World!'

  for opt, arg in opts:
    if opt == '-h':
      print('slack_message.py -m <message>')
      sys.exit()
    elif opt in ("-m", "--message"):
      message = arg
  
  send_slack_message(message)

if __name__ == "__main__":
  main(sys.argv[1:])
