"""
-----------------------------------------------------------------------------------------
post_fit.py
-----------------------------------------------------------------------------------------
Goal of the script:
Combine fit files, compute pRF derivatives
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name (e.g. sub-01)
sys.argv[2]: task (pRF3T, pRF7T)
sys.argv[3]: registration (e.g. T1w)
sys.argv[4]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[5]: cifti data mode (subc: subcortical, surf: surface)
-----------------------------------------------------------------------------------------
Output(s):
Combined estimate nifti file and pRF derivative nifti file
-----------------------------------------------------------------------------------------
To run:
>> cd to function
>> python prf/post_fit/post_fit.py [subject] [task] [reg] [preproc] [cifti-mode]
-----------------------------------------------------------------------------------------
Exemple:
cd /home/mszinte/projects/pRF3T7T/mri_analysis/
python prf/post_fit/post_fit.py sub-01 pRF3T T1w fmriprep_dct
python prf/post_fit/post_fit.py sub-01 pRF7T T1w fmriprep_dct
python prf/post_fit/post_fit.py sub-04 pRF7T T1w fmriprep_dct
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
import glob
import numpy as np
import ipdb
deb = ipdb.set_trace

# Functions import
# ----------------
from utils.utils import prf_fit2deriv

# MRI analysis imports
# --------------------
import nibabel as nb

# Define analysis parameters
# --------------------------
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# Settings
# --------
# Inputs
subject = sys.argv[1]
task = sys.argv[2]
if task == 'pRF3T': task_num = 0
elif task == 'pRF7T': task_num = 1
regist_type = sys.argv[3]
preproc = sys.argv[4]
if regist_type == 'fsLR_den-170k':
    cifti_mode= sys.argv[5]
    if cifti_mode == 'surf': file_ext,sh_end = '.npy','_surface'
    elif cifti_mode == 'subc': file_ext,sh_end = '_subc.npy','_subcortical'
else:
    file_ext = '.nii.gz'
    sh_end = ''

base_dir = analysis_info['base_dir']
stim_width = analysis_info['stim_width'][task_num]
stim_height = analysis_info['stim_height'][task_num]

# Create job and log output folders
fit_fn = "{base_dir}/derivatives/pp_data/{sub}/prf/fit/{sub}_task-{task}_space-{reg}_{preproc}_avg_prf-fit{file_ext}".format(
                base_dir=base_dir, sub=subject, reg=regist_type, preproc=preproc, file_ext=file_ext, task=task)
deriv_fn = "{base_dir}/derivatives/pp_data/{sub}/prf/fit/{sub}_task-{task}_space-{reg}_{preproc}_avg_prf-deriv{file_ext}".format(
                base_dir=base_dir, sub=subject, reg=regist_type, preproc=preproc, file_ext=file_ext, task=task)

if os.path.isfile(fit_fn) == False:
    sys.exit('Missing files, analysis stopped : {}'.format(fit_fn))
else:
    print('Computing derivatives: {}'.format(deriv_fn))
    
    # Compute derivatives
    # Load data
    if regist_type == 'fsLR_den-170k': 
        fit_mat = np.load(fit_fn)
    else: 
        fit_img = nb.load(fit_fn)
        fit_mat = fit_img.get_fdata()

    deriv_mat = prf_fit2deriv(input_mat=fit_mat, stim_width=stim_width, stim_height=stim_height)
    
    # save data
    if regist_type == 'fsLR_den-170k':
        np.save(deriv_fn, deriv_mat)
    else: 
        deriv_img = nb.Nifti1Image(dataobj=deriv_mat, affine=fit_img.affine, header=fit_img.header)
        deriv_img.to_filename(deriv_fn)