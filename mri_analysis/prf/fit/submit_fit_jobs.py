"""
-----------------------------------------------------------------------------------------
submit_fit_jobs.py
-----------------------------------------------------------------------------------------
Goal of the script:
Create jobscript to fit pRF
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name (e.g. sub-01)
sys.argv[2]: task (pRF3T, pRF7T)
sys.argv[3]: registration (e.g. T1w, fsLR_den-170k)
sys.argv[4]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[5]: cifti data mode (subc: subcortical, surf: surface)
-----------------------------------------------------------------------------------------
Output(s):
.sh file to execute in server
-----------------------------------------------------------------------------------------
To run:
>> cd to function
>> python fit/submit_fit_jobs.py [subject] [task] [registration] [preproc] [cifti-mode]
-----------------------------------------------------------------------------------------
Exemple:
cd /home/mszinte/projects/pRF3T7T/mri_analysis/
python prf/fit/submit_fit_jobs.py sub-01 pRF3T T1w fmriprep_dct
python prf/fit/submit_fit_jobs.py sub-01 pRF3T T1w fmriprep_dct_pca
python prf/fit/submit_fit_jobs.py sub-01 pRF7T T1w fmriprep_dct
python prf/fit/submit_fit_jobs.py sub-01 pRF7T T1w fmriprep_dct_pca
python prf/fit/submit_fit_jobs.py sub-05 pRF7T T1w fmriprep_dct
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
import numpy as np
import os
import json
import sys
import nibabel as nb
import datetime
import ipdb
deb = ipdb.set_trace

# Settings
# --------
# Inputs
subject = sys.argv[1]
task = sys.argv[2]
regist_type = sys.argv[3]
preproc = sys.argv[4]
if regist_type == 'fsLR_den-170k':
    cifti_mode= sys.argv[5]
    if cifti_mode == 'surf': file_ext,sh_end = '.npy','_surface'
    elif cifti_mode == 'subc': file_ext,sh_end = '_subc.npy','_subcortical'
else:
    file_ext = '.nii.gz'
    sh_end = ''

# Analysis parameters
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# Cluster settings
base_dir = analysis_info['base_dir']
sub_command = 'sbatch '
fit_per_hour = 15000.0
nb_procs = 8
proj_name = 'b161'

print("{} analysis: running on Skylake".format(task))

# Create job and log output folders    
# define tc input / pRF fit / pRF tc prediction
data_type = 'avg'
log_dir = '{base_dir}/derivatives/pp_data/{sub}/prf/log_outputs'.format(base_dir=base_dir, sub=subject)
input_fn = "{base_dir}/derivatives/pp_data/{sub}/func/{sub}_task-{task}_space-{reg}_{preproc}_{data_type}{file_ext}".format(
                base_dir=base_dir, sub=subject, reg=regist_type, preproc=preproc, data_type=data_type, file_ext=file_ext, task=task)
fit_fn = "{base_dir}/derivatives/pp_data/{sub}/prf/fit/{sub}_task-{task}_space-{reg}_{preproc}_{data_type}_prf-fit{file_ext}".format(
                base_dir=base_dir, sub=subject, reg=regist_type, preproc=preproc, data_type=data_type, file_ext=file_ext, task=task)
pred_fn = "{base_dir}/derivatives/pp_data/{sub}/prf/fit/{sub}_task-{task}_space-{reg}_{preproc}_{data_type}_prf-pred{file_ext}".format(
                base_dir=base_dir, sub=subject, reg=regist_type, preproc=preproc, data_type=data_type, file_ext=file_ext, task=task)

if os.path.isfile(fit_fn):
    if os.path.getsize(fit_fn) != 0:
        print("output file {} already exists and is non-empty: aborting analysis".format(fit_fn))
        exit()
        
if regist_type == 'fsLR_den-170k': data = np.load(input_fn)        
else: data = nb.load(input_fn).get_fdata()

data_var = np.var(data,axis=-1)
mask = data_var!=0.0    
num_vox = mask[...].sum()
job_dur_obj = datetime.timedelta(hours=np.ceil(num_vox/fit_per_hour))
job_dur = "{:1d}-{:02d}:00:00".format(job_dur_obj.days,divmod(job_dur_obj.seconds,3600)[0])


# create job shell
slurm_cmd = """\
#!/bin/bash
#SBATCH -p skylake
#SBATCH -A {proj_name}
#SBATCH --nodes=1
#SBATCH --cpus-per-task={nb_procs}
#SBATCH --time={job_dur}
#SBATCH -e {log_dir}/{sub}_task-{task}_space-{reg}_{preproc}_{data_type}_fit_%N_%j_%a.err
#SBATCH -o {log_dir}/{sub}_task-{task}_space-{reg}_{preproc}_{data_type}_fit_%N_%j_%a.out
#SBATCH -J {sub}_task-{task}_space-{reg}_{preproc}_{data_type}_fit\n\n""".format(
proj_name=proj_name, nb_procs=nb_procs, 
log_dir=log_dir, job_dur=job_dur, sub=subject, task=task,
reg=regist_type, preproc=preproc, data_type=data_type)

# define fit cmd
fit_cmd = "python prf/fit/prf_fit.py {sub} {task} {reg} {preproc} {input_fn} {fit_fn} {pred_fn} {nb_procs}".format(
            sub=subject, reg=regist_type, preproc=preproc, input_fn=input_fn, task=task,
            fit_fn=fit_fn, pred_fn=pred_fn, nb_procs=nb_procs)

# create sh folder and file
sh_dir = "{base_dir}/derivatives/pp_data/{sub}/prf/jobs/{sub}_task-{task}_space-{reg}_{preproc}_{data_type}{sh_end}.sh".format(
            base_dir=base_dir, sub=subject, reg=regist_type, preproc=preproc, data_type=data_type, sh_end=sh_end, task=task)

try:
    os.makedirs('{}/derivatives/pp_data/{}/prf/fit/'.format(base_dir,subject))
    os.makedirs('{}/derivatives/pp_data/{}/prf/jobs/'.format(base_dir,subject))
    os.makedirs('{}/derivatives/pp_data/{}/prf/log_outputs/'.format(base_dir,subject))
except:
    pass

of = open(sh_dir, 'w')
of.write("{slurm_cmd}{fit_cmd}".format(slurm_cmd=slurm_cmd, fit_cmd=fit_cmd))
of.close()

# Submit jobs
print("Submitting {sh_dir} to queue".format(sh_dir=sh_dir))
os.system("{sub_command} {sh_dir}".format(sub_command=sub_command, sh_dir=sh_dir))
