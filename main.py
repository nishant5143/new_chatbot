from openai import OpenAI
import os

client = OpenAI()


def chatbot(messages):

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
    )

    return response
