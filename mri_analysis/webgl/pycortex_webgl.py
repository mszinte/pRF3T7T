"""
-----------------------------------------------------------------------------------------
pycortex_webgl.py
-----------------------------------------------------------------------------------------
Goal of the script:
Create webgl pycortex across tasks
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name (e.g. 'sub-01')
sys.argv[2]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[3]: registration (e.g. T1w)
sys.argv[4]: recache db (1 = True, 0 = False)
sys.argv[5]: send to invibe server (1 = True, 0 = False)
--------------------------------------------------------------------------------------- --
Output(s):
pycortex webgl per subject
-----------------------------------------------------------------------------------------
To run:
>> cd to function
>> python webgl/pycortex_webgl.py [base_dir] [subject] [preproc] [reg] [recache] [invibe]
-----------------------------------------------------------------------------------------
Exemple: on mesocentre
cd ~/projects/pRF3T7T/mri_analysis/
python webgl/pycortex_webgl.py sub-01 fmriprep_dct T1w 1 1
python webgl/pycortex_webgl.py sub-04 fmriprep_dct T1w 1 1
-----------------------------------------------------------------------------------------
Written by Martin Szinte (martin.szinte@gmail.com)
-----------------------------------------------------------------------------------------
"""
# Stop warnings
# -------------
import warnings
warnings.filterwarnings("ignore")

# General imports
# ---------------
import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import ipdb
import h5py
deb = ipdb.set_trace

# MRI imports
# -----------
import nibabel as nb
import cortex

# Functions import
# ----------------
from utils.utils import draw_cortex_vertex, set_pycortex_config_file

# Get inputs
# ----------
subject = sys.argv[1]
preproc = sys.argv[2]
regist_type = sys.argv[3]
recache = bool(int(sys.argv[4]))
webapp = bool(int(sys.argv[5]))

# Define analysis parameters
# --------------------------
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)
    
# create folder
base_dir = analysis_info["base_dir"]
datasets_dir = '{}/derivatives/pp_data/{}/prf/pycortex/datasets'.format(base_dir, subject)

# Set pycortex db and colormaps
# -----------------------------
set_pycortex_config_file(base_dir)

webgl_dir = '{}/derivatives/webgl/{}_{}/'.format(base_dir, subject, preproc)
try: os.makedirs(webgl_dir)
except: pass

# Load datasets
if subject == 'sub-04':
    prf7T_dataset_file = "{}/{}_task-pRF7T_space-{}_{}.hdf".format(datasets_dir, subject, regist_type, preproc)
    prf7T_dataset = cortex.load(prf7T_dataset_file)
elif subject == 'sub-05':
    prf7T_dataset_file = "{}/{}_task-pRF7T_space-{}_{}.hdf".format(datasets_dir, subject, regist_type, preproc)
    prf7T_dataset = cortex.load(prf7T_dataset_file)
else:
    prf3T_dataset_file = "{}/{}_task-pRF3T_space-{}_{}.hdf".format(datasets_dir, subject, regist_type, preproc)
    prf3T_dataset = cortex.load(prf3T_dataset_file)

    prf7T_dataset_file = "{}/{}_task-pRF7T_space-{}_{}.hdf".format(datasets_dir, subject, regist_type, preproc)
    prf7T_dataset = cortex.load(prf7T_dataset_file)

# Put them together
if subject == 'sub-04':
    new_dataset = cortex.Dataset(pRF7T = prf7T_dataset)
elif subject == 'sub-05':
    new_dataset = cortex.Dataset(pRF7T = prf7T_dataset)
else:
    new_dataset = cortex.Dataset(pRF3T = prf3T_dataset, pRF7T = prf7T_dataset)
    
cortex.webgl.make_static(outpath=webgl_dir, data=new_dataset, recache=recache)

# Send to webapp
# --------------
if webapp == True:

    webapp_dir = '{}{}_{}/'.format(analysis_info['webapp_dir'], subject, preproc)
    os.system('rsync -avuz --progress {local_dir} {webapp_dir}'.format(local_dir=webgl_dir, webapp_dir=webapp_dir))
    print('go to : https://invibe.nohost.me/prf3t7t/{}_{}'.format(subject, preproc))