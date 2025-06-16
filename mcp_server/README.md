This is an MCP (Modular Code Processing) server project that uses FastAPI, the Wikipedia API, and OpenAI's GPT-4 to answer user questions with contextual knowledge. It modularly separates logic into components for cleaner code structure and demonstrates how a server can use an LLM to interact with external APIs.

 The server exposes 3 main endpoints: 

/wikipedia/search: Takes a query and returns matching Wikipedia article titles.

/wikipedia/summary: Given a title, returns the corresponding Wikipedia summary.
Example: Inputting “Declaration of Independence” would return a detailed summary about its historical context and significance.

/chat: This endpoint functions as a smart chatbot. It takes a natural language question, extracts a related title, retrieves the Wikipedia summary for that title, and then asks the LLM to answer the original question using that summary.
Example: Asking “What team does LeBron James play for?” will search “LeBron James,” pull his Wikipedia summary, and extract that he plays for the Los Angeles Lakers.

Example: If a user asks, “What team does LeBron James play for?", the system: 

- Queries Wikipedia with “LeBron James”

- Retrieves the top matching article summary

- Passes that summary and the original question to GPT-4

- Returns: “LeBron James plays for the Los Angeles Lakers.”

The project overall contains of 5 main files: 

app.py: Main FastAPI app. Defines all three endpoints and controls the request flow.

llm_utils.py: Contains logic to query the GPT-4 model using a given prompt. It provides the LLM-generated responses used in the chatbot endpoint.

wikipedia_utils.py: Handles all API requests to Wikipedia — both the search (titles) and the summary retrieval.

requirements.txt: Lists all necessary Python packages to run the project. These can be installed with pip install -r requirements.txt.

run.py: The script to launch the FastAPI server. It starts the backend and listens for API requests, enabling the LLM to interact with Wikipedia through the endpoints.

How to Run the Project:

1. Clone the repository 

2. Set up a virtual environment(optional):
python3 -m venv venv
source venv/bin/activate

3. Install all required packages: pip install -r requirements.txt

4. Create a seperate file title it .env and add your OpenAI API key(If you don't have an OPENAI API Key go this website: https://platform.openai.com/settings/organization/api-keys)

5. Run the server: uvicorn app:app --reload 

6. Open your browser and go to: http://127.0.0.1:8000/docs

7. Use the Swagger UI to test:

/wikipedia/search: Enter something like "Elon Musk"

/wikipedia/summary: Enter a title like "Python (programming language)"

/chat: Ask a question like "Who founded Tesla?"

8. View results:

You'll receive a structured JSON response.

Terminal will log a 200 OK status if successful.