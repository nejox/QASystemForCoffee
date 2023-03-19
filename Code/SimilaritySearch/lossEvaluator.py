import logging
import os
import csv
import numpy as np
from typing import List, Union
import math
from tqdm.autonotebook import trange
from sentence_transformers.util import batch_to_device
import torch
from torch import nn
from torch.utils.tensorboard import SummaryWriter

from sentence_transformers import SentenceTransformer, InputExample, losses

from sentence_transformers.evaluation import SentenceEvaluator


class LossEvaluator(SentenceEvaluator):

    def __init__(self, loader, loss_model: nn.Module = None, name: str = '', log_dir: str = None,
                 show_progress_bar: bool = False, write_csv: bool = True):

        """
        Evaluate a model based on the loss function.
        The returned score is loss value.
        The results are written in a CSV and Tensorboard logs.
        :param loader: Data loader object
        :param loss_model: loss module object
        :param name: Name for the output
        :param log_dir: path for tensorboard logs 
        :param show_progress_bar: If true, prints a progress bar
        :param write_csv: Write results to a CSV file
        """

        self.loader = loader
        self.write_csv = write_csv
        self.name = name
        self.loss_model = loss_model
        if show_progress_bar is None:
            show_progress_bar = (
                    logger.getEffectiveLevel() == logging.INFO or logger.getEffectiveLevel() == logging.DEBUG)
        self.show_progress_bar = show_progress_bar

        self.csv_file = "loss_evaluation" + ("_" + name if name else '') + "_results.csv"
        self.csv_headers = ["epoch", "steps", "loss"]
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        loss_model.to(self.device)

    def __call__(self, model, output_path: str = None, epoch: int = -1, steps: int = -1) -> float:

        self.loss_model.eval()

        loss_value = 0
        self.loader.collate_fn = model.smart_batching_collate
        num_batches = len(self.loader)
        data_iterator = iter(self.loader)

        with torch.no_grad():
            for _ in trange(num_batches, desc="Iteration", smoothing=0.05, disable=not self.show_progress_bar):
                sentence_features, labels = next(data_iterator)
                # move data to gpu
                sentence_features = list(map(lambda batch: batch_to_device(batch, self.device), sentence_features))
                labels = labels.to(self.device)

                loss_value += self.loss_model(sentence_features, labels).item()

        final_loss = loss_value / num_batches

        if output_path is not None and self.write_csv:

            csv_path = os.path.join(output_path, self.csv_file)
            output_file_exists = os.path.isfile(csv_path)

            with open(csv_path, newline='', mode="a" if output_file_exists else 'w', encoding="utf-8") as f:
                writer = csv.writer(f)
                if not output_file_exists:
                    writer.writerow(self.csv_headers)

                writer.writerow([epoch, steps, final_loss])

        self.loss_model.zero_grad()
        self.loss_model.train()

        return final_loss
