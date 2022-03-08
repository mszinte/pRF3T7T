"""
-----------------------------------------------------------------------------------------
pycortex_webgl.py
-----------------------------------------------------------------------------------------
Goal of the script:
Create webgl pycortex across tasks
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: directory to mesocentre disk (e.g. ~/disks/meso_S/)
sys.argv[2]: subject name (e.g. 'sub-01')
sys.argv[3]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[4]: registration (e.g. T1w)
sys.argv[5]: recache db (1 = True, 0 = False)
sys.argv[6]: send to invibe server (1 = True, 0 = False)
--------------------------------------------------------------------------------------- --
Output(s):
pycortex webgl per subject
-----------------------------------------------------------------------------------------
To run:
>> cd to function
>> python webgl/pycortex_webgl.py [base_dir] [subject] [preproc] [reg] [recache] [invibe]
-----------------------------------------------------------------------------------------
Exemple: on mesocentre
cd ~/projects/PredictEye/mri_analysis/
python webgl/pycortex_webgl.py /scratch/mszinte/data/PredictEye sub-01 fmriprep_dct T1w 1 1
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

# Get inputs
# ----------
subject = sys.argv[1]
preproc = sys.argv[3]
regist_type = sys.argv[4]
recache = bool(int(sys.argv[5]))
webapp = bool(int(sys.argv[6]))

# Define analysis parameters
# --------------------------
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# create folder
base_dir = analysis_info["base_dir"]
datasets_dir = '{}/pp_data/{}/prf/pycortex/datasets'.format(base_dir, subject)

webgl_dir = '{}/webgl/{}_{}/'.format(base_dir, subject, preproc)
try: os.makedirs(webgl_dir)
except: pass

# Load datasets
prf3T_dataset_file = "{}/{}_task-pRF3T_space-{}_{}.hdf".format(datasets_dir, subject, task, regist_type, preproc)
prf3T_dataset = cortex.load(prf3T_dataset_file)

prf7T_dataset_file = "{}/{}_task-pRF7T_space-{}_{}.hdf".format(datasets_dir, subject, task, regist_type, preproc)
prf7T_dataset = cortex.load(prf7T_dataset_file)

# Put them together
new_dataset = cortex.Dataset(pRF3T = prf3T_dataset, pRF7T = prf7T_dataset)
cortex.webgl.make_static(outpath=webgl_dir, data=new_dataset, recache=recache)

# Send to webapp
# --------------
if webapp == True:
    webapp_dir = '{}/{}_{}'.format(analysis_info['webapp_dir'],subject,regist_type)
    os.system('rsync -avuz --progress {local_dir} {webapp_dir}'.format(local_dir=webgl_dir, webapp_dir=webapp_dir))
    print('go to : https://invibe.nohost.me/prf3t7t/{}'.format(subject))