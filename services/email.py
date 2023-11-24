import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()


# Email credentials
sender_email = os.getenv("SENDER_EMAIL")
receiver_email = os.getenv("RECEIVER_EMAIL")
password = os.getenv("EMAIL_PASSWORD")


def send_messenger_from_email(recipient_id, message_text):
    msg = MIMEText(message_text)
    msg["Subject"] = recipient_id
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.aliceadsl.fr", 587)
        server.starttls()  # Encrypts the email
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.quit()
