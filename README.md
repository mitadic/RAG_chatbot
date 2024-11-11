# RAG_chatbot
A chatbot service utilising an LLM API, enhanced with RAG.

<img width="692" alt="image" src="https://github.com/user-attachments/assets/6d6224c3-a19a-4292-9ec0-bc9aa57088f4">

## Project features and technologies overview
* Database management: sqlalchemy.orm
* Endpoint routing: Fast API
* 3rd party API: Gemini API
* UI: auto-generated Swagger UI

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
python app.py
```

Visit the now locally hosted homepage via any browser.
```
https://127.0.0.1:5000
```

> [!NOTE]
> If you wish to start your own database from scratch, delete the demo file `library.sqlite` in directory `data/`

## Feedback

If you have any feedback, feel free to reach out.

| <img src="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png" alt="gh_logo.png" width="15" height="15"/> | <img src="https://cdn3.iconfinder.com/data/icons/web-ui-3/128/Mail-2-512.png" alt="email_icon.jpg" width="15" height="15"/> |
| ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [@MilosTadic01](github.com/MilosTadic01)                                                                                  | `milosgtadic` at yahoo.com                                                                                                       |


## License

[CC0 1.0 Universal](/LICENSE)
