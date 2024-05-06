import time

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from data_ingestion import (
    embedding_model,
    remove_extra_whitespace,
    remove_special_characters,
)
from image_embeddings import extract_feature_vector
from pinecone_db import PineconeDB


class SimSearch:

    def __init__(self):
        self.filename = "book_recommendation.csv"

    @staticmethod
    def process_text(text):
        text = remove_special_characters(text)
        text = remove_extra_whitespace(text)
        return text.lower()

    def embed_streaming_data(self):
        df = pd.read_csv(self.filename)
        last_row = df.tail(1)

        # Embed Textual Data
        category = remove_extra_whitespace(last_row["category"][0]).lower()
        author_name = SimSearch.process_text(last_row["author_name"][0])
        book_name = SimSearch.process_text(last_row["book_name"][0])
        text = category + " " + author_name + " " + book_name
        embed_model = embedding_model()
        text_vector = embed_model.encode([text])[0].tolist()

        # Embed Image Data
        image_vector = extract_feature_vector(last_row["image_url"][0])[0].tolist()

        return text_vector, image_vector, category

    def text_similarity_retrieval(self):
        text_vector, image_vector, category = self.embed_streaming_data()
        pc = PineconeDB(category)
        res = pc.query_db(text_vector)
        combined_vectors = text_vector + image_vector
        return res, combined_vectors

    def prepare_results(self):
        start = time.time()
        db_result, combined_vectors = self.text_similarity_retrieval()
        data = []

        for entry in db_result["matches"]:
            image_url = entry["metadata"]["image_url"]
            image_vector = extract_feature_vector(image_url)[0].tolist()
            comb_vec = entry["values"] + image_vector
            data_dict = {
                "entry_id": entry["id"],
                "author": entry["metadata"]["author"],
                "book_depository_stars": entry["metadata"]["book_depository_stars"],
                "name": entry["metadata"]["name"],
                "price": entry["metadata"]["price"],
                "text_similarity_score": entry["score"],
                "image_url": image_url,
                "combined_vectors": comb_vec,
                "combined_similarity_score": SimSearch.calculate_cosine_similarity(
                    combined_vectors, comb_vec
                ),
            }
            data.append(data_dict)
        end = time.time()
        print(
            f"It took {end - start} time to run for {len(db_result['matches'])} entries"
        )
        results_df = pd.DataFrame(data)
        results_df = results_df.sort_values(
            by=["combined_similarity_score"], ascending=False
        )
        results_df = results_df.loc[
            results_df.astype(str)
            .drop_duplicates(subset=["author", "name"], keep="first")
            .index
        ]
        results_df = results_df.head(3)
        results_df = results_df[
            [
                "entry_id",
                "name",
                "author",
                "price",
                "combined_similarity_score",
                "image_url",
            ]
        ]
        return results_df.reset_index(drop=True)

    @staticmethod
    def calculate_cosine_similarity(vector1, vector2):
        # Convert input vectors to numpy arrays
        vector1 = np.array(vector1)
        vector2 = np.array(vector2)

        # Reshape vectors to be 2D arrays
        vector1 = vector1.reshape(1, -1)
        vector2 = vector2.reshape(1, -1)

        # Calculate cosine similarity
        similarity = cosine_similarity(vector1, vector2)

        # Extract similarity value
        similarity_value = similarity[0][0]

        return similarity_value

    def run(self):
        return self.prepare_results()
