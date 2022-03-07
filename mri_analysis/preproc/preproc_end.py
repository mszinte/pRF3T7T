"""
-----------------------------------------------------------------------------------------
preproc_end.py
-----------------------------------------------------------------------------------------
Goal of the script:
Arrange and average runs including leave-one-out averaging procedure
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name
-----------------------------------------------------------------------------------------
Output(s):
# Preprocessed timeseries files
-----------------------------------------------------------------------------------------
To run:
1. cd to function
>> cd /home/mszinte/projects/PredictEye/mri_analysis/
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
dest_folder1 = "{base_dir}/pp_data_new/{sub}/func/fmriprep_dct".format(base_dir=base_dir, sub=sub_name)
try: os.makedirs(dest_folder1)
except: pass

dest_folder2 = "{base_dir}/pp_data_new/{sub}/func/fmriprep_dct_pca".format(base_dir=base_dir, sub=sub_name)
try: os.makedirs(dest_folder2)
except: pass

dest_folder3 = "{base_dir}/pp_data_new/{sub}/loo/fmriprep_dct".format(base_dir=base_dir, sub=sub_name)
try: os.makedirs(dest_folder3)
except: pass

dest_folder4 = "{base_dir}/pp_data_new/{sub}/loo/fmriprep_dct_pca".format(base_dir=base_dir, sub=sub_name)
try: os.makedirs(dest_folder4)
except: pass


orig_folder = "{base_dir}/deriv_data/pybest_new/{sub}".format(base_dir=base_dir, sub=sub_name)

for task_num, task_name in enumerate(analysis_info['task_names']):
    for task_run in np.arange(0,analysis_info['task_runs'][task_num],1):
        for ses_num,ses_name in enumerate(next(os.walk(orig_folder))[1]):
            for file_end in file_ends:
                # dct func

                orig_file1 = "{orig_fold}/{ses}/preproc/{sub}_{ses}_task-{task_name}_run-{task_run}_space-{reg}_desc-preproc_bold{file_end}".format(
                                        orig_fold=orig_folder, sub=sub_name, ses=ses_name, task_name=task_name, reg=regist_type, task_run=task_run+1, file_end=file_end)
                dest_file1 = "{dest_fold}/{sub}_task-{task_name}_run-{task_run}_space-{reg}_fmriprep_dct{file_end}".format(
                                        dest_fold=dest_folder1, sub=sub_name, task_name=task_name, reg=regist_type, task_run=task_run+1, file_end=file_end)

                if os.path.isfile(orig_file1):
                    os.system("{cmd} {orig} {dest}".format(cmd=trans_cmd, orig=orig_file1, dest=dest_file1))

                # dct + denoised func
                orig_file2 = "{orig_fold}/{ses}/denoising/{sub}_{ses}_task-{task_name}_run-{task_run}_space-{reg}_desc-denoised_bold{file_end}".format(
                                        orig_fold=orig_folder, sub=sub_name, ses=ses_name, task_name=task_name, reg=regist_type, task_run=task_run+1, file_end=file_end)
                dest_file2 = "{dest_fold}/{sub}_task-{task_name}_run-{task_run}_space-{reg}_fmriprep_dct_pca{file_end}".format(
                                        dest_fold=dest_folder2, sub=sub_name, task_name=task_name, reg=regist_type, task_run=task_run+1, file_end=file_end)

                if os.path.isfile(orig_file2):
                    os.system("{cmd} {orig} {dest}".format(cmd=trans_cmd, orig=orig_file2, dest=dest_file2))

# Average tasks runs
for preproc in analysis_info['preproc']:
    for task_name in analysis_info['task_names']:
        for file_end in file_ends:
            print('avg: '+task_name+' type: '+file_end)

            file_list = sorted(glob.glob("{base_dir}/pp_data_new/{sub}/func/{preproc}/*{task_name}*_space-{reg}_{preproc}{file_end}".format(
                                         base_dir=base_dir, sub=sub_name, preproc=preproc,task_name=task_name, reg=regist_type, file_end=file_end)))
            
            if len(file_list):
                
                # save
                new_file = "{base_dir}/pp_data_new/{sub}/func/{sub}_task-{task_name}_space-{reg}_{preproc}_avg{file_end}".format(
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

# Leave-one-out averages
for preproc in analysis_info['preproc']:
    for task_name in analysis_info['task_names']:
        for file_end in file_ends:
            

            file_list = sorted(glob.glob("{base_dir}/pp_data_new/{sub}/func/{preproc}/*{task_name}*_space-{reg}_{preproc}{file_end}".format(
                                         base_dir=base_dir, sub=sub_name, preproc=preproc,task_name=task_name, reg=regist_type, file_end=file_end)))
            
            if len(file_list):
                combi = list(it.combinations(file_list, len(file_list)-1))
                
                for loo_num, avg_runs in enumerate(combi):
                    print('loo avg %i: '%loo_num +task_name+' type: '+file_end)
                    
                    # compute average between loo runs
                    new_file_avg = "{base_dir}/pp_data_new/{sub}/loo/{preproc}/{sub}_task-{task_name}_space-{reg}_{preproc}_avg-{loo_num}{file_end}".format(
                                base_dir=base_dir, sub=sub_name, preproc=preproc, task_name=task_name, reg=regist_type, file_end=file_end, loo_num=loo_num+1)
                    
                    if regist_type == 'fsLR_den-170k':

                        img = np.load(file_list[0])
                        data_avg = np.zeros(img.shape)

                        for avg_run in avg_runs:
                            print('avg run: '+avg_run)
                            data_val = []
                            data_val = np.load(avg_run)
                            data_avg += data_val/len(avg_runs)
                            np.save(new_file_avg, data_avg)

                    else: 
                        img = nb.load(file_list[0])
                        data_avg = np.zeros(img.shape)

                        for avg_run in avg_runs:
                            print('avg add: '+avg_run)
                            data_val = []
                            data_val_img = nb.load(avg_run)
                            data_val = data_val_img.get_fdata()
                            data_avg += data_val/len(avg_runs)

                        new_img = nb.Nifti1Image(dataobj=data_avg, affine=img.affine, header=img.header)
                        new_img.to_filename(new_file_avg)
                        
                        
                    # copy loo run (left one out run)
                    for run in file_list:
                        if run not in avg_runs:
                            
                            new_file_loo = "{base_dir}/pp_data_new/{sub}/loo/{preproc}/{sub}_task-{task_name}_space-{reg}_{preproc}_loo-{loo_num}{file_end}".format(
                                            base_dir=base_dir, sub=sub_name, preproc=preproc, task_name=task_name, reg=regist_type, file_end=file_end, loo_num=loo_num+1)
                                                        
                            print('loo run: '+run)
                            os.system("{cmd} {orig} {dest}".format(cmd=trans_cmd, orig=run, dest=new_file_loo))

                    
                                
# Anatomy
output_files = ['dseg','desc-preproc_T1w','desc-aparcaseg_dseg','desc-aseg_dseg','desc-brain_mask']
orig_folder = "{base_dir}/deriv_data/fmriprep_new/fmriprep/{sub}".format(base_dir=base_dir, sub=sub_name)

dest_folder_anat = "{base_dir}/pp_data_new/{sub}/anat".format(base_dir=base_dir, sub=sub_name)
try: os.makedirs(dest_folder_anat)
except: pass

if regist_type == 'T1w':
    for output_file in output_files:
        
        orig_file = "{orig_fold}/ses-01/anat/{sub}_ses-01_{output_file}.nii.gz".format(orig_fold=orig_folder, sub=sub_name, output_file=output_file)
        dest_file = "{dest_fold}/{sub}_{output_file}.nii.gz".format(dest_fold=dest_folder_anat, sub=sub_name, output_file=output_file)

        if os.path.isfile(orig_file):
            os.system("{cmd} {orig} {dest}".format(cmd=trans_cmd, orig=orig_file, dest=dest_file))