import os
import random
from dataclasses import dataclass
from os import path as osp
from typing import Any, ClassVar, Dict, List, Optional

import numpy as np
import simple_parsing
import torch
import torch.optim
from simple_parsing.helpers import Serializable, choice, dict_field, list_field


@dataclass
class Hparams:
    """Hyperparameters of for the run"""

    
    wandb_entity  : str  = "recvis"         # name of the project
    test          : bool = True             # test code before running
    wandb_project : str  = (f"{'test-'*test}sem-seg")       # name of the wandb entity, here our team
    save_dir      : str  = osp.join(os.getcwd(), "wandb")   # directory to save wandb outputs


    agent       : str           = "trainer"         # trainer agent to use for training
    arch        : str           = "BarlowTwins"     # architecture to use
    datamodule  : str           = "BarlowTwins"     # lighting datamodule @TODO will soon be deleted since it is the same, get datamodule will use arch
    dataset     : Optional[str] = "BarlowTwinsDataset"         # dataset, use <Dataset>Eval for FT
    weights_path: str           = osp.join(os.getcwd(), "weights") # path to save weights
    asset_path  : str           = osp.join(os.getcwd(), "assets")  # path to download datasets
        
    seed_everything: Optional[int] = None   # seed for the whole run
    tune_lr        : bool          = False  # tune the model on first run
    tune_batch_size: bool          = False  # tune the model on first run
    gpu            : int           = 1      # number or gpu
    precision      : int           = 32     # precision
    val_freq       : int           = 1      # validation frequency
    accumulate_size: int           = 256   # gradient accumulation batch size
    max_epochs     : int           = 400    # maximum number of epochs
    dev_run        : bool          = False  # developpment mode, only run 1 batch of train val and test


@dataclass
class DatasetParams:
    """Dataset Parameters
    ! The batch_size and number of crops should be defined here
    """
    
    num_workers       : int         = 20         # number of workers for dataloadersint
    input_size        : tuple       = (32, 32)   # image_size
    batch_size        : int         = 256        # batch_size
    asset_path        : str         = osp.join(os.getcwd(), "assets")  # path to download the dataset
    n_crops           : int         = 5          # number of crops/global_crops
    n_global_crops    : int         = 2          # number of global crops
    global_crops_scale: List[int]   = list_field(0.5, 1)      # scale range of the global crops
    local_crops_scale : List[float] = list_field(0.05, 0.5)   # scale range of the local crops
    # @TODO the numbner of classes should be contained in the dataset and extracted automatically for the network?

@dataclass
class OptimizerParams:
    """Optimization parameters"""

    optimizer           : str            = "Adam"  # Optimizer (adam, rmsprop)
    lr                  : float          = 3e-4     # learning rate,                             default = 0.0002
    lr_sched_type       : str            = "step"   # Learning rate scheduler type.
    min_lr              : float          = 5e-6     # minimum lr for the scheduler
    betas               : List[float]    = list_field(0.9, 0.999)  # beta1 for adam. default = (0.9, 0.999)
    warmup_epochs       : int            = 40
    max_epochs          : int            = 400
    scheduler_parameters: Dict[str, Any] = dict_field(
        dict(
            warmup_start_lr    = 0.9995,
            max_epochs         = 0,
            warmup_epochs      = warmup_epochs,
        )
    )
    

@dataclass
class CallBackParams:
    """Parameters to use for the logging callbacks
    """
    log_erf_freq       : int   = 10     # effective receptive fields
    nb_erf             : int   = 6
    log_att_freq       : int   = 10     # attention maps
    log_pred_freq      : int   = 10     # log_pred_freq
    log_ccM_freq       : int   = 1      # log cc_M matrix frequency
    log_dino_freq      : int   = 1      # log output frrequency for dino
    attention_threshold: float = 0.5    # Logging attention threshold for head fusion
    nb_attention       : int   = 5      # nb of images for which the attention will be visualised

@dataclass
class MetricsParams:
    num_classes : int       = 21        # number of classes for the segmentation task
    average     : str       = "weighted"
    mdmc_average: str       = "global"
    ignore_index: int       = 21
    metrics     : List[str] = list_field("Accuracy","Recall","Precision","F1","IoU") # name of the metrics which will be used

    

@dataclass
class BarlowConfig:
    """Hyperparameters specific to Barlow Twin Model.
    Used when the `arch` option is set to "Barlow" in the hparams
    """
    
    # lambda coefficient used to scale the scale of the redundancy loss
    # so it doesn't overwhelm the invariance loss
    backbone              : str           = "resnet50"
    nb_proj_layers        : int           = 3         # nb projection layers, defaults is 3 should not move
    lmbda                 : float         = 5e-3
    bt_proj_dim           : int           = 2048      # number of channels to use for projection
    pretrained_encoder    : bool          = False     # use a pretrained model
    use_backbone_features : bool          = True      # only use backbone features for FT
    weight_checkpoint     : Optional[str] = osp.join(os.getcwd(),) # model checkpoint used in classification fine tuning
    backbone_parameters   : Optional[str] = None


@dataclass
class Parameters:
    """base options."""
    hparams       : Hparams         = Hparams()
    optim_param   : OptimizerParams = OptimizerParams()
    data_param    : DatasetParams   = DatasetParams()
    callback_param: CallBackParams  = CallBackParams()
    metric_param  : MetricsParams   = MetricsParams()
    def __post_init__(self):
        """Post-initialization code"""
        # Mostly used to set some values based on the chosen hyper parameters
        # since we will use different models, backbones and datamodules
        
        
        # Set render number of channels
        if "BarlowTwins" in self.hparams.arch:
            self.network_param: BarlowConfig = BarlowConfig()
        
        # Set random seed
        if self.hparams.seed_everything is None:
            self.hparams.seed_everything = random.randint(1, 10000)
            
            
            
        if self.network_param.backbone == "vit":
            self.network_param.backbone_parameters = dict(
                image_size      = self.data_param.input_size[0],
                patch_size      = self.data_param.input_size[0]//8,
                num_classes     = 0,
                dim             = 768,
                depth           = 4,
                heads           = 6,
                mlp_dim         = 1024,
                dropout         = 0.1,
                emb_dropout     = 0.1,
            )
        
        print("Random Seed: ", self.hparams.seed_everything)
        random.seed(self.hparams.seed_everything)
        torch.manual_seed(self.hparams.seed_everything)
        if not self.hparams.gpu != 0:
            torch.cuda.manual_seed_all(self.hparams.seed_everything)

    @classmethod
    def parse(cls):
        parser = simple_parsing.ArgumentParser()
        parser.add_arguments(cls, dest="parameters")
        args = parser.parse_args()
        instance: Parameters = args.parameters
        return instance
