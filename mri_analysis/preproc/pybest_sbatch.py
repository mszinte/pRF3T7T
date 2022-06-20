"""
-----------------------------------------------------------------------------------------
pybest_sbatch.py
-----------------------------------------------------------------------------------------
Goal of the script:
Run pybest on mesocentre using job mode
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: main project directory
sys.argv[2]: project name (correspond to directory)
sys.argv[3]: subject (e.g. sub-01)
sys.argv[4]: registration type (e.g. T1w)
sys.argv[5]: server nb of hour to request (e.g 10)
sys.argv[6]: pca noise processing (0 =no, 1 = yes)
sys.argv[6]: email account
-----------------------------------------------------------------------------------------
Output(s):
preprocessed files
-----------------------------------------------------------------------------------------
To run:
1. cd to function
>> cd /home/mszinte/projects/pRF3T7T/mri_analysis/
2. run python command
python preproc/pybest_sbatch.py [main directory] [project name] [subject num] 
                                [registration type] [hour proc.] [pca] [email account]
-----------------------------------------------------------------------------------------
Exemple:
python preproc/pybest_sbatch.py /scratch/mszinte/data pRF3T7T sub-01 T1w 2 0 martin.szinte
python preproc/pybest_sbatch.py /scratch/mszinte/data pRF3T7T sub-04 T1w 2 0 martin.szinte
python preproc/pybest_sbatch.py /scratch/mszinte/data pRF3T7T sub-05 T1w 2 0 martin.szinte
-----------------------------------------------------------------------------------------
Written by Martin Szinte (martin.szinte@gmail.com)
-----------------------------------------------------------------------------------------
"""

# imports modules
import sys
import os
import time
#import ipdb
import json
opj = os.path.join
#deb = ipdb.set_trace

# inputs
main_dir = sys.argv[1]
project_dir = sys.argv[2]
subject = sys.argv[3]
sub_num = subject[-2:]
regist_type =sys.argv[4]
hour_proc = int(sys.argv[5])
noise_proc = int(sys.argv[6])
if noise_proc == 0: noise_proc_txt = ' --skip-noiseproc';nb_procs = 8
elif noise_proc == 1: noise_proc_txt = '';nb_procs = 32
email_account = sys.argv[7]

# Define cluster/server specific parameters
cluster_name  = 'skylake'
proj_name = 'b161'
memory_val = 48
log_dir = opj(main_dir,project_dir,'derivatives','pybest','log_outputs')
if regist_type == 'fsLR_den-170k':
    cifti_file = opj(main_dir,project_dir,'derivatives','pybest','indices','cifti_indices.hdf5')
    cifti_cmd = "'{cifti_file}' 'Left_indices' 'Right_indices' 'Subcortex_indices' --iscifti 'y' --mode 'all'".format(cifti_file=cifti_file)
else:
    cifti_cmd = ''

# define SLURM cmd
slurm_cmd = """\
#!/bin/bash
#SBATCH --mail-type=ALL
#SBATCH -p skylake
#SBATCH --mail-user={email_account}@univ-amu.fr
#SBATCH -A {proj_name}
#SBATCH --nodes=1
#SBATCH --mem={memory_val}gb
#SBATCH --cpus-per-task={nb_procs}
#SBATCH --time={hour_proc}:00:00
#SBATCH -e {log_dir}/{subject}_pybest_%N_%j_%a.err
#SBATCH -o {log_dir}/{subject}_pybest_%N_%j_%a.out
#SBATCH -J {subject}_pybest
#SBATCH --mail-type=BEGIN,END\n\n""".format(proj_name=proj_name, nb_procs=nb_procs, hour_proc=hour_proc, 
                                            subject=subject, memory_val=memory_val, log_dir=log_dir, email_account=email_account)



# define pybest cmd
fmriprep_dir = "{main_dir}/{project_dir}/derivatives/fmriprep/fmriprep/".format(main_dir=main_dir,project_dir=project_dir)
bids_dir = "{main_dir}/{project_dir}/".format(main_dir=main_dir, project_dir=project_dir)
pybest_dir = "{main_dir}/{project_dir}/derivatives/pybest/".format(main_dir=main_dir,project_dir=project_dir)

pybest_cmd = "pybest {fmriprep_dir} {bids_dir} {cifti_cmd} --out-dir {pybest_dir} --subject '{sub_num}' --space '{regist_type}' --high-pass-type 'dct' --noise-source fmriprep --skip-signalproc --verbose 'DEBUG' --save-all{noise_proc}".format(
                        fmriprep_dir=fmriprep_dir,bids_dir=bids_dir, cifti_cmd=cifti_cmd, pybest_dir=pybest_dir, sub_num=sub_num, regist_type=regist_type, noise_proc=noise_proc_txt)

# create sh folder and file
sh_dir = "{main_dir}/{project_dir}/derivatives/pybest/jobs/{subject}_pybest_{regist_type}.sh".format(main_dir=main_dir, subject=subject,project_dir=project_dir,regist_type=regist_type)


try:
    os.makedirs(opj(main_dir,project_dir,'derivatives','pybest','jobs'))
    os.makedirs(opj(main_dir,project_dir,'derivatives','pybest','log_outputs'))
except:
    pass

of = open(sh_dir, 'w')
of.write("{slurm_cmd}{pybest_cmd}".format(slurm_cmd=slurm_cmd,pybest_cmd=pybest_cmd))
of.close()

# Submit jobs
print("Submitting {sh_dir} to queue".format(sh_dir=sh_dir))
os.chdir(log_dir)
os.system("sbatch {sh_dir}".format(sh_dir=sh_dir))
