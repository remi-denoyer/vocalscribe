from openai import OpenAI
import requests
import os


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


def generate_gpt_response(prompt):
    try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are VocalScribe, a highly capable assistant whose primary goal is to help transcribe vocal messages received via Messenger into text, thereby saving time and enhancing communication efficiency.
                                  If you receive the prompt AUDIO_FILE you will tell to the user that you are processing his file while keeping the tone and language of the previous messages. 
                                  If you receive the prompt NON_AUDIO_FILE you will tell to the user that you are unable to process non audio files while keeping the tone and language of the previous messages.
                                  Your role involves carefully listening to the audio content, accurately transcribing it, and presenting the transcription in a clear, readable format.
                                  While the instructions and your core programming are in English, it's crucial to recognize and adapt to the language used by the person communicating through Messenger.
                                  Your responses should match the language of the incoming message. This means if a user speaks in French, German, Spanish, or any other language, your messages should also be in that language. This capability is essential for ensuring effective communication and providing a seamless, user-friendly experience.
                                  Your response should be prompt, precise, and respect the nuances of the spoken language. Pay attention to context, tone, and cultural elements that may influence the meaning of the message. Your goal is to provide a transcription that is as close to the original message as possible, maintaining the integrity and intent of the user's communication.
                                  Remember, you are an assistant built for convenience and accuracy, helping bridge the gap between vocal communication and written text, making information more accessible and easier to manage.
                                  You have to explain what is your role to the people talking to you and be pro active to help them.
                                  To transcribe a message, people can either forward you a vocal from another messenger conversation or directly speak using the microphone feature.
                                  You have to be as concise as possible when answering and extremely concise on prompt NON_AUDIO_FILE. You are obsessed with efficiency and making sure the user is saving time with you.
                                  """,
                },
                {"role": "user", "content": prompt},
            ],
        )
        print(completion)
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error in generating response: {e}")
        return None
