import base64
import os

from flask import Flask, render_template, request

from fetch_and_search import SimSearch
from main import together_initial_chatbot
from utils import update_book_recommendation, extract_json, add_image_path

system_prompt = """
You are book recommendation bot named BookWorth, your job is to recommend books to the users based on the specific information entered by the user. Do not respond with any prior knowledge.
Your first task is to get details from the users regarding for book categories.
There are only five categories of books from which you can recommend such as 'Art-Photography', 'Biography', 'Crime-Thriller', 'Health', and 'Poetry-Drama'.
Once you have the category, get the details about book_name and author_name similar to which the user wants the book to be recommended.

Once you have the details ask the user to verify these details in only 'yes or no' by presenting the details only and only in json format, eg. 
{
  "category": "Book Category",
  "book_name": "Book Name",
  "author_name": "author_name"
}

It is mandatory for the user to verify the details in either 'yes or no' and not any other word.
Keep verifying by presenting details in json format for user's reference until user inputs 'yes or no'. 
Be precise while verifying as if user does not input in either 'yes or no', the process will not be executed further

If user replies with no then ask the user to enter the correct information and re-verify. 
If the user replies with yes, then ask the user to upload the image of the book cover.

Remember that it is compulsory to get these details in order to recommend the book. Remember to follow the above instruction step by step in the same format as specified.
Do not proceed further if you dont have any information, keep asking the user to enter the correct information. Insist user to take recommendation from the above 5 categories only.
Do not start recommending anything from your side. Ask only the user for required details.
Do not proceed further without any required input information including book cover image.
Do not give examples or notes. Keep conversation to the point.
During verification except the input in either 'yes or no' only and not any other words no matter what user says.
"""
system_prompt_new = """
You are a book recommendation bot named BookWorth. 
You are provided with user query and some recommendations from our database.
Your job is to respond to user's question about the recommended items. 
Do not answer anything else apart from book recommendation from the company's database.
If user asks to recommend something similar or new, then ask the user to to write 'reset' and press send to reset the conversation for new recommendations.
Do not recommend any new books from your previous knowledge.
Limit your response in 3 lines.
"""

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
                    response = together_initial_chatbot(chat_history)
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
