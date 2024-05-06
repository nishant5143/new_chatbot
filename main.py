from together import Together

client = Together()


def together_initial_chatbot(messages):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3-70b-chat-hf",
        messages=messages,
    )
    return response


def together_recommendation_chatbot(prompt, chat_history):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3-70b-chat-hf",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": chat_history},
        ],
    )

    return response
