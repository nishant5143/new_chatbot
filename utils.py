import json
import re
import os
import pandas as pd


def extract_book_details(chat_history):
    text = chat_history[0]['content']
    pattern = r'\[(Category|category): ([\w-]+), (Book Name|book_name): ([\w\s]+), (Author Name|author_name): ([\w\s]+)\]'

    match = re.search(pattern, text)

    if match:
        data = {
            'category': match.group(2).lower(),
            'book_name': match.group(4).lower(),
            'author_name': match.group(6).lower()
        }
        return True, data
    else:
        return False, "No match found"


def extract_json(chat_history):
    text = chat_history[0]['content']
    start = text.find('{')
    end = text.rfind('}') + 1

    # Extract the JSON string
    json_str = text[start:end]
    try:
        data = json.loads(json_str)
        return True, data
    except Exception as e:
        return False, "No match found"


def update_book_recommendation(data):
    file_name = "book_recommendation.csv"

    if os.path.exists(file_name):
        existing_df = pd.read_csv(file_name)
    else:
        existing_df = pd.DataFrame(columns=['category', 'book_name', 'author_name'])

    new_df = pd.DataFrame([data])

    updated_df = pd.concat([existing_df, new_df], ignore_index=True)

    updated_df.to_csv(file_name, index=False)
    print("Data entry to csv file successful")
