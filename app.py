from flask import Flask, jsonify, request, render_template
import requests
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
import os

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
            transcription = r.recognize_google(audio, language="fr-FR")

        return transcription

    except requests.RequestException as e:
        raise Exception(f"Error fetching file: {e}")
    except Exception as e:
        raise Exception(f"Error processing audio: {e}")


app = Flask(__name__)


@app.route("/transcribe", methods=["GET"])
def transcribe():
    audio_format = "mp4"

    # Get messageId from query parameter
    message_id = request.args.get("messageId")
    if not message_id:
        return jsonify({"error": "No messageId provided"}), 400

    # Load the access token from .env
    access_token = os.getenv("ACCESS_TOKEN")
    graph_api_url = f"https://graph.facebook.com/v18.0/{message_id}/attachments?access_token={access_token}"

    try:
        # Get the file URL
        response = requests.get(graph_api_url)
        response.raise_for_status()
        file_url = response.json()["data"][0]["file_url"]

        # Check if the file is an mp4
        if audio_format not in file_url:
            return jsonify({"error": "Message format not supported"}), 400

        # Download the audio file from the URL
        audio_response = requests.get(file_url)
        audio_response.raise_for_status()

        # Convert the audio file to WAV format
        audio_stream = BytesIO(audio_response.content)
        original_audio = AudioSegment.from_file(
            audio_stream, format="mp4"
        )  # Format without the dot
        audio_stream = BytesIO()
        original_audio.export(audio_stream, format="wav")

        # Reset the stream position to the beginning for further processing
        audio_stream.seek(0)

        # Initialize the recognizer and transcribe
        r = sr.Recognizer()
        with sr.AudioFile(audio_stream) as source:
            audio = r.record(source)
            transcription = r.recognize_google(audio, language="fr-FR")

        return jsonify({"transcription": transcription})

    except requests.RequestException as e:
        return jsonify({"error": f"Error fetching file: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing audio: {e}"}), 500


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

        # Check for messaging events
        for event in payload.get("entry", []):
            messaging = event.get("messaging", [])
            for message in messaging:
                sender_id = message["sender"]["id"]

                if message.get("message"):
                    # Check if the message contains an attachment of type 'audio'
                    attachments = message["message"].get("attachments", [])
                    audio_attachment = next(
                        (
                            attachment
                            for attachment in attachments
                            if attachment.get("type") == "audio"
                        ),
                        None,
                    )

                    if audio_attachment:
                        file_url = audio_attachment["payload"]["url"]
                        # Send a message acknowledging receipt of the audio
                        send_messenger(
                            sender_id,
                            "Received your vocal message, transcribing now...",
                        )

                        # Call transcribe function with the audio file URL
                        try:
                            transcription = transcribe_from_url(file_url)
                            if transcription:
                                send_messenger(sender_id, transcription)
                            else:
                                send_messenger(
                                    sender_id, "Sorry, unable to transcribe the audio."
                                )
                        except Exception as e:
                            send_messenger(
                                sender_id, f"Error during transcription: {e}"
                            )
                    else:
                        # For non-audio messages, send a polite refusal
                        send_messenger(
                            sender_id,
                            "I currently only support vocal transcription. Please send an audio message.",
                        )

        return jsonify(success=True), 200


if __name__ == "__main__":
    app.run(debug=True)
