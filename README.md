# Agentic RAG using Gemini
A full-stack web application demonstrating a Retrieval-Augmented Generation (RAG) chat interface and a basic shopping cart feature, built with React and FastAPI and using google-genai sdk.

## ✨ Features

* **Interactive Chat Interface:** Real-time chat between user and an AI assistant.
* **RAG-Powered Responses:** Assistant uses a RAG pipeline (retrieving relevant product info) to generate informative answers.
* **Streaming Responses:** AI responses are streamed token-by-token for a smoother user experience.
* **Function Calling:** The RAG agent utilizes function calling to retrieve data dynamically.
* **Hybrid Search:** Combines keyword (PostgreSQL FTS) and semantic vector search (pgvector) for effective information retrieval.
* **Shopping Cart Display:** Fetches and displays user-specific order/cart data from the backend.

## 🏛️ Agentic Rag Architecture
![agentic_rag](https://github.com/user-attachments/assets/5ace76d2-7315-4763-8d85-abea14d44ae5)

##📋 Prerequisites

Before you begin, ensure you have met the following requirements:

* **Node.js & npm/yarn:** For running the React frontend. ([Download Node.js](https://nodejs.org/))
* **Python:** Version 3.9+ recommended. ([Download Python](https://www.python.org/))
* **pip:** Python package installer (usually comes with Python).
* **PostgreSQL:** A running instance of PostgreSQL database. ([Download PostgreSQL](https://www.postgresql.org/))
* **pgvector Extension:** Enabled on your PostgreSQL database. ([pgvector GitHub](https://github.com/pgvector/pgvector))
* **Git:** For cloning the repository.

## ⚙️ Getting Started

Follow these steps to get your development environment set up:

1.  **Clone the repository:**
    ```bash
    git clone [your-repository-url]
    cd [your-project-directory]
    ```

2.  **Backend Setup:**
    ```bash
    cd backend # Navigate to the backend directory

    # Create and activate a virtual environment (recommended)
    python -m venv backend_env
    # On Windows:
    # backend_env\Scripts\activate
    # On macOS/Linux:
    # source backend_env/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Database Setup:
    # - Ensure PostgreSQL is running.
    # - Run file Database/init_db.py to create tables and configuration for search

    # Environment Variables:
    # - Create a .env file in the 'backend' directory.
    # - Add the required environment variables (see Configuration section below).
    #   Example .env file:
    #   DATABASE_URL=postgresql://user:password@host:port/database
    #   GEMINI_API_KEY=your_gemini_api_key_here

    # Run the backend server
    fastapi dev main.py
    ```
    *(The backend will be running on `http://localhost:8000`)*

3.  **Frontend Setup:**
    ```bash
    cd ../frontend # Navigate to the frontend directory (from the project root)

    # Install dependencies
    npm install
    # or if you use yarn:
    # yarn install

    # Run the frontend development server
    npm start
    # or if you use yarn:
    # yarn start
    ```
    *(The frontend should now open automatically in your browser, likely at `http://localhost:3000`)*

## 🔧 Configuration

The application requires the following environment variables to be set in the `.env` file within the `backend` directory:

* `DATABASE_URL`: The connection string for your PostgreSQL database.
    * Format: `postgresql://<user>:<password>@<host>:<port>/<database_name>`
* `GEMINI_API_KEY`: Your API key for the Google Gemini service. Get yours from [Google AI Studio](https://aistudio.google.com/app/apikey).
* `MODEL_NAME`: (Optional, if hardcoded check `settings.py` or similar) The specific Gemini model name being used (e.g., `gemini-2.0-flash`).
* [Add any other necessary environment variables]

## ▶️ Usage

1.  Make sure both the backend and frontend servers are running (follow the "Getting Started" steps).
2.  Open your web browser and navigate to `http://localhost:3000` (or the port your frontend is running on).
3.  Interact with the chat interface by typing messages and sending them.
4.  View the shopping cart section to see the displayed items (currently hardcoded for User ID 1).

## 🌐 API Endpoints (Backend)

A brief overview of the main API endpoints:

* `POST /api/chat`: Get a non-streaming chat response (if implemented).
* `POST /api/chat/stream`: Get a streaming chat response using Server-Sent Events.
* `GET /api/cart`: Fetch cart/order data for a specific user (`?user_id=...`).

## Demo
[https://youtu.be/ip9_BZqYyn8]
