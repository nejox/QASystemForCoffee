import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import tensorflow_text as text

from sentence_transformers import SentenceTransformer, util
from datasets import load_dataset
from sentence_transformers import InputExample
from torch.utils.data import DataLoader
from sentence_transformers import losses

class EmbedderBase(object):
    def format_text(self, plain_text):
        """
        Modify this function when formatting input of other embedders.
        """
        pass

    def embed_single_text(self, single_text):
        pass

    def embed_list_text(self, list_text):
        pass

class SwivelEmbedder(EmbedderBase):
    def __init__(self, model_link="https://tfhub.dev/tensorflow/cord-19/swivel-128d/3"):
        self.embedder = hub.KerasLayer(model_link)
        print(f"Loaded pre-trained model {model_link} successfully!")

    def embed_single_text(self, plain_text):
        formated_text = tf.constant([plain_text])
        return np.array(self.embedder(formated_text))

    def embed_list_text(self, list_text):
        return np.array(self.embedder(tf.constant(list_text)))

class BertEmbedder(EmbedderBase):
    def __init__(self, bert_link="https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-4_H-256_A-4/2",
                 preprocessor_link="https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3",
                 sequence_length=256):
        self.preprocessor = hub.load(preprocessor_link)
        self.embedder = hub.KerasLayer(bert_link, trainable=False)
        self.sequence_length = sequence_length
        print(f"Loaded pre-trained model {bert_link} successfully!")

    def embed_single_text(self, plain_text):
        text = tf.constant([plain_text])
        tokenized_text = self.preprocessor.tokenize(text)
        encoder_input = self.preprocessor.bert_pack_inputs(
            [tokenized_text], seq_length=self.sequence_length) # ['input_mask', 'input_type_ids', 'input_word_ids']

        outputs = self.embedder(encoder_input)
        return np.array(outputs["pooled_output"]) # Embedding of the whole sentence, shape [1, 768]

    def embed_list_text(self, list_text):
        text = tf.constant(list_text)
        tokenized_text = self.preprocessor.tokenize(text)
        encoder_input = self.preprocessor.bert_pack_inputs(
            [tokenized_text], seq_length=self.sequence_length)  # ['input_mask', 'input_type_ids', 'input_word_ids']

        outputs = self.embedder(encoder_input)
        return np.array(outputs["pooled_output"])  # Embedding of the whole sentence, shape [1, 768]


class Sentencet5Embedder(EmbedderBase):
    def __init__(self, model_link="https://tfhub.dev/google/sentence-t5/st5-11b/1"):
        self.embedder = hub.KerasLayer(model_link)
        print(f"Loaded pre-trained model {model_link} successfully!")

    def embed_single_text(self, plain_text):
        formated_text = tf.constant([plain_text])
        return np.array(self.embedder(formated_text))

    def embed_list_text(self, list_text):
        return np.array(self.embedder(tf.constant(list_text)))

class UniversalSentenceEmbedder:
    def __init__(self, model_link="https://tfhub.dev/google/universal-sentence-encoder/4"):
        self.embedder = hub.load(model_link)
        print(f"Loaded pre-trained model {model_link} successfully!")
        
    def embed_single_text(self, plain_text):
        return(np.array(self.embedder([plain_text])))

    def embed_list_text(self, list_text):
        return np.array(self.embedder(list_text))

class allMiniLMEmbedder:
    def __init__(self, model_id="sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(model_id)
        print(f"Loaded pre-trained model {model_id} successfully!")

    def embed_single_text(self, plain_text):
        return (self.embedder.encode(plain_text, convert_to_tensor=False))

    def embed_list_text(self, list_text):
        return (self.embedder.encode(list_text, convert_to_tensor=False))


class FinetunedAllMiniLMEmbedder:
    def __init__(self, model_id="sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(model_id)
        print(f"Loaded pre-trained model {model_id} successfully!")
        
    def fine_tune(self):
        self.dataset = load_dataset("json", data_files="training_data.json")
        train_examples = []
        train_data = self.dataset['train']['set']
        n_examples = self.dataset['train'].num_rows

        for i in range(n_examples):
            example = train_data[i]
            train_examples.append(InputExample(texts=[example[0], example[1]]))

        train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)
        train_loss = losses.MultipleNegativesRankingLoss(model=self.embedder)
        num_epochs = 4
        warmup_steps = int(len(train_dataloader) * num_epochs * 0.1)
        self.embedder.fit(train_objectives=[(train_dataloader, train_loss)],
                          epochs=num_epochs,
                          warmup_steps=warmup_steps) 

    def embed_single_text(self, plain_text):
        return (self.embedder.encode(plain_text, convert_to_tensor=False))

    def embed_list_text(self, list_text):
        return (self.embedder.encode(list_text, convert_to_tensor=False))



