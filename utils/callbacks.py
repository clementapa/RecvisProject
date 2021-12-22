import wandb
from pytorch_lightning.callbacks import Callback
from pytorch_lightning.loggers import WandbLogger
import numpy as np
import torch
import PIL

from utils.transforms import UnNormalize
import matplotlib.pyplot as plt

PASCAL_VOC_classes = {
    0: "background",
    1: "airplane",
    2: "bicycle",
    3: "bird",
    4: "boat",
    5: "bottle",
    6: "bus",
    7: "car",
    8: "cat",
    9: "chair",
    10: "cow",
    11: "table",
    12: "dog",
    13: "horse",
    14: "motorbike",
    15: "person",
    16: "potted_plant",
    17: "sheep",
    18: "sofa",
    19: "train",
    20: "tv",
    # 21: "void",
}

class LogPredictionsCallback(Callback):

    def on_validation_batch_end(
        self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx
    ):
        """Called when the validation batch ends."""

        # `outputs` comes from `LightningModule.validation_step`
        # which corresponds to our model predictions in this case

        # Let's log 20 sample image predictions from first batch
        if batch_idx == 0:
            self.log_images("validation", batch, 5, outputs)

    def on_train_batch_end(
        self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx
    ):
        """Called when the training batch ends."""

        # `outputs` comes from `LightningModule.validation_step`
        # which corresponds to our model predictions in this case

        # Let's log 20 sample image predictions from first batch
        if batch_idx == 0:
            self.log_images("train", batch, 5, outputs)

    def log_images(self, name, batch, n, outputs):

            x, y = batch
            images = x[:n].cpu()
            ground_truth = np.array(y[:n].cpu())

            if name == "train":
                outputs = outputs["preds"] # preds

            predictions = np.array(outputs[:n].cpu())
            
            samples = []

            mean = np.array([0.485, 0.456, 0.406]) # TODO this is not beautiful
            std = np.array([0.229, 0.224, 0.225])

            for i in range(len(batch)):

                bg_image = images[i].numpy().transpose((1, 2, 0))
                mean = np.array([0.485, 0.456, 0.406])
                std = np.array([0.229, 0.224, 0.225])
                bg_image = std * bg_image + mean
                bg_image = np.clip(bg_image, 0, 1)

                prediction_mask = predictions[i]
                true_mask = ground_truth[i]

                samples.append(
                    wandb.Image(
                        bg_image,
                        masks={
                            "prediction": {
                                "mask_data": prediction_mask,
                                "class_labels": PASCAL_VOC_classes,
                            },
                            "ground truth": {
                                "mask_data": true_mask,
                                "class_labels": PASCAL_VOC_classes,
                            },
                        }, 
                    )
                )
            wandb.log({name:samples})

class LogFeatureVisualizationCallback(Callback):
    # TODO add feature vizualization for training and validation data
    # should probably use hooks to keep the model structure
    # classe image = classe predominante dans l'image + prendre features encoder
    pass

class LogAttentionVisualizationCallback(Callback):
    # TODO add attention vizualization for training and validation data
    # should probably use hooks to keep the model structure
    # classe image = classe predominante dans l'image + prendre features encoder
    # We shall use the activation map in order to visualize the effective receptive fields
    # those can be obtained by projecting the activation maps from upper layers
    # and resizing with a deconvolution or with interpolation ?
    # the original paper uses an average over 1000 images, this can also be considered.
    pass