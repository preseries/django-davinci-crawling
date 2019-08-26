#!/bin/sh
#
# Usage: prepare-lab-env.sh -n environment-name
#        prepare-lab-env.sh -n davinvi-crawling-lab
#
# In order to execute conda and activate conda environments we need to
# setup accordingly the terminal session.
# echo ". $HOME/anaconda/etc/profile.d/conda.sh" >> ~/.bash_profile

DIRECTORY="$( cd "$(dirname "$0")" ; pwd -P )"

ENV_NAME=

while :; do
    case $1 in
        -n|--name) ENV_NAME=$2
        ;;
    *) break
    esac
    shift 2
done

if [ -z "$ENV_NAME" ]
then
      echo "The environment name must be specified"
      exit 2
fi

# Create the environment using conda. We need python 3.7 (ipywidgets)
conda create -y -n $ENV_NAME pip python=3.7

# Activating the environment
source $HOME/anaconda/bin/activate $ENV_NAME

# Installing JupyterLab
conda install -y jupyterlab

# Generate the config file to do some changes on it
mkdir .jupyter
jupyter notebook -y --config=.jupyter/jupyter_notebook_config.py --generate-config

# Configure Jupyter to be made available beyond localhost
from_str="#c.NotebookApp.ip = 'localhost'"
to_str="c.NotebookApp.ip = '*'"
sed -i 's/${from_str}/${to_str}/g' .jupyter/jupyter_notebook_config.py

# Configure JupyterLab to have access to the python environment
pip install ipykernel
ipython kernel install --user --name=$ENV_NAME

# Installing DSE driver
pip install dse-driver

# Installing pandas using conda
conda install -y pandas

# Installing Altair
conda install -y -c conda-forge altair vega_datasets

# Installing interactive widgets and the JupyterLab extensions
conda install -y -c conda-forge ipywidgets
conda install -y nodejs
jupyter labextension install @jupyter-widgets/jupyterlab-manager

# Installing Jupyter Themes and Setting a theme
conda install -c conda-forge jupyterthemes
jt -t chesterish
