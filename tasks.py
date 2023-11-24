from celery import shared_task
from services.messenger import send_messenger
from services.openai import transcribe_from_url, generate_gpt_response


@shared_task
def transcribe_and_respond_task(file_url, recipient_id):
    try:
        transcription = transcribe_from_url(file_url)
        if transcription:
            send_messenger(recipient_id, transcription)
        else:
            send_messenger(recipient_id, "Sorry, unable to transcribe the audio.")
    except Exception as e:
        send_messenger(recipient_id, f"Error during transcription: {e}")


@shared_task
def generate_gpt_response_task(prompt, sender_id):
    gpt_response = generate_gpt_response(prompt)
    send_messenger(sender_id, gpt_response)
