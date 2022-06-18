"""
-----------------------------------------------------------------------------------------
prf_fit.py
-----------------------------------------------------------------------------------------
Goal of the script:
pRF fit code
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name
sys.argv[2]: task
sys.argv[3]: registration type
sys.argv[4]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[5]: recorded time series filename and path
sys.argv[6]: prf fit filename and path
sys.argv[7]: predicted time series filename and path
sys.argv[8]: number of processors
-----------------------------------------------------------------------------------------
Output(s):
Nifti image files with fit parameters for a z slice
-----------------------------------------------------------------------------------------
To run :
>> cd to function directory
>> python fit/prf_fit.py [subject] [task] [registration] [preproc]
                         [intput file] [fit file] [predic file] [nb_procs]
-----------------------------------------------------------------------------------------
Exemple:
cd /home/mszinte/projects/PredictEye/mri_analysis/
python fit/prf_fit.py sub-01 pRF3T T1w fmriprep_dct /path_to... /path_to... /path_to... 8
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
from prf.model.prfpy.rf import *
from prf.model.prfpy.timecourse import *
from prf.model.prfpy.stimulus import PRFStimulus2D
from prf.model.prfpy.model import Iso2DGaussianModel
from prf.model.prfpy.fit import Iso2DGaussianFitter
import nibabel as nb

# Get inputs
# ----------
start_time = datetime.datetime.now()
subject = sys.argv[1]
task = sys.argv[2]
if task == 'pRF3T': task_num = 0
elif task == 'pRF7T': task_num = 1
regist_type = sys.argv[3]
preproc = sys.argv[4]
input_fn = sys.argv[5]
fit_fn = sys.argv[6]
pred_fn = sys.argv[7]
nb_procs = int(sys.argv[8])

# Define analysis parameters
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# Define cluster/server specific parameters
base_dir = analysis_info['base_dir']

# Get task specific settings
visual_dm_file = scipy.io.loadmat('{}/derivatives/pp_data/visual_dm/{}_vd.mat'.format(base_dir,task))
visual_dm = visual_dm_file['stim'].transpose([1,0,2])

# Load data
if regist_type == 'fsLR_den-170k': 
    data = np.load(input_fn)
else: 
    data_img = nb.load(input_fn)
    data = data_img.get_fdata()

data_var = np.var(data,axis=-1)
mask = data_var!=0.0    
num_vox = mask[...].sum()
data_to_analyse = data[mask]
data_where = np.where(data_var!=0.0)
data_indices = []
if data.ndim == 4:
    for x,y,z in zip(data_where[0],data_where[1],data_where[2]):
        data_indices.append((x,y,z))
    fit_mat = np.zeros((data.shape[0],data.shape[1],data.shape[2],6))
elif data.ndim == 2:
    for gray_ordinate in data_where[0]:
        data_indices.append((gray_ordinate))
    fit_mat = np.zeros((data.shape[0],6))
pred_mat = np.zeros(data.shape)

# determine model
stimulus = PRFStimulus2D(   screen_size_cm=analysis_info['screen_width'][task_num],
                            screen_distance_cm=analysis_info['screen_distance'][task_num],
                            design_matrix=visual_dm,
                            TR=analysis_info['TR'][task_num])

gauss_model = Iso2DGaussianModel(stimulus=stimulus)
grid_nr = analysis_info['grid_nr']
max_ecc_size = analysis_info['max_ecc_size'][task_num]
sizes = max_ecc_size * np.linspace(0.1,1,grid_nr)**2
eccs = max_ecc_size * np.linspace(0.1,1,grid_nr)**2
polars = np.linspace(0, 2*np.pi, grid_nr)

# grid fit
print("Grid fit")
gauss_fitter = Iso2DGaussianFitter(data=data_to_analyse, model=gauss_model, n_jobs=nb_procs)
gauss_fitter.grid_fit(ecc_grid=eccs, polar_grid=polars, size_grid=sizes, pos_prfs_only=True)

# iterative fit
print("Iterative fit")
gauss_fitter.iterative_fit(rsq_threshold=0.0001, verbose=False)
fit_fit = gauss_fitter.iterative_search_params

# Re-arrange data
for est,vox in enumerate(data_indices):
    fit_mat[vox] = fit_fit[est]
    pred_mat[vox] = gauss_model.return_prediction(  mu_x=fit_fit[est][0], mu_y=fit_fit[est][1], size=fit_fit[est][2], 
                                                    beta=fit_fit[est][3], baseline=fit_fit[est][4])

# Save fit and prediction data
if regist_type == 'fsLR_den-170k':
    np.save(fit_fn, fit_mat)
    np.save(pred_fn, pred_mat)
else: 
    fit_img = nb.Nifti1Image(dataobj=fit_mat, affine=data_img.affine, header=data_img.header)
    fit_img.to_filename(fit_fn)
    pred_img = nb.Nifti1Image(dataobj=pred_mat, affine=data_img.affine, header=data_img.header)
    pred_img.to_filename(pred_fn)

# Print duration
end_time = datetime.datetime.now()
print("\nStart time:\t{start_time}\nEnd time:\t{end_time}\nDuration:\t{dur}".format(
            start_time=start_time,
            end_time=end_time,
            dur=end_time - start_time))