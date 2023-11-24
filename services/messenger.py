import requests
import os
from dotenv import load_dotenv

base_url = "https://graph.facebook.com/v18.0/"

load_dotenv()
access_token = os.getenv("ACCESS_TOKEN")


def send_messenger(recipient_id, message_text):
    url = f"{base_url}/174174782446443/messages"
    params = {"access_token": access_token}
    MAX_MESSAGE_LENGTH = 2000
    responses = []
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
            response = requests.post(url, json=payload, params=params)
            response.raise_for_status()
            responses.append(response.json())
        except Exception as e:
            print(f"Error in sending messenger: {e}")
            raise

    return responses


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
            "attachments": [],
        },
    }
    if "attachments" in message_data:
        message_payload["message"]["attachments"] = [
            {"type": attachment["type"], "payload": attachment["payload"]}
            for attachment in message_data["attachments"]
        ]

    return message_payload
