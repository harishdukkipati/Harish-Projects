from fastapi import FastAPI, Query
from wikepedia_utils import search_wikipedia, get_summary
from llm_utils import ask_llm

app = FastAPI()

@app.get("/wikipedia/search")
def wikipedia_search(q: str = Query(..., description="Search query")):
    return {"results": search_wikipedia(q)}

@app.get("/wikipedia/summary")
def wikipedia_summary(title: str):
    summary = get_summary(title)
    return {"title": title, "summary": summary}

@app.get("/chat")
def chat_with_wiki_assistant(query: str):
    title = extract_title_from_query(query)
    print(f"LLM extracted title: {title}")

    summary = get_summary(title)
    
    if summary:
        print(f"Summary for '{title}': {summary[:200]}...")
        prompt = (
            f"Wikipedia summary:\n{summary}\n\n"
            f"Question: {query}\n"
            f"Answer based on the summary above:"
        )
    else:
        print("No Wikipedia summary found, answering with LLM only.")
        prompt = f"Question: {query}\nAnswer:"
    
    answer = ask_llm(prompt)
    print(f"LLM answer: {answer}")

    return {
        "related_article": title if summary else None,
        "wikipedia_summary": summary if summary else None,
        "llm_answer": answer
    }

def extract_title_from_query(query: str) -> str:
    prompt = (
        f"Given this question, extract the most relevant Wikipedia article title "
        f"as a short phrase or name. Return ONLY the title, no explanation.\n\n"
        f"Question: {query}\n\nTitle:"
    )
    title = ask_llm(prompt)
    return title.strip().strip('"')  # clean quotes or spaces if any
