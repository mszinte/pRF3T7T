"""
-----------------------------------------------------------------------------------------
load_dataset.py
-----------------------------------------------------------------------------------------
Goal of the script:
Load dataset and create webviewer
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject 
sys.argv[2]: acq
sys.argv[3]: model
sys.argv[4]: prf_sign or tc
sys.argv[5]: recache
-----------------------------------------------------------------------------------------
Output(s):
None
-----------------------------------------------------------------------------------------
To run:
python post_fit/load_dataset.py sub-01 acq-2mm gauss pos 1
python post_fit/load_dataset.py sub-01 acq-2mm gauss tc 1
python post_fit/load_dataset.py sub-01 acq-2p5mm gauss pos 1
python post_fit/load_dataset.py sub-01 acq-2p5mm gauss tc 1
> to run localy
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
import ipdb
import platform
import time
import matplotlib.pyplot as plt
opj = os.path.join
deb = ipdb.set_trace

# MRI imports
# -----------
import nibabel as nb
import cortex

# Functions import
# ----------------
from utils import set_pycortex_config_file

# Get inputs
# ----------
subject = sys.argv[1]
acq = sys.argv[2]
model = sys.argv[3]
prf_sign = sys.argv[4]
recache = int(sys.argv[5])
if recache == 1: recache_val = True
else: recache_val = False

# Define analysis parameters
# --------------------------
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# Define folder
# -------------
base_dir = analysis_info['base_dir']
base_dir_local = analysis_info['base_dir_local']
account = analysis_info['account']

# Copy dataset locally
# --------------------
print('copy dataset to temp folder...')
dataset_dir_ori = "{account}:{base_dir}/pp_data/{subject}/{model}/pycortex_outputs/dataset/{prf_sign}/".format(
                            account = account, base_dir = base_dir, subject = subject, model = model, prf_sign = prf_sign)
dataset_file = "{acq}_{prf_sign}.hdf".format(acq = acq, prf_sign = prf_sign)

trans_cmd = 'rsync --progress'
dataset_dir_dest = analysis_info['local_temp']
os.system('{trans_cmd} {ori_dir}{file} {dest_dir}'.format(trans_cmd = trans_cmd, 
							ori_dir = dataset_dir_ori, file = dataset_file, dest_dir = dataset_dir_dest))

# Set pycortex db and colormaps
# -----------------------------
set_pycortex_config_file(base_dir_local)

print('load dataset...')
ds = cortex.dataset.Dataset.from_file("{file_dir}{file}".format(file_dir = dataset_dir_dest,file = dataset_file))

print('create webgl...')
cortex.webgl.show(data = ds, recache = recache_val)
time.sleep(15)
