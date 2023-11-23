from flask import Flask, jsonify, request, render_template
import requests
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment
import os
from celery_utils import make_celery
from dotenv import load_dotenv

# Load environment variables before initializing the app


load_dotenv()

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    CELERY_RESULT_BACKEND=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

celery = make_celery(app)

# Load environment variables
load_dotenv()


def send_messenger(recipient_id, message_text):
    url = "https://graph.facebook.com/v18.0/174174782446443/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE",
    }
    params = {"access_token": os.getenv("ACCESS_TOKEN")}

    response = requests.post(url, json=payload, params=params)
    return response.json()


def transcribe_from_url(file_url):
    audio_format = "mp4"

    try:
        # Download the audio file from the URL
        audio_response = requests.get(file_url)
        audio_response.raise_for_status()

        # Convert the audio file to WAV format
        audio_stream = BytesIO(audio_response.content)
        original_audio = AudioSegment.from_file(audio_stream, format=audio_format)
        audio_stream = BytesIO()
        original_audio.export(audio_stream, format="wav")

        # Reset the stream position to the beginning for further processing
        audio_stream.seek(0)

        # Initialize the recognizer and transcribe
        r = sr.Recognizer()
        with sr.AudioFile(audio_stream) as source:
            audio = r.record(source)
            transcription = r.recognize_google(
                audio, language="fr-FR"
            )

        return transcription

    except requests.RequestException as e:
        raise Exception(f"Error fetching file: {e}")
    except Exception as e:
        raise Exception(f"Error processing audio: {e}")


app = Flask(__name__)


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


@celery.task
def transcribe_and_respond(file_url, recipient_id):
    try:
        transcription = transcribe_from_url(file_url)
        if transcription:
            send_messenger(recipient_id, transcription)
        else:
            send_messenger(recipient_id, "Sorry, unable to transcribe the audio.")
    except Exception as e:
        send_messenger(recipient_id, f"Error during transcription: {e}")


if __name__ == "__main__":
    app.run(debug=True)
