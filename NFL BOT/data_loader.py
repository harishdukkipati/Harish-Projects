from pinecone import Pinecone, ServerlessSpec
from transformers import BertTokenizer, BertModel
import torch
import json
import config
import logging

logging.basicConfig(level=logging.DEBUG)

pc = Pinecone(api_key=config.PINECONE_API_KEY)
index_name = 'nfl-chatbot'

if index_name not in pc.list_indexes().names():
    logging.info(f"Creating index '{index_name}'.")
    pc.create_index(
        name=index_name,
        dimension=768,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
else:
    logging.info(f"Index '{index_name}' already exists.")

index = pc.Index(index_name)

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')


def get_embedding(text):
    inputs = tokenizer(text, return_tensors='pt',
                       truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()


with open('nfl_documents.json', 'r') as f:
    knowledge_graph_data = json.load(f)

for i, triple in enumerate(knowledge_graph_data):
    # Create a text representation of the triple
    text_representation = f"{triple['subject']} {triple['predicate']} {triple['object']}"
    embedding = get_embedding(text_representation)
    index.upsert([{
        "id": str(i),  # Use the index as the ID
        "values": embedding.tolist(),
        "metadata": {
            "subject": triple['subject'],
            "predicate": triple['predicate'],
            "object": triple['object'],
            "text": text_representation  # Include the full text for retrieval
        }
    }])
    logging.info(
        f"Inserted triple ID {triple['id']} with data: {text_representation}")

logging.info("Verifying inserted documents...")
for triple in knowledge_graph_data:
    text_representation = f"{triple['subject']} {triple['predicate']} {triple['object']}"
    embedding = get_embedding(text_representation).tolist()
    result = index.query(vector=embedding, top_k=1, include_metadata=True)
    if result['matches']:
        match = result['matches'][0]
        logging.info(
            f"Queried triple: {match.get('metadata', 'No metadata found')}")
    else:
        logging.warning(f"No match found for triple: {text_representation}")
