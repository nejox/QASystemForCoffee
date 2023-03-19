import sys
sys.path.append("D:\Programming\master\MAI_NLP_PROJECT")
import logging
from django.apps import AppConfig

from transformers import pipeline
from sentence_transformers import SentenceTransformer
from Code.config import config


class CoffeeappApiConfig(AppConfig):
    # Model here, so it is only loaded once
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'coffeeapp_api'
    qa_model = pipeline("question-answering", model=config.QA_MODEL, tokenizer=config.QA_MODEL)
    embedder_model = SentenceTransformer(config.EMBEDDER)
    summarizer = pipeline("summarization", model="philschmid/bart-large-cnn-samsum")
    logging.info("Loaded QA Model and Embedder Model!")