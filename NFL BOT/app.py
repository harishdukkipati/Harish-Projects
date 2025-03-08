from flask import Flask, request, jsonify
from pinecone import Pinecone, ServerlessSpec
from transformers import BertTokenizer, BertModel
import torch
import openai
import config
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Pinecone
pc = Pinecone(api_key=config.PINECONE_API_KEY)
index_name = 'nfl-chatbot'
index = pc.Index(index_name)

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI
openai.api_key = config.OPENAI_API_KEY

# Load pre-trained model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')


def get_embedding(text):
    inputs = tokenizer(text, return_tensors='pt',
                       truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()


def query_openai(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()


@app.route('/ask', methods=['POST'])
def ask():
    logging.info("Endpoint '/ask' was called.")
    user_query = request.json['query']
    logging.info(f"Received query: {user_query}")

    try:
        query_embedding = get_embedding(user_query).tolist()
        logging.info(f"Query embedding: {query_embedding}")
        # Log first 10 values for inspection
        logging.info(f"Query embedding sample values: {query_embedding[:10]}")

        # Query Pinecone with top_k specified correctly
        result = index.query(vector=query_embedding,
                             top_k=5, include_metadata=True)  # Fetch more results for potential matches
        logging.info(f"Pinecone query result: {result}")

        # Process matches to identify the most relevant knowledge graph relationships
        matched_triples = []
        if result['matches']:
            for match in result['matches']:
                if 'metadata' in match:
                    triple = match['metadata']
                    matched_triples.append(triple)

        if matched_triples:
            # Construct a coherent answer based on matched triples
            response_content = []
            for triple in matched_triples:
                subject = triple.get('subject', 'Unknown')
                predicate = triple.get('predicate', 'has a relation')
                obj = triple.get('object', 'Unknown')
                response_content.append(f"{subject} {predicate} {obj}.")
            most_relevant_information = " ".join(response_content)
        else:
            most_relevant_information = "No relevant information found."

    except Exception as e:
        logging.error(f"Error querying Pinecone: {e}")
        return jsonify({"error": str(e)}), 500

    # Use OpenAI to generate a response
    prompt = f"Q: {user_query}\nA: {most_relevant_information}\nQ: {user_query}\nA:"
    response = query_openai(prompt)
    logging.info(f"OpenAI response: {response}")

    return jsonify({"response": response})


if __name__ == '__main__':
    app.run(port=5000)
