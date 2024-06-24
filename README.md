This is what I explored and worked with new SOMOS dataset during my Independent Project at MIDAS Lab

Trained MOS prediction models on different datasets using self-supervised learning model for speech, wav2vec2. Achieved
a 45% improvement in MOS prediction accuracy compared to SOTA models on the SOMOS dataset.

Also leveraged Tacotron2 with TOBI labels to identify prosodic variations which give better naturalness scores (LCC,SRCC)

[Data and pretrained models on Zenodo](https://zenodo.org/records/8409156)

Implentation of the [PRS paper](https://arxiv.org/abs/2310.05078).


## Downloads: 
Download the data and pre-trained weights from zenodo in a folder named ASRU. We use the full path to ASRU folder to set up the REF variable later. We only provide PRS pre-trained weights for stage2. 

## Environment: 
Create a conda environment using the env.yaml
``` conda env create -f env.yaml ```

## Environment-variable
Set the environment variable in linux based machine using this
``` export REF="path/to/the/ASRU/"  ```
