import os
import json
import anthropic
import urllib.request
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8995091020:AAHqkFsCAJb5GXsWvRtRIsEiiNuoFjVF0Bc"
CLAUDE_API_KEY     = "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"
TELEGRAM_API       = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id, text):
    url  = f"{TELEGRAM_API}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"[send_message error] {e}")

def get_claude_response(user_message):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=800,
        system="You are Genie 🧞, a friendly and smart AI assistant in a Telegram bot. Be helpful and concise.",
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text

@app.route('/api/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            update = request.get_json()
            if "message" in update:
                message    = update["message"]
                chat_id    = message["chat"]["id"]
                first_name = message.get("from", {}).get("first_name", "Friend")
                text       = message.get("text", "")

                if text == "/start":
                    reply = f"✨ Hello {first_name}! I'm *Genie* 🧞\n\nI'm powered by Claude AI — ask me anything!"
                elif text == "/help":
                    reply = "🧞 *Genie Bot Help*\n\nJust type any message and I'll reply with AI!"
                elif text:
                    reply = get_claude_response(text)
                else:
                    reply = "Please send a text message 😊"

                send_message(chat_id, reply)
        except Exception as e:
            print(f"[webhook error] {e}")
        return jsonify({"ok": True}), 200

    return "<h1>Genie Bot is Running! 🧞</h1>", 200

