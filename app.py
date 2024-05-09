import base64
import os

from flask import Flask, render_template, request

from fetch_and_search import SimSearch
from main import together_initial_chatbot
from prompts import *
from utils import update_book_recommendation, extract_json, add_image_path

app = Flask(__name__)
chat_history = [{"role": "system", "content": system_prompt}]
recom_chat_history = [{"role": "system", "content": system_prompt_new}]
image_flag = False
result_flag = False
recommendation_bot = False

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def create_upload_folder():
    upload_folder_path = app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_folder_path):
        os.makedirs(upload_folder_path)


create_upload_folder()


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
    return encoded_string


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST", "GET"])
def chat():
    global chat_history
    global image_flag
    global result_flag
    global recommendation_bot
    global recom_chat_history

    if request.method == "GET" and result_flag:
        result_dicts = []
        recom_dict = []
        ss = SimSearch()
        result_df = ss.run()
        for idx, row in result_df.iterrows():
            result_dict = {
                "book_name": row["name"].title(),
                "author_name": row["author"].title(),
                "price": row["price"],
                "image_base64": encode_image_to_base64(row["image_url"]),
            }
            new_result_dict = result_dict.copy()
            result_dicts.append(result_dict)
            new_result_dict.pop("image_base64")
            recom_dict.append(new_result_dict)
        user_query = extract_json(chat_history[-4:])
        result_flag = False
        recommendation_bot = True
        recom_chat = f"User Query = {user_query[1]}, our recommendations = {recom_dict}"
        recom_chat_history.append({"role": "user", "content": recom_chat})
        response = together_initial_chatbot(recom_chat_history)
        recom_bot_response = response.choices[0].message.content
        recom_chat_history.append({"role": "assistant", "content": recom_bot_response})
        chat_history.append({"role": "assistant", "content": recom_bot_response})
        return render_template(
            "index.html", chat_history=chat_history[1:], result_dicts=result_dicts
        )

    if request.method == "POST":
        user_input = request.form["user_input"]

        if user_input.lower() == "reset":
            image_flag = False
            result_flag = False
            recommendation_bot = False
            chat_history.clear()
            chat_history.append({"role": "system", "content": system_prompt})
        else:
            if user_input != "":
                if recommendation_bot:
                    recom_chat_history.append({"role": "user", "content": user_input})

                chat_history.append({"role": "user", "content": user_input})

            if recommendation_bot:
                response = together_initial_chatbot(recom_chat_history)
                recom_bot_response = response.choices[0].message.content
                recom_chat_history.append(
                    {"role": "assistant", "content": recom_bot_response}
                )
                chat_history.append(
                    {"role": "assistant", "content": recom_bot_response}
                )
                return render_template("index.html", chat_history=chat_history[1:])

            if "image" in request.files and image_flag:
                image_file = request.files["image"]
                if image_file.filename == "":
                    temp_chat = chat_history.copy()
                    temp_chat.append(
                        {"role": "user", "content": "image not uploaded successfully"}
                    )
                    response = together_initial_chatbot(temp_chat)
                    bot_response = response.choices[0].message.content
                    chat_history.append({"role": "assistant", "content": bot_response})
                    return render_template("index.html", chat_history=chat_history[1:])

                image_path = os.path.join(
                    app.config["UPLOAD_FOLDER"], image_file.filename
                )
                image_file.save(image_path)
                temp_history = chat_history.copy()
                temp_history.append(
                    {"role": "user", "content": "image uploaded successfully"}
                )
                result_flag = True
                add_image_path(image_path)
                response = together_initial_chatbot(temp_history)
                bot_response = response.choices[0].message.content
                chat_history.append({"role": "assistant", "content": bot_response})
                image_flag = False
                return render_template("index.html", chat_history=chat_history[1:])

            response = together_initial_chatbot(chat_history)

            bot_response = response.choices[0].message.content

            if "upload" in bot_response and user_input.lower() == "yes":
                detail_flag, book_details = extract_json(chat_history[-2:])
                if not detail_flag:
                    temp_history = chat_history.copy()
                    temp_history[-1:] = [
                        {"content": "wrong details entered", "role": "user"}
                    ]
                    response = together_initial_chatbot(temp_history)
                    bot_response = response.choices[0].message.content
                else:
                    update_book_recommendation(book_details)
                    chat_history.append({"role": "assistant", "content": bot_response})
                    image_flag = True
                    return render_template("index.html", chat_history=chat_history[1:])

            chat_history.append({"role": "assistant", "content": bot_response})

        return render_template("index.html", chat_history=chat_history[1:])


if __name__ == "__main__":
    app.run(debug=False)
