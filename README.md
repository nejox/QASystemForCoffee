# Question Answering System for Coffee Machines
This is a question answering system that can help users troubleshoot their coffee machines. By inputting a question, the system searches through a database of documents related to coffee machines and provides the user with an accurate answer.
Disclaimer: This project is a student project of three during the Master Artifical Intelligence at Technical University of Applied Sciences Würzburg.

## How it Works
The system uses an extractive question answering variant and a data pipeline to gather comprehensive and relevant documents from various manufacturers and products. It then utilizes BERT-based Transformers, specifically BERT, DistilBERT, and RoBERTa, that have been fine-tuned on a dataset of 653 question-answer pairs to provide accurate answers.

Tech Stack involved in this Project:
- Python-based Webscraper with Selenium & BeautifulSoup
- Elasticsearch & Kibana
- Webservice with Django
- Huggingface for all the NLP Stuff
