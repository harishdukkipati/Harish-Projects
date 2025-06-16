## MCP Server – Wikipedia + GPT-4 Integration

This is an MCP (Modular Code Processing) server project that uses **FastAPI**, the **Wikipedia API**, and **OpenAI's GPT-4** to answer user questions with contextual knowledge. It modularly separates logic into components for cleaner code structure and demonstrates how a server can use an LLM to interact with external APIs.

---

### Endpoints Overview

The server exposes 3 main endpoints:

- **`/wikipedia/search`**:  
  Takes a query and returns matching Wikipedia article titles.

- **`/wikipedia/summary`**:  
  Given a title, returns the corresponding Wikipedia summary.  

- **`/chat`**:  
  Functions as a smart chatbot. It takes a natural language question, extracts a related title, retrieves the Wikipedia summary for that title, and asks the LLM to answer the original question using that summary.  

#### Example Breakdown

If a user asks:  
**“What team does LeBron James play for?”**, the system will:

1. Query Wikipedia with title `"LeBron James"`
2. Retrieve the top matching article summary
3. Pass that summary and the original question to GPT-4
4. Return:  **"LeBron James plays for the Los Angeles Lakers."**

---

### How to run the Project

1. **Clone the repository**

2. **Set up a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate

3. **Install all required packages**:
   ```bash
   pip install -r requirements.txt

4. **Create a .env file and add your OpenAI API Key**
   - In the root directory of your project, create a file named `.env`
   - Add the following line to it (replace with your actual API key):

     ```
     OPENAI_API_KEY=your_openai_key_here
     ```

   - If you don’t have an OpenAI API key, you can get one from:  
     [https://platform.openai.com/settings/organization/api-keys](https://platform.openai.com/settings/organization/api-keys)

5. **Run the server**:

   ```bash
   uvicorn app:app --reload

6. **Open your browser and go to**:

    ```bash
    http://127.0.0.1:8000/docs

7. **Use the Swagger UI to test the endpoints**:

- **`/wikipedia/search`**: Enter something like `"Elon Musk"`
- **`/wikipedia/summary`**: Enter a title like `"Python (programming language)"`
- **`/chat`**: Ask a question like `"Who founded Tesla?"`

8. **View Results**:

- You’ll receive a structured JSON response with the answer
- The terminal will show a `200 OK` status if the API call was successful
