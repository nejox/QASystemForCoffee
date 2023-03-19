import collections
import logging
import sys
# sys.path.append("D:\Programming\master\MAI_NLP_PROJECT")
# import Code.SimilaritySearch.embedders as embedders
import pandas as pd
from django.conf import settings
import openai

from Code.Clients import client_factory
from Code.CoffeeappBackend.coffeeapp_api.apps import CoffeeappApiConfig
from Code.config import config


class QuestionAnswerer:

    def __init__(self, language, question, manufacturer=None, product=None, model=None, max_answers=config.MAX_ANSWERS):
        self.language = language
        self.product = product
        self.manufacturer = manufacturer
        self.question = question
        self.max_answers = max_answers
        self.answers = None
        self.errors = None
        self.qa_model = CoffeeappApiConfig.qa_model
        self.embedder_model = CoffeeappApiConfig.embedder_model
        self.summarizer = CoffeeappApiConfig.summarizer
        self.n_returns = config.SIM_SEARCH_RETURNS

    def is_valid(self):
        """Checks if the QuestionAnswerer is valid.

        Returns
        -------
        bool
            True if the QuestionAnswerer is valid, False otherwise
        """
        try:
            if self.language and self.question:
                return True
            else:
                self.errors = "question not valid"
                return False
        except Exception:
            self.errors = Exception
            return False

    def ask(self):
        """Entry method for the QuestionAnswerer"""
        try:
            context = self._get_context()
            logging.debug("Received Context and Question!")
            self.answers = self._get_answers(context)
            logging.debug("Answered Question!")
        except Exception:
            self.errors = Exception
            return False

    def _get_context(self):
        """
        Method that reads the context given from ES and extracts only the paragraph texts.

        Returns
        -------
        list
            List of paragraphs from one specific manufacturer and product
        """
        embedded_question = self.embedder_model.encode(self.question)
        logging.debug("Embedded Question!")

        contexts = client_factory.get_context_client().search_similar_context(manufacturer=self.manufacturer,
                                                                              product_name=self.product,
                                                                              language=self.language,
                                                                              question_embedded=embedded_question,
                                                                              n_returns=self.n_returns)

        if contexts:
            df = pd.DataFrame(contexts)
            df["headerParagraphText"].fillna("", inplace=True)
            df["subHeaderParagraphText"].fillna("", inplace=True)  # fill None paragraphs with empty string
            df["total"] = df["headerParagraphText"].astype(str) + df["subHeaderParagraphText"].astype(str)
            texts = df["total"].unique().tolist()
            texts = list(filter(None, texts))

            return texts

        else:
            logging.error("no context retrievable")
            return None

    def _get_answers(self, context):
        """Method that returns the answers to the question.

        Parameters
        ----------
        context : list
            List of paragraphs from one specific manufacturer and product

        Returns
        -------
        list
            List of answers to the question
        """

        logging.info("QA Model received " + str(len(context)) + " contexts!")

        results = []
        result_answers = []

        for paragraph in context:
            result = self.qa_model(question=self.question, context=paragraph)

            result_answer = result["answer"].replace(".", "").replace(",", "").lower()

            # filter mechanic: to filter answers like "12" or "yes"
            if len(result["answer"]) <= 10 or result_answer in result_answers:
                continue

            result_answers.append(result_answer)
            results.append(result)

        topResults = sorted(results, key=lambda k: k['score'], reverse=True)[0:self.max_answers]
        answers = [answer["answer"] for answer in topResults]

        conversation = self.question + "\n" + "\n".join(answers)
        # summary = self.summarizer(conversation)[0]["summary_text"]

        generation = self._generate_answer(self.question, answers)

        # TODO: return summary and answers
        answer_object = {
            "extracted_answers": answers,
            # "summary": summary,
            "generation": generation
        }

        return answer_object  # , answers

    def _generate_answer(self, question, answers):
        """Method that generates a new answer based on the answers.

        Parameters
        ----------
        answers : list
            List of answers to the question

        Returns
        -------
        str
            Generated answer
        """
        openai.api_key = config.KEY

        # Write all answers in one string
        answer_string = ""
        for answer in answers:
            answer_string += answer + r"\n"

        # Set up the prompt
        # prompt = "Write an answer to the user question \"How do I clean the machine?\" about a coffee machine manual  with the following text prompts:\nClean with a damp cloth or sponge.\nWhile cleaning, never immerse the coffee maker in water\nWhile cleaning, never immerse the coffee maker in water.\nremove the plug from the mains.\nClean the body of the coffee machine with a damp cloth or sponge.\n\nIgnore unreasonable prompts"
        # prompt = "Once upon a time"
        prompt = "Write an answer to the user question \"" + question + "\" about a coffee machine manual  with the following text prompts:\n" + answer_string + "\n\n"

        # Set up the parameters for the API request
        params = {
            "engine": "text-davinci-003",
            "prompt": prompt,
            "temperature": 0.7,
            "max_tokens": 256,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        }

        # Send the API request
        response = openai.Completion.create(**params)

        # Extract the generated text from the response
        generated_text = response.choices[0].text.strip()

        return generated_text
