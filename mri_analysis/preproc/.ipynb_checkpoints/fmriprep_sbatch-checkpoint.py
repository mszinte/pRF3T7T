"""
-----------------------------------------------------------------------------------------
fmriprep_sbatch.py
-----------------------------------------------------------------------------------------
Goal of the script:
Run fMRIprep on mesocentre using job mode
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: main project directory
sys.argv[2]: project name (correspond to directory)
sys.argv[3]: subject (e.g. sub-001)
sys.argv[4]: server nb of hour to request (e.g 10)
sys.argv[5]: anat only (1) or not (0)
sys.argv[6]: use of aroma (1) or not (0)
sys.argv[7]: use Use fieldmap-free distortion correction
sys.argv[8]: skip BIDS validation (1) or not (0)
sys.argv[9]: save cifti hcp format data with 170k vertices
sys.argv[10]: email account
-----------------------------------------------------------------------------------------
Output(s):
preprocessed files
-----------------------------------------------------------------------------------------
To run:
1. cd to function
>> cd /home/mszinte/projects/pRF3T7T/mri_analysis/
2. run python command
python preproc/fmriprep_sbatch.py [main directory] [project name] [subject num]
                                  [hour proc.] [anat only] [aroma] [fmapfree] 
                                  [skip bids validation] [cifti] [email account]
-----------------------------------------------------------------------------------------
Exemple:
python preproc/fmriprep_sbatch.py /scratch/mszinte/data pRF3T7T sub-01 20 1 0 0 0 1 martin.szinte
python preproc/fmriprep_sbatch.py /scratch/mszinte/data pRF3T7T sub-01 20 0 0 0 0 1 martin.szinte
-----------------------------------------------------------------------------------------
Written by Martin Szinte (martin.szinte@gmail.com)
-----------------------------------------------------------------------------------------
"""

# imports modules
import sys
import os
import time
# import ipdb
import json
opj = os.path.join
# deb = ipdb.set_trace

# inputs
main_dir = sys.argv[1]
project_dir = sys.argv[2]
subject = sys.argv[3]
sub_num = subject[-2:]
hour_proc = int(sys.argv[4])
anat = int(sys.argv[5])
aroma = int(sys.argv[6])
fmapfree = int(sys.argv[7])
skip_bids_val = int(sys.argv[8])
hcp_cifti_val = int(sys.argv[9])
email_account = sys.argv[10]

# Define cluster/server specific parameters
cluster_name  = 'skylake'
proj_name = 'b161'
singularity_dir = '/scratch/mszinte/softwares/fmriprep-20.2.3.simg'
nb_procs = 32
memory_val = 64
log_dir = opj(main_dir,project_dir,'deriv_data','fmriprep','log_outputs')

# special input
anat_only, use_aroma, use_fmapfree, anat_only_end, use_skip_bids_val, hcp_cifti, tf_export, tf_bind = '','','','','', '', '', ''
if anat == 1:
    anat_only = ' --anat-only'
    anat_only_end = '_anat'
    nb_procs = 8
if aroma == 1:
    use_aroma = ' --use-aroma'
if fmapfree == 1:
    use_fmapfree= ' --use-syn-sdc'
if skip_bids_val == 1:
    use_skip_bids_val = ' --skip_bids_validation'
if hcp_cifti_val == 1:
    tf_export = 'export SINGULARITYENV_TEMPLATEFLOW_HOME=/opt/templateflow'
    tf_bind = ' -B /scratch/mszinte/softwares/fmriprep_tf/:/opt/templateflow'
    hcp_cifti = ' --cifti-output 170k'

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
#SBATCH -e {log_dir}/{subject}_fmriprep{anat_only_end}_%N_%j_%a.err
#SBATCH -o {log_dir}/{subject}_fmriprep{anat_only_end}_%N_%j_%a.out
#SBATCH -J {subject}_fmriprep{anat_only_end}
#SBATCH --mail-type=BEGIN,END\n\n{tf_export}
""".format(proj_name=proj_name, nb_procs=nb_procs, hour_proc=hour_proc, subject=subject, anat_only_end=anat_only_end,
           memory_val=memory_val, log_dir=log_dir, email_account=email_account, tf_export=tf_export)

# define singularity cmd
singularity_cmd = "singularity run --cleanenv{tf_bind} -B {main_dir}:/work_dir {simg} --fs-license-file /work_dir/freesurfer/license.txt /work_dir/{project_dir}/bids_data/ /work_dir/{project_dir}/deriv_data/fmriprep/ participant --participant-label {sub_num} -w /work_dir/{project_dir}/temp_data/ --bold2t1w-dof 12 --ignore sbref --output-spaces T1w fsnative fsaverage MNI152NLin2009cAsym:res-1{hcp_cifti} --low-mem --mem-mb 64000 --nthreads {nb_procs:.0f}{anat_only}{use_aroma}{use_fmapfree}{use_skip_bids_val}".format(
                                tf_bind = tf_bind,
                                main_dir = main_dir,
                                project_dir = project_dir,
                                simg = singularity_dir,
                                sub_num = sub_num,
                                nb_procs = nb_procs,
                                anat_only = anat_only,
                                use_aroma = use_aroma,
                                use_fmapfree = use_fmapfree,
                                use_skip_bids_val = use_skip_bids_val,
                                hcp_cifti = hcp_cifti)

# create sh folder and file
sh_dir = "{main_dir}/{project_dir}/deriv_data/fmriprep/jobs/sub-{sub_num}_fmriprep{anat_only_end}.sh".format(main_dir = main_dir, sub_num = sub_num,project_dir = project_dir,anat_only_end = anat_only_end)

try:
    os.makedirs(opj(main_dir,project_dir,'deriv_data','fmriprep','jobs'))
    os.makedirs(opj(main_dir,project_dir,'deriv_data','fmriprep','log_outputs'))
except:
    pass
of = open(sh_dir, 'w')
of.write("{slurm_cmd}{singularity_cmd}".format(slurm_cmd = slurm_cmd,singularity_cmd = singularity_cmd))
of.close()

# Submit jobs
print("Submitting {sh_dir} to queue".format(sh_dir = sh_dir))
os.chdir(log_dir)
os.system("sbatch {sh_dir}".format(sh_dir = sh_dir))
