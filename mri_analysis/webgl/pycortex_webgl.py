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
base_dir = sys.argv[1]
subject = sys.argv[2]
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
webgl_dir = '{}/webgl/{}/'.format(base_dir, subject)
try: os.makedirs(webgl_dir)
except: pass

# Load flatmaps

# pRF maps
prf_dataset_folder = '{}/pp_data/{}/gauss/pycortex_outputs/flatmaps/prf'.format(base_dir, subject)
prf_dataset_file = "{}/{}_space-{}_prf.hdf".format(prf_dataset_folder, subject, regist_type, preproc)
prf_dataset = cortex.load(prf_dataset_file)

# sac-fix glm maps
type_maps = ['SacFix','PurFix','PurEndo-Fix','PurExo-Fix','PurExo-PurEndo',\
             'SacEndo-Fix','SacExo-Fix','SacExo-SacEndo']

for type_map in type_maps:
    exec("{type_map}_dataset_file) = '{base_dir}/pp_data/{subject}/glm/pycortex_outputs/flatmaps/{type_map}/{subject}_space-{regist_type}_{preproc}_glm_{type_map}.hdf'".format(
         type_map=type_map, base_dir=base_dir,subject=subject))

    

sacfix_dataset_folder = '{}/pp_data/{}/glm/pycortex_outputs/flatmaps/{}'.format(base_dir, subject, 'Sac-Fix')
sacfix_dataset_file = "{}/{}_space-{}_{}_glm_{}.hdf".format(sacfix_dataset_folder, subject, regist_type, preproc, 'Sac-Fix')
sacfix_dataset = cortex.load(sacfix_dataset_file)

# sac-fix glm maps
purfix_dataset_folder = '{}/pp_data/{}/glm/pycortex_outputs/flatmaps/{}'.format(base_dir, subject, 'Pur-Fix')
purfix_dataset_file = "{}/{}_space-{}_{}_glm_{}.hdf".format(purfix_dataset_folder, subject, regist_type, preproc, 'Pur-Fix')
purfix_dataset = cortex.load(purfix_dataset_file)

# PurEndo-Fix glm maps
# PurExo-Fix glm maps
# PurExo-PurEndo glm maps

# SacEndo-Fix glm maps
# SacExo-Fix glm maps
# SacExo-SacEndo glm maps


# put together
new_dataset = cortex.Dataset(prf = prf_dataset, sacfix = sacfix_dataset, purfix = purfix_dataset)
cortex.webgl.make_static(outpath=webgl_dir, data=new_dataset, recache=recache)

# Send to webapp
# --------------
if webapp == True:
    webapp_dir = '{}/{}'.format(analysis_info['webapp_dir'],subject)
    os.system('rsync -avuz --progress {local_dir} {webapp_dir}'.format(local_dir=webgl_dir, webapp_dir=webapp_dir))
    print('go to : https://invibe.nohost.me/predicteye/{}'.format(subject))