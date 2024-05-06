import re
import uuid

from config import *
from data_filteration import filter_dataset
from pinecone_db import PineconeDB
from sentence_transformers import SentenceTransformer


def remove_special_characters(text):
    pattern = r'[^a-zA-Z0-9\s]'
    cleaned_text = re.sub(pattern, ' ', text)
    return cleaned_text


def convert_to_lower(df, column_name):
    df[column_name] = df[column_name].str.lower()
    return df


def replace_nan(df, column_name, value):
    df[column_name].fillna(value, inplace=True)
    return df


def remove_extra_whitespace(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def preprocess_dataset():
    data = filter_dataset(dataset_file_path, main_url)
    data = replace_nan(data, "author", "unknown")
    for col in ["name", "author", "category"]:
        data[col] = data[col].apply(lambda x: remove_special_characters(x))
        data[col] = data[col].apply(lambda x: remove_extra_whitespace(x))
        data = convert_to_lower(data, col)
    return data


def embedding_model():
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return model


def prepare_vectors_and_metadata(embed_model, df):
    vectors_and_metadata = []
    for i, row in df.iterrows():
        _id = f"{str(uuid.uuid4())}-{i}"
        text = row["category"] + " " + row["author"] + " " + row['name']
        vector = embed_model.encode([text])[0]
        metadata = {
            "name": row['name'],
            "author": row["author"],
            "book_depository_stars": row["book_depository_stars"],
            "price": row["price"],
            "old_price": row["old_price"],
            "category": row["category"],
            "image_url": row["full_path"]
        }
        vectors_and_metadata.append((_id, vector, metadata))
    return vectors_and_metadata


def ingest_historical_data():
    data = preprocess_dataset()
    for category in filtered_categories:
        category = remove_special_characters(category)
        category = remove_extra_whitespace(category).lower()
        filtered_cat_data = data[data['category'] == category]
        cat_embed_metadata = prepare_vectors_and_metadata(embedding_model(), filtered_cat_data)
        pc = PineconeDB(category.replace(' ', '-'))
        pc.upsert_to_pinecone(cat_embed_metadata)
        print("Successfully created all 5 indexes")
    return True

# if __name__ == '__main__':
# ingest_historical_data()
