import json
import pandas as pd
import numpy as np
import os
import collections
import transformers
import datasets
from utils import *
from sklearn.model_selection import train_test_split
from datasets import Dataset
from datasets import DatasetDict
from transformers import AutoTokenizer
from transformers import AutoModelForQuestionAnswering, TrainingArguments, Trainer
from transformers import default_data_collator
from tqdm import tqdm
import time
import torch
import gc

# run huggingface-cli login in your terminal to login to huggingface.co
from huggingface_hub.hf_api import HfFolder;

HfFolder.save_token('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')

############
max_length = 384  # The maximum length of a feature (question and context)
stride = 128  # The authorized overlap between two part of the context when splitting it is needed.
batch_size = 8
pad_on_right = True
max_answer_length = 30
N_BEST_SIZE_ = 20
tokenizer_for_train = ""
num_train_epochs = 15
learning_rate = 5e-5

############


def train_models(models):
    data = read_data(popAnswerEnd=False)

    # qa_df = pd.DataFrame(data)
    qa_train, qa_test = train_test_split(data, train_size=0.75)

    dataset_train = Dataset.from_pandas(pd.DataFrame(qa_train))
    dataset_test = Dataset.from_pandas(pd.DataFrame(qa_test))

    qa_dataset = DatasetDict({
        "train": dataset_train,
        "test": dataset_test
    })

    for model, tokenizer in tqdm(models):
        try:
            print(f"----Training: Model {model}----")
            train_model(model, tokenizer, qa_dataset, "models/")
            print(f"----Model {model} trained successfully----")
        except Exception as e:
            print("----Exception----")
            print(e)
            continue


def train_model(model_name, tokenizer_name, dataset, model_path):

    if "roberta" in model_name:
        global batch_size
        batch_size = 8

    global tokenizer_for_train
    tokenizer_for_train = AutoTokenizer.from_pretrained(tokenizer_name)

    tokenized_datasets = dataset.map(prepare_train_features, batched=True,
                                     remove_columns=dataset["train"].column_names)

    model_to_train = AutoModelForQuestionAnswering.from_pretrained(model_name)

    baseModel = model_name.split("/")[-1]
    output = f"{baseModel}-coffee" + time.strftime("%Y%m%d")
    training_args = TrainingArguments(
        output_dir=output,  # output directory
        num_train_epochs=num_train_epochs,  # total number of training epochs
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,  # batch size per device during training
        per_device_eval_batch_size=batch_size,  # batch size for evaluation
        warmup_steps=500,  # number of warmup steps for learning rate scheduler
        weight_decay=0.01,  # strength of weight decay
        # logging_dir='./logs',  # directory for storing logs
        logging_steps=100,
        evaluation_strategy="epoch",
        push_to_hub=True
    )
    data_collator = default_data_collator

    trainer = Trainer(
        model=model_to_train,  # the instantiated 🤗 Transformers model to be trained
        args=training_args,  # training arguments, defined above
        train_dataset=tokenized_datasets["train"],  # training dataset
        eval_dataset=tokenized_datasets["test"],  # evaluation dataset
        data_collator=data_collator,
        tokenizer=tokenizer_for_train
    )
    trainer.train()
    trainer.push_to_hub()
    # trainer.save_model(output)

    # # evaluate
    # raw_predictions = trainer.predict(tokenized_datasets["test"])
    #
    # test_features = qa_dataset["test"].map(
    #     prepare_validation_features,
    #     batched=True,
    #     remove_columns=qa_dataset["test"].column_names
    # )
    #
    # final_predictions = postprocess_qa_predictions(qa_dataset["test"], test_features, raw_predictions.predictions)
    #
    #
    # formatted_predictions = [{"id": k, "prediction_text": v} for k, v in final_predictions.items()]
    # references = [{"id": ex["id"], "answers": ex["answers"]} for ex in qa_dataset["test"]]
    #
    # for d in references:
    #     d["answers"].pop('answer_end', None)
    # # references
    # from datasets import load_metric
    #
    # metric = load_metric("squad_v2" if squad_v2 else "squad")
    # score = metric.compute(predictions=formatted_predictions, references=references)
    # score


def prepare_train_features(examples):
    # Some of the questions have lots of whitespace on the left, which is not useful and will make the
    # truncation of the context fail (the tokenized question will take a lots of space). So we remove that
    # left whitespace
    examples["question"] = [q.lstrip() for q in examples["question"]]

    # Tokenize our examples with truncation and padding, but keep the overflows using a stride. This results
    # in one example possible giving several features when a context is long, each of those features having a
    # context that overlaps a bit the context of the previous feature.
    tokenized_examples = tokenizer_for_train(
        examples["question" if pad_on_right else "context"],
        examples["context" if pad_on_right else "question"],
        truncation="only_second" if pad_on_right else "only_first",
        max_length=max_length,
        stride=stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    # Since one example might give us several features if it has a long context, we need a map from a feature to
    # its corresponding example. This key gives us just that.
    sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")
    # The offset mappings will give us a map from token to character position in the original context. This will
    # help us compute the start_positions and end_positions.
    offset_mapping = tokenized_examples.pop("offset_mapping")

    # Let's label those examples!
    tokenized_examples["start_positions"] = []
    tokenized_examples["end_positions"] = []

    for i, offsets in enumerate(offset_mapping):
        # We will label impossible answers with the index of the CLS token.
        input_ids = tokenized_examples["input_ids"][i]
        cls_index = input_ids.index(tokenizer_for_train.cls_token_id)

        # Grab the sequence corresponding to that example (to know what is the context and what is the question).
        sequence_ids = tokenized_examples.sequence_ids(i)

        # One example can give several spans, this is the index of the example containing this span of text.
        sample_index = sample_mapping[i]
        answers = examples["answers"][sample_index]
        # If no answers are given, set the cls_index as answer.
        if len(answers["answer_start"]) == 0:
            tokenized_examples["start_positions"].append(cls_index)
            tokenized_examples["end_positions"].append(cls_index)
        else:
            # Start/end character index of the answer in the text.
            start_char = answers["answer_start"][0]
            end_char = start_char + len(answers["text"][0])

            # Start token index of the current span in the text.
            token_start_index = 0
            while sequence_ids[token_start_index] != (1 if pad_on_right else 0):
                token_start_index += 1

            # End token index of the current span in the text.
            token_end_index = len(input_ids) - 1
            while sequence_ids[token_end_index] != (1 if pad_on_right else 0):
                token_end_index -= 1

            # Detect if the answer is out of the span (in which case this feature is labeled with the CLS index).
            if not (offsets[token_start_index][0] <= start_char and offsets[token_end_index][1] >= end_char):
                tokenized_examples["start_positions"].append(cls_index)
                tokenized_examples["end_positions"].append(cls_index)
            else:
                # Otherwise move the token_start_index and token_end_index to the two ends of the answer.
                # Note: we could go after the last offset if the answer is the last word (edge case).
                while token_start_index < len(offsets) and offsets[token_start_index][0] <= start_char:
                    token_start_index += 1
                tokenized_examples["start_positions"].append(token_start_index - 1)
                while offsets[token_end_index][1] >= end_char:
                    token_end_index -= 1
                tokenized_examples["end_positions"].append(token_end_index + 1)

    return tokenized_examples


def prepare_validation_features(examples):
    # Some of the questions have lots of whitespace on the left, which is not useful and will make the
    # truncation of the context fail (the tokenized question will take a lots of space). So we remove that
    # left whitespace
    examples["question"] = [q.lstrip() for q in examples["question"]]

    # Tokenize our examples with truncation and maybe padding, but keep the overflows using a stride. This results
    # in one example possible giving several features when a context is long, each of those features having a
    # context that overlaps a bit the context of the previous feature.
    tokenized_examples = tokenizer(
        examples["question" if pad_on_right else "context"],
        examples["context" if pad_on_right else "question"],
        truncation="only_second" if pad_on_right else "only_first",
        max_length=max_length,
        stride=stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    # Since one example might give us several features if it has a long context, we need a map from a feature to
    # its corresponding example. This key gives us just that.
    sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

    # We keep the example_id that gave us this feature and we will store the offset mappings.
    tokenized_examples["example_id"] = []

    for i in range(len(tokenized_examples["input_ids"])):
        # Grab the sequence corresponding to that example (to know what is the context and what is the question).
        sequence_ids = tokenized_examples.sequence_ids(i)
        context_index = 1 if pad_on_right else 0

        # One example can give several spans, this is the index of the example containing this span of text.
        sample_index = sample_mapping[i]
        tokenized_examples["example_id"].append(examples["id"][sample_index])

        # Set to None the offset_mapping that are not part of the context so it's easy to determine if a token
        # position is part of the context or not.
        tokenized_examples["offset_mapping"][i] = [
            (o if sequence_ids[k] == context_index else None)
            for k, o in enumerate(tokenized_examples["offset_mapping"][i])
        ]

    return tokenized_examples


def postprocess_qa_predictions(examples, features, raw_predictions, n_best_size=N_BEST_SIZE_,
                               max_answer_length=max_answer_length):
    all_start_logits, all_end_logits = raw_predictions
    # Build a map example to its corresponding features.
    example_id_to_index = {k: i for i, k in enumerate(examples["id"])}
    features_per_example = collections.defaultdict(list)
    for i, feature in enumerate(features):
        features_per_example[example_id_to_index[feature["example_id"]]].append(i)

    # The dictionaries we have to fill.
    predictions = collections.OrderedDict()

    # Logging.
    print(f"Post-processing {len(examples)} example predictions split into {len(features)} features.")

    # Let's loop over all the examples!
    for example_index, example in enumerate(examples):
        # Those are the indices of the features associated to the current example.
        feature_indices = features_per_example[example_index]

        min_null_score = None  # Only used if squad_v2 is True.
        valid_answers = []

        context = example["context"]
        # Looping through all the features associated to the current example.
        for feature_index in feature_indices:
            # We grab the predictions of the model for this feature.
            start_logits = all_start_logits[feature_index]
            end_logits = all_end_logits[feature_index]
            # This is what will allow us to map some the positions in our logits to span of texts in the original
            # context.
            offset_mapping = features[feature_index]["offset_mapping"]

            # Update minimum null prediction.
            cls_index = features[feature_index]["input_ids"].index(tokenizer.cls_token_id)
            feature_null_score = start_logits[cls_index] + end_logits[cls_index]
            if min_null_score is None or min_null_score < feature_null_score:
                min_null_score = feature_null_score

            # Go through all possibilities for the `n_best_size` greater start and end logits.
            start_indexes = np.argsort(start_logits)[-1: -n_best_size - 1: -1].tolist()
            end_indexes = np.argsort(end_logits)[-1: -n_best_size - 1: -1].tolist()
            for start_index in start_indexes:
                for end_index in end_indexes:
                    # Don't consider out-of-scope answers, either because the indices are out of bounds or correspond
                    # to part of the input_ids that are not in the context.
                    if (
                            start_index >= len(offset_mapping)
                            or end_index >= len(offset_mapping)
                            or offset_mapping[start_index] is None
                            or offset_mapping[end_index] is None
                    ):
                        continue
                    # Don't consider answers with a length that is either < 0 or > max_answer_length.
                    if end_index < start_index or end_index - start_index + 1 > max_answer_length:
                        continue

                    start_char = offset_mapping[start_index][0]
                    end_char = offset_mapping[end_index][1]
                    valid_answers.append(
                        {
                            "score": start_logits[start_index] + end_logits[end_index],
                            "text": context[start_char: end_char]
                        }
                    )

        if len(valid_answers) > 0:
            best_answer = sorted(valid_answers, key=lambda x: x["score"], reverse=True)[0]
        else:
            # In the very rare edge case we have not a single non-null prediction, we create a fake prediction to avoid
            # failure.
            best_answer = {"text": "", "score": 0.0}

        # Let's pick our final answer: the best one or the null answer (only for squad_v2)
        if not squad_v2:
            predictions[example["id"]] = best_answer["text"]
        else:
            answer = best_answer["text"] if best_answer["score"] > min_null_score else ""
            predictions[example["id"]] = answer

    return predictions


if __name__ == '__main__':
    # clearing cuda memory cache
    torch.cuda.empty_cache()
    gc.collect()

    models = [
        ("deepset/roberta-base-squad2", "deepset/roberta-base-squad2"),  # fine tuned
        ("distilbert-base-cased-distilled-squad", "distilbert-base-cased-distilled-squad"),  # fine tuned
        ("distilbert-base-uncased-distilled-squad", "distilbert-base-uncased-distilled-squad"),
        ("deepset/bert-base-cased-squad2", "deepset/bert-base-cased-squad2"),
        ("bert-large-uncased-whole-word-masking-finetuned-squad", "bert-large-uncased-whole-word-masking-finetuned-squad"),
        ("roberta-base", "roberta-base"),
        ("bert-base-uncased", "bert-base-uncased"),
        ("bert-base-cased", "bert-base-cased")
    ]

    train_models(models)
