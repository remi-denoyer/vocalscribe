from flask import Flask, jsonify, request, render_template
import requests
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

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


if __name__ == "__main__":
    app.run(debug=True)
