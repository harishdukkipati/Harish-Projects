# 📝 Project: N-gram Language Models (Unigram, Bigram, Trigram)

## 📖 Overview
In this project, I implemented **unigram, bigram, and trigram language models** in Python to predict word sequences and evaluate how effectively each model captures language patterns.  

---

## 🚀 Features
- Built **unigram, bigram, and trigram models** for word sequence prediction  
- Trained models on text corpora to **calculate probabilities** based on preceding word context  
- Evaluated model accuracy using **perplexity** as the primary metric  
- Compared the performance of different N-gram models in capturing natural language dependencies  

---

## ⚙️ Technical Highlights
- **Language:** Python  
- **Concepts:** Statistical language modeling, Markov assumption, probability distributions  
- **Evaluation Metric:** Perplexity (lower perplexity = better model performance)  
- **Comparison:** Demonstrated that higher-order N-grams (bigrams/trigrams) captured more contextual information than unigrams  

---

## 🧩 Learning Outcomes
Through this project, I gained experience with:
- Implementing **probabilistic models** for NLP tasks  
- Understanding the **trade-offs** between model complexity and performance  
- Evaluating and comparing models using a standard metric (**perplexity**)  
- Applying N-gram models as a foundation for more advanced **language modeling approaches**  

model = BigramModel()
model.train("training_corpus.txt")

# Predict next word
print(model.predict("the quick"))

