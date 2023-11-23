from flask import Flask, jsonify, request, render_template
import requests
from io import BytesIO
import os
from celery_utils import make_celery
from tasks import transcribe_and_respond
from dotenv import load_dotenv
from functions import send_messenger

load_dotenv()

app = Flask(__name__)
app.config.update(
    broker_url=os.getenv("REDIS_URL"),
    result_backend=os.getenv("REDIS_URL"),
    broker_connection_retry_on_startup=True,
)

celery = make_celery(app)


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@app.route("/terms-of-service")
def terms_of_service():
    return render_template("terms_of_service.html")


@app.route("/messenger", methods=["GET", "POST"])
def messenger_webhook():
    # Verification step for Facebook webhook setup
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if verify_token == os.getenv("WEBHOOK_TOKEN"):
            return challenge, 200
        return "Verification token mismatch", 403

    # Handling POST requests (actual webhook events)
    elif request.method == "POST":
        payload = request.json
        print("Received webhook:", payload)

        # Enqueue transcription tasks without waiting for them to complete
        for event in payload.get("entry", []):
            messaging = event.get("messaging", [])
            for message in messaging:
                sender_id = message["sender"]["id"]
                if message.get("message"):
                    attachments = message["message"].get("attachments", [])
                    audio_attachment = next(
                        (a for a in attachments if a.get("type") == "audio"),
                        None,
                    )

                    if audio_attachment:
                        file_url = audio_attachment["payload"]["url"]
                        # Send an acknowledgment message
                        send_messenger(
                            sender_id,
                            "Received your vocal message, transcribing now...",
                        )

                        # Enqueue the transcription task
                        transcribe_and_respond.delay(file_url, sender_id)
                    else:
                        # For non-audio messages, send a polite refusal
                        send_messenger(
                            sender_id,
                            "I currently only support vocal transcription. Please send an audio message.",
                        )

        return jsonify(success=True), 200


if __name__ == "__main__":
    app.run(debug=True)
