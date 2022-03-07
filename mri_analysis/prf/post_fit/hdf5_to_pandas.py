"""
-----------------------------------------------------------------------------------------
roi_to_pandas.py
-----------------------------------------------------------------------------------------
Goal of the script:
Create pandas dataframe from hdf5 files
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name (e.g. 'sub-001')
sys.argv[2]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[3]: registration (e.g. T1w)
sys.argv[4]: task
sys.argv[5]: sub-task
-----------------------------------------------------------------------------------------
Output(s):
pandas csv file per subject
-----------------------------------------------------------------------------------------
To run:
>> cd to function
>> python post_fit/hdf5_to_pandas.py [subject] [preproc] [reg] [task] [sub-task]
-----------------------------------------------------------------------------------------
Exemple:
cd /home/mszinte/projects/PredictEye/mri_analysis/
python post_fit/hdf5_to_pandas.py sub-01 fmriprep_dct T1w pRF
python post_fit/hdf5_to_pandas.py sub-01 fmriprep_dct T1w pMF sac
python post_fit/hdf5_to_pandas.py sub-01 fmriprep_dct T1w pMF sp
-----------------------------------------------------------------------------------------
Written by Martin Szinte (martin.szinte@gmail.com)
-----------------------------------------------------------------------------------------
"""

# General imports
# ---------------
import os, sys, json, glob, ipdb, h5py, scipy.io
import numpy as np
import pandas as pd
opj = os.path.join
deb = ipdb.set_trace

# MRI imports
# -----------
import nibabel as nb
import cortex

# Get inputs
# ----------
subject = sys.argv[1]
preproc = sys.argv[2]
regist_type = sys.argv[3]
task = sys.argv[4]
if len(sys.argv) < 6: sub_task = ''
else: sub_task = sys.argv[5]

# Define analysis parameters
# --------------------------
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# Define folders and settings
# ---------------------------
base_dir = analysis_info['base_dir']
rois = analysis_info['rois']
rois_mask_dir = "{}/pp_data/{}/gauss/roi_masks/".format(base_dir, subject)
deriv_dir = "{}/pp_data/{}/gauss/fit/{}".format(base_dir, subject,task)
h5_dir = "{}/pp_data/{}/gauss/h5/{}{}".format(base_dir, subject, task, sub_task)
pandas_dir = "{}/pp_data/{}/gauss/pandas/{}{}".format(base_dir, subject, task, sub_task)

# save dataframe
try: os.makedirs(pandas_dir)
except: pass


rsq_idx, ecc_idx, polar_real_idx, polar_imag_idx , size_idx, \
    amp_idx, baseline_idx, cov_idx, x_idx, y_idx, hemi_idx = 0,1,2,3,4,5,6,7,8,9,10

# Create dataframe
# ---------------


for roi_num, roi in enumerate(rois):

    print('creating {} {} {} pandas file'.format(roi, preproc, regist_type))

    # load h5 file
    h5_file = h5py.File("{}/{}_{}_{}.h5".format(h5_dir, roi, preproc, regist_type),'r')

    # load deriv data
    deriv_data = h5_file['{}{}/derivatives'.format(task, sub_task)]
    
    # load time course data
    tc_data = h5_file['{}{}/time_course'.format(task, sub_task)]

    # load model time course data
    tc_model_data = h5_file['{}{}/time_course_model'.format(task, sub_task)]

    # load coordinates data
    coord_data = h5_file['{}{}/coord'.format(task, sub_task)]

    # define dataframe
    df_roi = pd.DataFrame(deriv_data,columns = ['rsq','ecc','polar_real','polar_imag','size','amp','baseline','cov','x','y','hemi'])
    df_roi['roi']=[roi for x in range(df_roi.shape[0])]
    df_roi['subject']=[subject for x in range(df_roi.shape[0])]
    df_roi['task']=[task for x in range(df_roi.shape[0])]
    df_roi['sub_task']=[sub_task for x in range(df_roi.shape[0])]
    df_roi['signal_tc']=pd.Series(data=tc_data)
    df_roi['model_tc']=pd.Series(data=tc_model_data)
    df_roi['voxel_coords']=pd.Series(data=coord_data)

    df_name = '{}/{}_{}_{}.gz'.format(pandas_dir, roi, preproc, regist_type)

    df_roi.to_pickle(df_name,compression='gzip')