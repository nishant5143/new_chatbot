import pandas as pd
from config import filtered_categories


def process_price_col(val):
    try:
        val = float(val)
    except ValueError:
        val = val.__str__().replace("US$", "")
        val = float(val)
    return val


def filter_dataset(dataset_file_path, main_url):
    df = pd.read_csv(dataset_file_path)

    filtered_df = df[df["category"].isin(filtered_categories)].reset_index(drop=True)

    filtered_df["price"] = filtered_df["price"].str.replace("US$", "")
    filtered_df["price"] = pd.to_numeric(filtered_df["price"])
    filtered_df["old_price"].fillna(df["price"], inplace=True)
    filtered_df["old_price"] = filtered_df["old_price"].apply(
        lambda x: process_price_col(x)
    )

    filtered_df["img_paths"] = filtered_df["img_paths"].str.replace(
        "dataset", "book-covers"
    )

    filtered_df["full_path"] = main_url + "/" + filtered_df["img_paths"]

    cols_to_keep = [
        "name",
        "author",
        "book_depository_stars",
        "price",
        "old_price",
        "category",
        "full_path",
    ]
    filtered_df = filtered_df[cols_to_keep]

    return filtered_df
