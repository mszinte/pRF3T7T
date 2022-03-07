"""
-----------------------------------------------------------------------------------------
pfit.py
-----------------------------------------------------------------------------------------
Goal of the script:
Create pRF or pMF estimates
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name
sys.argv[2]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[3]: slice number
sys.argv[4]: registration type
sys.argv[5]: output filename
sys.argv[6]: task (e.g. 'pRF' or 'pMF')
sys.argv[7]: sub-task (e.g. 'sp' or 'sac')
-----------------------------------------------------------------------------------------
Output(s):
Nifti image files with fit parameters for a z slice
-----------------------------------------------------------------------------------------
To run:
>> cd to function directory
>> python fit/pfit.py [subject] [preproc] [slice_nb] [registration] [output file] 
                                                        [task] [subtask]
-----------------------------------------------------------------------------------------
Exemple:
cd /home/mszinte/projects/PredictEye/mri_analysis/
python fit/pfit.py sub-01 fmriprep_dct 10 T1w /path_to/sub-01....nii.gz pRF
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
import sys, os
import numpy as np
import scipy.io
import glob
import datetime
import json
import ipdb
deb = ipdb.set_trace

# MRI analysis imports
# --------------------
from model.prfpy.rf import *
from model.prfpy.timecourse import *
from model.prfpy.stimulus import PRFStimulus2D
from model.prfpy.model import Iso2DGaussianModel
from model.prfpy.fit import Iso2DGaussianFitter
import nibabel as nb

# Get inputs
# ----------
start_time = datetime.datetime.now()
subject = sys.argv[1]
preproc = sys.argv[2]
slice_nb = int(sys.argv[3])
regist_type = sys.argv[4]
if regist_type == 'fsLR_den-170k':
else: 
opfn = sys.argv[5]
task = sys.argv[6]
if len(sys.argv) < 8: sub_task = ''
else: sub_task = sys.argv[7]

# Define analysis parameters
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# Define cluster/server specific parameters
base_dir = analysis_info['base_dir']
nb_procs = 32

# Get task specific settings
if task == 'pRF':
    # to create stimulus design (create in matlab - see others/make_visual_dm.m)
    visual_dm_file = scipy.io.loadmat('{}/pp_data/visual_dm/pRF_vd.mat'.format(base_dir))
    visual_dm = visual_dm_file['stim'].transpose([1,0,2])

elif task == 'pMF':
    pmf_seq_num_all = analysis_info['pmf_seq_num']    # put by hand after looking randomly selected order in event file
    pmf_seq_num = pmf_seq_num_all[int(subject[-2:])-1]
    # to create stimulus design (create using fit/pmf_design.py)
    visual_dm_file = scipy.io.loadmat("{}/pp_data/visual_dm/{}{}_vd_{}.mat".format(base_dir,task,sub_task, pmf_seq_num))
    visual_dm = visual_dm_file['stim']

# Load data
data_file = "{base_dir}/pp_data/{sub}/func/{sub}_task-{task}_space-{reg}_{preproc}_avg.nii.gz".format(
                        base_dir=base_dir, sub=subject, task=task, reg=regist_type, preproc=preproc)
data_img = nb.load(data_file)
data = data_img.get_fdata()
data_var = np.var(data, axis=3)
mask = data_var!=0.0

slice_mask = mask[:,:,slice_nb].astype(bool)
num_vox = np.sum(slice_mask)
data_slice = data[:,:,slice_nb,:]
data_to_analyse = data_slice[slice_mask]

# determine voxel indices
y, x = np.meshgrid(np.arange(data.shape[1]),np.arange(data.shape[0]))
x_vox,y_vox = x[slice_mask],y[slice_mask]
vox_indices = [(xx,yy,slice_nb) for xx,yy in zip(x_vox,y_vox)]

# determine model

stimulus = PRFStimulus2D(   screen_size_cm=analysis_info['screen_width'],
                            screen_distance_cm=analysis_info['screen_distance'],
                            design_matrix=visual_dm,
                            TR=analysis_info['TR'])


gauss_model = Iso2DGaussianModel(stimulus=stimulus)
grid_nr = analysis_info['grid_nr']
max_ecc_size = analysis_info['max_ecc_size']
sizes = max_ecc_size * np.linspace(0.1,1,grid_nr)**2
eccs = max_ecc_size * np.linspace(0.1,1,grid_nr)**2
polars = np.linspace(0, 2*np.pi, grid_nr)

print("Slice {slice_nb} containing {num_vox} brain mask voxels".format(slice_nb=slice_nb, num_vox=num_vox))

# grid fit
print("Grid fit")
gauss_fitter = Iso2DGaussianFitter(data=data_to_analyse, model=gauss_model, n_jobs=nb_procs)
gauss_fitter.grid_fit(ecc_grid=eccs, polar_grid=polars, size_grid=sizes, pos_prfs_only=True)

# iterative fit
print("Iterative fit")
gauss_fitter.iterative_fit(rsq_threshold=0.0001, verbose=False)
estimates_fit = gauss_fitter.iterative_search_params

# Re-arrange data
estimates_mat = np.zeros((data.shape[0],data.shape[1],data.shape[2],6))
for est,vox in enumerate(vox_indices):
    estimates_mat[vox] = estimates_fit[est]

# Save estimates data
new_img = nb.Nifti1Image(dataobj=estimates_mat, affine=data_img.affine, header=data_img.header)
new_img.to_filename(opfn)

# Print duration
end_time = datetime.datetime.now()
print("\nStart time:\t{start_time}\nEnd time:\t{end_time}\nDuration:\t{dur}".format(
            start_time=start_time,
            end_time=end_time,
            dur=end_time - start_time))