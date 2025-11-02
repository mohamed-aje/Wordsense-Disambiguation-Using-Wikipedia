This project is part of Natural Language Processing and Text Mining course at the University of Oulu. 

Project 30: Wordsense Disambiguation Using Wikipedia 2 

# 🧠 WordSense Disambiguation Using Wikipedia

This repository implements an improved **Lesk algorithm** for **Word Sense Disambiguation (WSD)** using both **WordNet** and **Wikipedia** as lexical resources.  
It also includes **WikiSim similarity**, **AQUAINT batch evaluation**, and **correlation analysis** with standard benchmark datasets (MC, RG, WS353).

---

## 🚀 Key Features

✅ **Improved WordNet Lesk**  
- Uses tokenization, lemmatization, and semantic overlap  
- Integrates Wu–Palmer similarity (`wup_similarity`) for semantic closeness  

✅ **Improved Wikipedia Lesk**  
- Retrieves disambiguation pages and article summaries  
- Combines contextual and title-based overlaps  

✅ **AQUAINT Batch Evaluation**  
- Runs Lesk algorithm across multiple AQUAINT text files  
- Exports structured JSON results with run metadata  

✅ **WikiSim Similarity**  
- Computes semantic similarity between custom word pairs  
- Used for convex combination experiments  

✅ **Correlation Experiments**  
- Evaluates WikiSim & embedding-based similarity correlations  
- Supports datasets: **MC**, **RG**, **WS353**  
- Supports embeddings: **FastText**, **Word2Vec**, etc.

---

