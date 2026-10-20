# GoFit / Gym Bro VAMOS — AI Fitness Chatbot

A web-based fitness chatbot with a friendly Malaysian "Gym Bro" personality. Built with Python, FastAPI, MongoDB, and the Groq API, the application lets users ask about workouts, diet, and healthy habits in English, Malay, or Manglish, then revisit saved conversations.

The assistant's behavior is guided by a system prompt that requests short, motivating answers and asks it to decline topics outside fitness and healthy living.

## Features

- **AI fitness conversations:** Text-based workout, diet, and lifestyle guidance generated through Groq using `llama-3.1-8b-instant`.
- **Malaysian personality:** A prompt designed for friendly, professional responses in English, Malay, or Manglish.
- **Recent conversation context:** Each AI request includes up to five previously saved messages from the selected conversation.
- **Persistent chat history:** MongoDB stores conversations so users can reopen them from the sidebar.
- **Multiple conversations:** Start a new chat or continue an existing session, with titles generated from the first message.
- **Registration and login forms:** Register a username, email, and password, then log in through the web interface.
- **Browser interface:** A landing page, account pages, and a chat screen with message bubbles, a typing indicator, and Enter-to-send support.

## Technology stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Backend | Python, FastAPI | Page routes, form handling, and JSON endpoints |
| Server | Uvicorn | Runs the application locally |
| Templates | Jinja2 | Serves the HTML pages |
| Frontend | HTML, CSS, JavaScript | Interface, browser storage, and Fetch API requests |
| AI | Groq Python SDK | Requests responses from the hosted language model |
| Database | MongoDB, PyMongo | Stores users and chat sessions |
| Configuration | python-dotenv | Loads the API key from a local `.env` file |
| Validation | Pydantic | Validates incoming chat request fields |

## How it works

```text
Browser (HTML / CSS / JavaScript)
    |
    | Page requests, login/signup forms, and JSON chat requests
    v
FastAPI backend (main.py)
    |                         |
    | Users and chat history  | System prompt + recent messages + new message
    v                         v
MongoDB                     Groq API
    ^                         |
    | Save message pair       | Generated reply
    +----- FastAPI <----------+
              |
              v
        Browser chat interface
```

1. **Create an account:** The signup form submits a username, email, password, and password confirmation. The backend checks that the passwords match and that the username is available before inserting the user into MongoDB.
2. **Log in:** The backend compares the submitted credentials with the stored record and redirects successful logins to `/chat`. The login page also saves the submitted username as `current_user` in browser `localStorage`.
3. **Start a conversation:** The chat interface generates a session ID in JavaScript and fetches saved conversation titles for the browser's selected username.
4. **Send a message:** JavaScript posts `message`, `username`, and `session_id` to `/api/chat`. The backend looks up the session and creates a record if it does not exist.
5. **Generate a response:** The backend combines the Malaysian Gym Bro system prompt, up to five saved messages, and the new user message. It calls Groq with the configured model and a temperature of `0.8`.
6. **Save and display:** After a successful AI response, the backend appends both messages to MongoDB and returns the reply. The browser displays it and refreshes the history sidebar.
7. **Continue later:** Selecting a sidebar item loads that session's saved messages. Subsequent messages use the same session ID. Selecting **New Chat** generates a new ID and clears the visible conversation; its database record is created when the first message is sent.

The complete saved conversation can be reopened, but only the five most recent saved messages are included as history in each AI request.

## Project structure

```text
Fitness-Chatbot/
├── main.py                 # FastAPI app, Groq calls, MongoDB access, and routes
├── templates/
│   ├── index.html          # Landing page
│   ├── login.html          # Login form and browser username storage
│   ├── signup.html         # Registration form
│   └── chat.html           # Chat layout and history sidebar
├── static/
│   ├── chat.js             # Messaging, session IDs, and history loading
│   ├── Script.js           # Landing-page scroll animations
│   ├── chat.css
│   ├── login.css
│   ├── signup.css
│   ├── style.css
│   └── image/
│       └── Logo company.png
├── .gitignore              # Excludes .env
└── README.md
```

## Run locally

### Prerequisites

- Python 3 with `pip` and `venv` available.
- A running MongoDB instance at `mongodb://localhost:27017/`.
- A Groq API key with access to the model configured in `main.py`.
- Internet access for AI requests. The interface also uses externally hosted images and Font Awesome icons.

### 1. Create a virtual environment and install dependencies

Run these commands from the project root in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn pymongo pydantic groq python-dotenv jinja2 python-multipart
```

These commands invoke the virtual environment directly, so activation is optional. `python-multipart` is required for the login and signup form endpoints. The repository currently has no dependency lockfile or pinned package versions.

### 2. Configure the API key

Create a `.env` file in the project root:

```dotenv
API_KEY=your_groq_api_key_here
```

The variable name must be `API_KEY`, matching `main.py`. The existing `.gitignore` excludes `.env`; keep your real key out of source control.

The MongoDB URI, database name, and model name are currently set directly in `main.py`:

| Setting | Current value |
| --- | --- |
| MongoDB URI | `mongodb://localhost:27017/` |
| Database | `fitness_db` |
| Collections | `users`, `chat_history` |
| Groq model | `llama-3.1-8b-instant` |

### 3. Start the application

Make sure MongoDB is running, then execute:

```powershell
.\.venv\Scripts\python.exe main.py
```

Open <http://127.0.0.1:8000> in your browser. Run the command from the project root because the app uses relative paths for `static/` and `templates/`.

The development server listens on `127.0.0.1:8000` with automatic reload enabled. FastAPI also provides interactive endpoint documentation at <http://127.0.0.1:8000/docs>.

### 4. Try the workflow

1. Open `/signup` and create a test account.
2. Open `/login`, enter the credentials, and submit the form.
3. Ask a fitness question, such as: `Bro, suggest a beginner three-day gym routine.`
4. Send a follow-up to try the recent conversation context.
5. Select **New Chat**, send another question, and use the history sidebar to reopen the first conversation.

## Routes and API

| Method | Path | Purpose / input |
| --- | --- | --- |
| GET | `/` | Landing page |
| GET | `/signup` | Registration page |
| POST | `/signup` | Form fields: `username`, `email`, `password`, `confirm_password` |
| GET | `/login` | Login page |
| POST | `/login` | Form fields: `username`, `password` |
| GET | `/chat` | Chat page |
| POST | `/api/chat` | JSON: `message`, `username`, `session_id`; returns `reply` |
| POST | `/api/get_history` | JSON: `username`; returns `history` with session IDs and titles |
| POST | `/api/load_chat` | JSON: `session_id`; returns saved `messages` |

Example request body for `/api/chat`:

```json
{
  "message": "Suggest a beginner chest workout.",
  "username": "demo_user",
  "session_id": "demo-session-001"
}
```

Example response shape:

```json
{
  "reply": "An AI-generated fitness response appears here."
}
```

## Stored data

- **`users`:** Stores `username`, `email`, and `password`.
- **`chat_history`:** Stores `session_id`, `username`, `title`, `messages`, and a creation `timestamp`. Each message has a `sender` (`user` or `bot`) and `text`.

History is sorted by session creation time, newest first. Sending another message does not update that timestamp.

## Current scope and limitations

This is a development prototype. Registration and credential checks exist, but passwords are currently stored in plain text, and the backend does not establish an authenticated session or enforce ownership of chat requests. The username in browser storage identifies the history to request; it is not proof of authentication.

Messages are currently inserted into the page using `innerHTML` without sanitization. Password hashing, server-side authentication and authorization, and safe message rendering are necessary improvements before public deployment.

The implemented experience is text chat. Landing-page references to real-time form correction, calorie/macro tracking, and fridge-based meal planning do not correspond to dedicated implemented tools. The assistant can discuss fitness topics through generated text, and its topic restrictions depend on prompting.

## Troubleshooting

- **Missing API key:** Check that `.env` exists in the project root and contains `API_KEY`. The Groq client is created during application startup, so a missing key can prevent startup.
- **Database connection failures:** Confirm MongoDB is listening at `localhost:27017`. Change the hardcoded URI in `main.py` if your database runs elsewhere.
- **Groq errors:** Check your API key, account access to the configured model, and the backend terminal output. The current chat handler returns API exceptions inside the `reply` field.
- **Missing templates or static files:** Start the server from the project root.
- **Signup-page login link:** The existing link points to `login.html`; use `/login` directly if it does not navigate correctly.
