from openai import OpenAI
import requests
import os


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
    try:
        # Download the audio file from the URL
        audio_response = requests.get(file_url)
        audio_response.raise_for_status()

        # Define a local file path
        local_file_path = (
            "temp_audio_file.mp4"  # You can use a more dynamic naming scheme
        )

        # Save the file locally
        with open(local_file_path, "wb") as audio_file:
            audio_file.write(audio_response.content)

        # Transcribe the audio file using OpenAI's Audio API
        client = OpenAI()
        with open(local_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )

        # Delete the file after transcription
        os.remove(local_file_path)

        return transcription

    except requests.RequestException as e:
        raise Exception(f"Error fetching file: {e}")
    except Exception as e:
        raise Exception(f"Error processing audio: {e}")
