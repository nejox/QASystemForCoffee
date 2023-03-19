# from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import json
import numpy as np
import warnings

# TODO: Probably obsolete, as the qa pipeline is now loaded in the settings.py

warnings.simplefilter(action='ignore', category=FutureWarning)
nlp = pipeline("question-answering", model="deepset/roberta-base-squad2")

def answer_question(context, question):
    """Method that returns the answers to the question.

    Parameters
    ----------
    context : list
        List of paragraphs from one specific manufacturer and product
    questions : str
        Question to be answered

    Returns
    -------
    list
        List of answers to the question
    """

    results = []
    
    for paragraph in context:
        
        result = nlp(question=question, context=paragraph)
        results.append(result)

    results = sorted(results, key=lambda k: k['score'], reverse=True)

    return results