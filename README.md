# RAG_chatbot
A chatbot service utilising an LLM API, enhanced with RAG.
## Demo

| ![demo](/assets/demo.gif) |
|:--------------:|
| Here's how to utilize Google's Gemini to not rely on common knowledge and instead focus on the uploaded documents in order to reply: *"Bananas are vegetables. Bananas can attend preschool."* |

## Installation

> [!NOTE]
> These installation steps portray a generic case on Linux and Mac OS.

### Installation steps

1. Clone the repository; enter the created directory.

        git clone https://github.com/mitadic/RAG_chatbot; cd RAG_chatbot

2. Create a virtual environment; activate it.

        python -m venv .; source ./bin/activate

3. Install the required packages for the venv.

        pip install -r requirements.txt

4. Obtain your personal Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

5. Add your key to your environment

        echo API_KEY=ReplaceThisWithYourKey > .env

### Usage

Run the app.
```bash
python app.py
```

Visit the now locally hosted service via any browser by c/p the following url. Create users, then log in as those users via the 🔒 symbol to simulate conversations with Gemini.
```
127.0.0.1:8000/docs#
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
The diagram below focuses on the travel path of the Query. Note what is fed into the Query Wrapper before the resulting string is sent to Gemini API.

![image](/assets/query_traversal_diagram.png)

## Feedback

If you have any feedback, feel free to reach out.

| <img src="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png" alt="gh_logo.png" width="15" height="15"/> | <img src="https://cdn3.iconfinder.com/data/icons/web-ui-3/128/Mail-2-512.png" alt="email_icon.jpg" width="15" height="15"/> |
| ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [@mitadic](github.com/mitadic)                                                                                  | `milosgtadic` at yahoo.com                                                                                                       |

## Credits
This has been a final bootcamp project where I've had the good fortune of [Zisis Batzos](github.com/zisismp4)'s mentorship. While I've set the project targets mostly independently, this was made possible with the help of Zisis's expertise and guidance which have equiped me with the technical vocabulary and the clarity of mind to limit the app's utility, for instance by omitting a flashy front-end, and maximize the extent of my learning about Generative AI and the general RAG application design.

| Visual resource | Tool |
| :---- | :---- |
| demo gif | [ffmpeg](https://www.ffmpeg.org/)
| Database diagram | [dbdiagram.io](https://dbdiagram.io/home) |
| Components configuration diagram | [draw.io](https://www.app.diagrams.net/) |

## License

[CC0 1.0 Universal](/LICENSE)
