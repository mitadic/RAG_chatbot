# RAG_chatbot
A chatbot service making use of an LLM API, enhanced with RAG.
## Demo

| ![demo](/assets/demo.gif) |
|:--------------:|
| Here's how to utilize Google's Gemini to not rely on common knowledge and instead focus on the uploaded documents in order to reply: *"Bananas are vegetables. Bananas can attend preschool."* |

## Installation

### Installation steps

1. Clone the repository; enter the created directory.

        git clone https://github.com/mitadic/RAG_chatbot; cd RAG_chatbot

2. Create a virtual environment; activate it.

        python3 -m venv .; source ./bin/activate

3. Install the required packages for the venv.

        pip3 install -r requirements.txt

4. Obtain your personal Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

5. Add your key to your environment

        echo API_KEY=ReplaceThisWithYourKey > .env

> [!NOTE]
> These installation steps portray a generic case on UNIX-like systems (Linux, Mac OS).

### Usage

Run the app.
```bash
python3 app.py
```

Visit the now locally hosted homepage via any browser. Create users, then log in as those users via the 🔒 symbol to simulate conversations with Gemini.
```
https://127.0.0.1:8000
```

If you wish to start over from scratch and initialize a fresh database, delete the files (`.sqlite` and `.index`) in the directory `/data/`. You may want to do so if you lose track of users' passwords, because the emulated "admin" can't delete such users.

## Architecture

### Project features and technologies overview
| Component | Technology |
| --------- | ---------- |
Database | SQLite
Database interaction | sqlalchemy.orm
Endpoint routing | FastAPI
LLM API | Gemini API
Authentication | fastapi.security.OAuth2PasswordBearer
RAG (vector DB embeddings and sim. search) | Faiss
UI | auto-generated Swagger UI

To see all the project dependencies, check out [requirements.txt](/requirements.txt)

### SQLite Database blueprint
![image](/assets/db_design_blueprint.png)

### Components Configuration
The diagram below focuses on the traversal of the Query. Note what is fed into the Query Wrapper before the resulting string is sent to Gemini API.

![image](/assets/query_traversal_diagram.png)

## Feedback

If you have any feedback, feel free to reach out.

| <img src="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png" alt="gh_logo.png" width="15" height="15"/> | <img src="https://cdn3.iconfinder.com/data/icons/web-ui-3/128/Mail-2-512.png" alt="email_icon.jpg" width="15" height="15"/> |
| ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [@mitadic](github.com/mitadic)                                                                                  | `milosgtadic` at yahoo.com                                                                                                       |

## Credits
This has been a final bootcamp project where I've had the good fortune of [Zisis Batzos's](github.com/zisismp4) mentorship. While I've independently set the project targets, this was made possible with the help of Zisis's expertise and guidance which have equiped me with the technical vocabulary and the clarity of mind to limit the app's utility and maximize the extent of my learning about Generative AI. Thank you Zisis!

## License

[CC0 1.0 Universal](/LICENSE)
