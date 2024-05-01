from flask import Flask, render_template, request
from main import chatbot
from utils import extract_book_details, update_book_recommendation, extract_json

app = Flask(__name__)

system_prompt = """
You are book recommendation bot named BookWorth, your job is to recommend books to the users based on the specific information entered by the user.
Your first task is to get details from the users regarding for book categories.
There are only five categories of books from which you can recommend such as 'Art-Photography', 'Biography', 'Crime-Thriller', 'Health', and 'Poetry-Drama'.
Once you have the category, get the details about book_name and author_name similar to which the user wants the book to be recommended.

Once you have the details ask the user to verify these details in only 'yes or no' by presenting the details only and only in json format, eg. 
{
  "category": "Book Category",
  "book_name": "Book Name",
  "author_name": "author_name"
}
It is mandatory for the user to verify the details in 'yes or no', keep verifying by presenting details in json format until user inputs in required format.

If user replies with no then ask the user to enter the correct information and re-verify. 
If the user replies with yes, then ask the user to upload the image of the book cover.

Remember that it is compulsory to get these details in order to recommend the book. Remember to follow the above instruction step by step in the same format as specified.
Do not proceed further if you dont have any information, keep asking the user to enter the correct information. Insist user to take recommendation from the above 5 categories only.
Do not start recommending anything from your side. Ask only the user for required details.
Do not proceed further without any required input information including book cover image.
"""

chat_history = [{"role": "system", "content": system_prompt}]
image_flag = False


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    global chat_history
    global image_flag

    if request.method == "POST":
        user_input = request.form["user_input"]

        if user_input.lower() == "reset":
            chat_history.clear()
            chat_history.append({"role": "system", "content": system_prompt})
        else:
            if user_input != "":
                chat_history.append({"role": "user", "content": user_input})

            if "image" in request.files and image_flag:
                image_file = request.files["image"]
                print(image_file)

            response = chatbot(chat_history)

            bot_response = response.choices[0].message.content

            if "upload" in bot_response and user_input.lower() == "yes":
                detail_flag, book_details = extract_json(chat_history[-2:])
                if not detail_flag:
                    temp_history = chat_history.append({"role": "assistant", "user": "wrong details"})
                    response = chatbot(temp_history)
                    bot_response = response.choices[0].message.content
                else:
                    update_book_recommendation(book_details)
                    chat_history.append({"role": "assistant", "content": bot_response})
                    image_flag = True
                    return render_template("index.html", chat_history=chat_history[1:])

            chat_history.append({"role": "assistant", "content": bot_response})

        return render_template("index.html", chat_history=chat_history[1:])


if __name__ == "__main__":
    app.run(debug=True)
