from flask import Flask, jsonify, request, render_template
import requests
from io import BytesIO
import os
from celery_utils import make_celery
from tasks import transcribe_and_respond
from dotenv import load_dotenv
from services.messenger import send_messenger, get_messenger_message_payload
from services.openai import generate_gpt_response

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
def on_messenger_webhook():
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
        for event in payload.get("entry", []):
            messaging = event.get("messaging", [])
            for message in messaging:
                process_messenger_message(message)
        return jsonify(success=True), 200


@app.route("/message", methods=["POST"])
def on_messenger_message():
    payload = request.json
    print("Received message: ", payload)
    message_id = payload.get("id", None)
    if not payload["id"]:
        return "Unprocessable message", 400
    message = get_messenger_message_payload(message_id)
    return process_messenger_message(message)


# Should be abstracted to support other messaging platforms
def process_messenger_message(message):
    sender_id = message["sender"]["id"]
    # Check for text messages and respond with GPT
    if message.get("message") and "text" in message["message"]:
        user_message = message["message"]["text"]
        gpt_response = generate_gpt_response(user_message)
        send_messenger(sender_id, gpt_response)

    # Check for audio attachments
    elif message.get("message"):
        attachments = message["message"].get("attachments", [])
        audio_attachment = next(
            (a for a in attachments if a.get("type") == "audio"), None
        )

        if audio_attachment:
            file_url = audio_attachment["payload"]["url"]
            # Generate and send an acknowledgment message
            send_messenger(sender_id, "...")

            # Enqueue the transcription task
            transcribe_and_respond.delay(file_url, sender_id)
        else:
            # Generate and send a message for non-audio attachments using GPT
            non_audio_message = generate_gpt_response("NON_AUDIO_FILE")
            send_messenger(sender_id, non_audio_message)
    return jsonify(success=True), 200


if __name__ == "__main__":
    app.run(debug=True)
