"""
-----------------------------------------------------------------------------------------
preproc_end.py
-----------------------------------------------------------------------------------------
Goal of the script:
Arrange and average runs
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name
-----------------------------------------------------------------------------------------
Output(s):
# Preprocessed timeseries files
-----------------------------------------------------------------------------------------
To run:
1. cd to function
>> cd /home/mszinte/projects/pRF3T7T/mri_analysis/
2. run python command
python preproc/preproc_end.py [subject name] [registration_type]
-----------------------------------------------------------------------------------------
Exemple:
python preproc/preproc_end.py sub-01 T1w
python preproc/preproc_end.py sub-01 MNI152NLin2009cAsym-res-1
python preproc/preproc_end.py sub-01 fsLR_den-170k
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
import json
import sys
import os
import glob
import ipdb
import platform
import numpy as np
opj = os.path.join
deb = ipdb.set_trace

sub_name = sys.argv[1]
regist_type = sys.argv[2]

if regist_type == 'fsLR_den-170k':
    file_ends = ['.npy','_subc.npy']
else: 
    file_ends = ['.nii.gz']

# MRI analysis imports
# --------------------
import nibabel as nb
import itertools as it

with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)
trans_cmd = 'rsync -avuz --progress'

# Define cluster/server specific parameters
# -----------------------------------------
base_dir = analysis_info['base_dir'] 

# Copy files in pp_data folder
# ----------------------------
dest_folder1 = "{base_dir}/derivatives/pp_data/{sub}/func/fmriprep_dct".format(base_dir=base_dir, sub=sub_name)
try: os.makedirs(dest_folder1)
except: pass

if sub_name == 'sub-01':
    task_runs = [5,2]
elif sub_name == 'sub-02':
    task_runs = [5,2]
elif sub_name == 'sub-03':
    task_runs = [2,2]
elif sub_name == 'sub-04':
    task_runs = [0,2]
elif sub_name == 'sub-05':
    task_runs = [0,2]

orig_folder = "{base_dir}/derivatives/pybest/{sub}".format(base_dir=base_dir, sub=sub_name)

for task_num, task_name in enumerate(analysis_info['task_names']):
    for task_run in np.arange(0,task_runs[task_num],1):
        for ses_num,ses_name in enumerate(next(os.walk(orig_folder))[1]):
            for file_end in file_ends:
                # dct func
                orig_file1 = "{orig_fold}/{ses}/preproc/{sub}_{ses}_task-{task_name}_run-{task_run}_space-{reg}_desc-preproc_bold{file_end}".format(
                                        orig_fold=orig_folder, sub=sub_name, ses=ses_name, task_name=task_name, reg=regist_type, task_run=task_run+1, file_end=file_end)
                dest_file1 = "{dest_fold}/{sub}_task-{task_name}_run-{task_run}_space-{reg}_fmriprep_dct{file_end}".format(
                                        dest_fold=dest_folder1, sub=sub_name, task_name=task_name, reg=regist_type, task_run=task_run+1, file_end=file_end)

                if os.path.isfile(orig_file1):
                    os.system("{cmd} {orig} {dest}".format(cmd=trans_cmd, orig=orig_file1, dest=dest_file1))


# Average tasks runs
for preproc in analysis_info['preproc']:
    for task_name in analysis_info['task_names']:
        for file_end in file_ends:
            print('avg: '+task_name+' type: '+file_end)

            file_list = sorted(glob.glob("{base_dir}/derivatives/pp_data/{sub}/func/{preproc}/*{task_name}*_space-{reg}_{preproc}{file_end}".format(
                                         base_dir=base_dir, sub=sub_name, preproc=preproc,task_name=task_name, reg=regist_type, file_end=file_end)))
            

            if len(file_list):
                
                # save
                new_file = "{base_dir}/derivatives/pp_data/{sub}/func/{sub}_task-{task_name}_space-{reg}_{preproc}_avg{file_end}".format(
                            base_dir=base_dir, sub=sub_name, preproc=preproc, task_name=task_name, reg=regist_type, file_end=file_end)


                if regist_type == 'fsLR_den-170k':
                    img = np.load(file_list[0])
                    data_avg = np.zeros(img.shape)

                    for file in file_list:
                        print('add: '+file)
                        data_val = []
                        data_val = np.load(file)
                        data_avg += data_val/len(file_list)
                    np.save(new_file, data_avg)

                else: 
                    img = nb.load(file_list[0])
                    data_avg = np.zeros(img.shape)

                    for file in file_list:
                        print('add: '+file)
                        data_val = []
                        data_val_img = nb.load(file)
                        data_val = data_val_img.get_fdata()
                        data_avg += data_val/len(file_list)

                    new_img = nb.Nifti1Image(dataobj=data_avg, affine=img.affine, header=img.header)
                    new_img.to_filename(new_file)

                                
# Anatomy
output_files = ['dseg','desc-preproc_T1w','desc-aparcaseg_dseg','desc-aseg_dseg','desc-brain_mask']
orig_folder = "{base_dir}/derivatives/fmriprep/fmriprep/{sub}".format(base_dir=base_dir, sub=sub_name)

dest_folder_anat = "{base_dir}/derivatives/pp_data/{sub}/anat".format(base_dir=base_dir, sub=sub_name)
try: os.makedirs(dest_folder_anat)
except: pass

if sub_name == 'sub-02':ses = "ses-02"
else:ses = "ses-01"

if regist_type == 'T1w':
    for output_file in output_files:
        
        orig_file = "{orig_fold}/{ses}/anat/{sub}_{ses}_{output_file}.nii.gz".format(orig_fold=orig_folder, sub=sub_name, output_file=output_file, ses=ses)
        dest_file = "{dest_fold}/{sub}_{output_file}.nii.gz".format(dest_fold=dest_folder_anat, sub=sub_name, output_file=output_file)

        if os.path.isfile(orig_file):
            os.system("{cmd} {orig} {dest}".format(cmd=trans_cmd, orig=orig_file, dest=dest_file))