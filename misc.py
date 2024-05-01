# @app.route("/chat", methods=["POST"])
# def chat():
#     if request.method == "POST":
#         user_input = request.form["user_input"]
#         messages = [{"role": "user", "content": user_input}]
#         response = chatbot(messages)
#         messages.append({"role": "assistant", "content": messages})
#         bot_response = response.choices[0].message.content
#         return render_template("chat.html", user_input=user_input, bot_response=bot_response)



new_system_prompt = """
            You are an assistant to assess the book price valuation for users from provided database to you.
            Upon the user query, you have to initialize your conversation.
            Your first task is to get details from the users regarding for book categories.
            There are five categories of books you have to consider such as 'Art-Photography', 'Biography', 'Crime-Thriller', 'Health', and 'Poetry-Drama'.
            Remember that its compulsory to get the book category first.
            Then in sub-sequent conversation you have to ask to upload book cover image.
            Give your response in maximum two lines.
"""

condition1 = "upload the cover image"
condition2 = "upload the image"
condition3 = "upload the book cover image"
condition4 = "upload the image of the book cover"
condition5 = "book cover image"