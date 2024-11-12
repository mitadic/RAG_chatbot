# RAG_chatbot
A chatbot service utilising an LLM API, enhanced with RAG.

![image](https://github.com/user-attachments/assets/38a7a3eb-c931-4d24-bc79-04ba56bb57d2)

<img width="692" alt="image" src="https://github.com/user-attachments/assets/6d6224c3-a19a-4292-9ec0-bc9aa57088f4">

## Project features and technologies overview
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

## Installation

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

## Usage/Examples

Run the app.
```bash
python3 app.py
```

Visit the now locally hosted homepage via any browser.
```
https://127.0.0.1:8000
```

> [!NOTE]
> If you wish to start over from scratch and initialize a fresh database, delete the files (`.sqlite` and `.index`) in the directory `data/`

## Feedback

If you have any feedback, feel free to reach out.

| <img src="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png" alt="gh_logo.png" width="15" height="15"/> | <img src="https://cdn3.iconfinder.com/data/icons/web-ui-3/128/Mail-2-512.png" alt="email_icon.jpg" width="15" height="15"/> |
| ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [@mitadic](github.com/mitadic)                                                                                  | `milosgtadic` at yahoo.com                                                                                                       |


## License

[CC0 1.0 Universal](/LICENSE)
