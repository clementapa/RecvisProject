"""
Auteur: Arthur Zucker
- Capture configuration
- Update with argvs
- launches training through agent
"""
from __future__ import absolute_import, division

from pytorch_lightning import seed_everything
from simple_parsing import ArgumentParser

from pytorch_lightning.loggers import WandbLogger
from agents import *
from config.hparams import hparams
import wandb
# from apex import amp
parser = ArgumentParser()
# automatically add arguments for all the fields of the classes in hparams:
parser.add_arguments(hparams, dest="hparams")
args = parser.parse_args()


def main():
    # initialize wandb instance
    run = WandbLogger(config=vars(args.hparams), project=args.hparams.wandb_project, entity = args.hparams.wandb_entity, allow_val_change=True)
    config = run.experiment.config
    seed_everything(config.seed_everything)

    # Create the Agent and pass all the configuration to it then run it..
    agent_class = globals()[config.agent]
    agent = agent_class(config, run)
    # run the model
    agent.run()
    agent.finalize()


if __name__ == "__main__":
    main()