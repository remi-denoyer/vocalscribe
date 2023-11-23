from celery import shared_task
from functions import send_messenger, transcribe_from_url


@shared_task
def transcribe_and_respond(file_url, recipient_id):
    try:
        transcription = transcribe_from_url(file_url)
        if transcription:
            send_messenger(recipient_id, transcription)
        else:
            send_messenger(recipient_id, "Sorry, unable to transcribe the audio.")
    except Exception as e:
        send_messenger(recipient_id, f"Error during transcription: {e}")
