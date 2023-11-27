import os

import requests
from dotenv import load_dotenv

from services.email import send_messenger_from_email

base_url = "https://graph.facebook.com/v18.0/"

load_dotenv()
access_token = os.getenv("ACCESS_TOKEN")


def send_messenger(recipient_id, message_text):
    is_enabled = recipient_id == os.getenv("OPEN_MESSENGER_ID")
    url = f"{base_url}/174174782446443/messages"
    params = {"access_token": access_token}
    MAX_MESSAGE_LENGTH = 2000
    # Split the message_text into chunks of MAX_MESSAGE_LENGTH
    for start in range(0, len(message_text), MAX_MESSAGE_LENGTH):
        chunk = message_text[start : start + MAX_MESSAGE_LENGTH]
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": chunk},
            "messaging_type": "RESPONSE",
        }

        # Send each chunk as a separate message
        try:
            if is_enabled:
                response = requests.post(url, json=payload, params=params)
                response.raise_for_status()
            else:
                send_messenger_from_email(recipient_id, chunk)

        except Exception as e:
            print(f"Error in sending messenger: {e}")
            raise


def get_messenger_message_payload(message_id):
    response = requests.get(
        f"{base_url}{message_id}",
        params={"fields": "message,attachments,from", "access_token": access_token},
    )
    response.raise_for_status()
    message_data = response.json()
    message_payload = {
        "sender": {"id": message_data.get("from", {}).get("id")},
        "message": {
            "mid": message_data.get("id"),
            "text": message_data.get("message"),
            "attachments": message_data.get("attachments", {}).get("data", []),
        },
    }

    return message_payload
