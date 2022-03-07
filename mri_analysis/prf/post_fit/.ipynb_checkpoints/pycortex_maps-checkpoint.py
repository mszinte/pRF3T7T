"""
-----------------------------------------------------------------------------------------
pycortex_maps.py
-----------------------------------------------------------------------------------------
Goal of the script:
Create flatmap plots and dataset
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name (e.g. sub-01)
sys.argv[2]: registration (e.g. T1w)
sys.argv[3]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[4]: save in SVG file (0  = No, 1 = Yes)
-----------------------------------------------------------------------------------------
Output(s):
Pycortex flatmaps figures
-----------------------------------------------------------------------------------------
To run:
On invibe server
>> cd to function
>> python prf/post_fit/pycortex_maps.py [subject] [reg] [preproc] [svg]
-----------------------------------------------------------------------------------------
Exemple:
[TO RUN LOCALLY OR ON INVIBE SERVER]
cd ~/disks/meso_H/projects/PredictEye/mri_analysis/
ipython prf/post_fit/pycortex_maps.py sub-01 T1w fmriprep_dct 0
ipython prf/post_fit/pycortex_maps.py sub-01 fsLR_den-170k fmriprep_dct 0
ipython prf/post_fit/pycortex_maps.py sub-01 T1w fmriprep_dct_pca 0
ipython prf/post_fit/pycortex_maps.py sub-01 fsLR_den-170k fmriprep_dct_pca 0
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
deb = ipdb.set_trace

# MRI imports
# -----------
import nibabel as nb
import cortex

# Functions import
# ----------------
from utils.utils import draw_cortex_vertex, set_pycortex_config_file

# Get inputs
# ----------
subject = sys.argv[1]
regist_type = sys.argv[2]
if regist_type == 'fsLR_den-170k':
    file_ext = '.npy'
    cifti_mode= 'surf'
    cortex_type = 'VertexRGB'
    subject2draw = 'hcp'
else:
    file_ext = '.nii.gz'
    sh_end = ''
    cortex_type = 'VolumeRGB'
    subject2draw = subject

preproc = sys.argv[3]
save_svg = int(sys.argv[4])
if save_svg == 1: save_svg = True
else: save_svg = False

# Define analysis parameters
# --------------------------
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# Define folder
# -------------
xfm_name = analysis_info["xfm_name"]
base_dir = analysis_info["base_dir_local"]
cvrsq_val = analysis_info["cvr2_range"]
deriv_dir = "{}/pp_data_new/{}/prf/fit".format(base_dir,subject)

# Set pycortex db and colormaps
# -----------------------------
set_pycortex_config_file(base_dir)

# Pycortex plots
# --------------
rsq_idx, ecc_idx, polar_real_idx, polar_imag_idx , size_idx, \
    amp_idx, baseline_idx, cov_idx, x_idx, y_idx, cv_rsq_idx = 0,1,2,3,4,5,6,7,8,9,10

cmap_polar, cmap_uni, cmap_ecc_size = 'hsv', 'Reds', 'Spectral'
col_offset = 1.0/14.0
cmap_steps = 255

print('save flatmaps')
maps_names = []
flatmaps_dir = '{}/pp_data_new/{}/prf/pycortex/flatmaps'.format(base_dir, subject)
datasets_dir = '{}/pp_data_new/{}/prf/pycortex/datasets'.format(base_dir, subject)

try: os.makedirs(flatmaps_dir); 
except: pass
try: os.makedirs(datasets_dir)
except: pass


data_types = ['avg','avg-loo']
for data_type in data_types:

    # Load data
    deriv_fn = "{}/{}_task-pRF_space-{}_{}_{}_prf-deriv{}".format(deriv_dir, subject, regist_type, preproc, data_type,file_ext)
    
    if regist_type == 'fsLR_den-170k': deriv_mat = np.load(deriv_fn)
    else: deriv_mat = nb.load(deriv_fn).get_fdata()

    # R-square
    rsq_data = deriv_mat[...,rsq_idx]
    alpha = rsq_data
    param_rsq = {'data': rsq_data, 'cmap': cmap_uni, 'alpha': rsq_data, 'vmin': 0,'vmax': 1,'cbar': 'discrete', 'cortex_type': cortex_type,
                 'description': 'pRF rsquare', 'curv_brightness': 1, 'curv_contrast': 0.1, 'add_roi': False}
    maps_names.append('rsq')
    
    # CV-R-square
    cv_rsq_data = deriv_mat[...,cv_rsq_idx]
    cv_rsq_data[cv_rsq_data==1]=0
    cv_rsq_alpha = (cv_rsq_data - np.nanmin(cv_rsq_data))/ (np.nanmax(cv_rsq_data) - np.nanmin(cv_rsq_data))
    param_cv_rsq = {'data': cv_rsq_data, 'cmap': cmap_uni, 'alpha': cv_rsq_alpha, 'vmin': cvrsq_val[0],'vmax': cvrsq_val[1],'cbar': 'discrete', 'cortex_type': cortex_type,
                 'description': 'pRF cv-rsquare', 'curv_brightness': 1, 'curv_contrast': 0.1, 'add_roi': False}
    maps_names.append('cv_rsq')

    # Polar angle
    pol_comp_num = deriv_mat[...,polar_real_idx] + 1j * deriv_mat[...,polar_imag_idx]
    polar_ang = np.angle(pol_comp_num)
    ang_norm = (polar_ang + np.pi) / (np.pi * 2.0)
    ang_norm = np.fmod(ang_norm + col_offset,1)
    param_polar = { 'data': ang_norm, 'cmap': cmap_polar, 'alpha': alpha, 'vmin': 0, 'vmax': 1, 'cmap_steps': cmap_steps, 'cortex_type': cortex_type,
                    'cbar': 'polar', 'col_offset': col_offset, 'description': 'pRF polar:{cmap_steps:3.0f} steps'.format(cmap_steps=cmap_steps), 
                    'curv_brightness': 0.1, 'curv_contrast': 0.25, 'add_roi': save_svg}
    exec('param_polar_{cmap_steps} = param_polar'.format(cmap_steps = int(cmap_steps)))
    exec('maps_names.append("polar_{cmap_steps}")'.format(cmap_steps = int(cmap_steps)))

    # Eccentricity
    ecc_data = deriv_mat[...,ecc_idx]
    param_ecc = {'data': ecc_data, 'cmap': cmap_ecc_size, 'alpha': alpha, 'vmin': 0, 'vmax': 15,'cbar': 'ecc', 'cortex_type': cortex_type,
                 'description': 'pRF eccentricity', 'curv_brightness': 1, 'curv_contrast': 0.1, 'add_roi': save_svg}
    maps_names.append('ecc')

    # Size
    size_data = deriv_mat[...,size_idx]
    param_size = {'data': size_data, 'cmap': cmap_ecc_size, 'alpha': alpha, 'vmin': 0, 'vmax': 8, 'cbar': 'discrete', 'cortex_type':cortex_type,
                  'description': 'pRF size', 'curv_brightness': 1, 'curv_contrast': 0.1, 'add_roi': False}
    maps_names.append('size')

    # Coverage
    cov_data = deriv_mat[...,cov_idx]
    param_cov = {'data': cov_data, 'cmap': cmap_uni, 'alpha': alpha,'vmin': 0, 'vmax': 1, 'cbar': 'discrete', 'cortex_type':cortex_type,
                'description': 'pRF coverage', 'curv_brightness': 1, 'curv_contrast': 0.1, 'add_roi': False}
    maps_names.append('cov')

    # Draw flatmaps
    volumes = {}
    for maps_name in maps_names:

        # create flatmap
        roi_name = 'pRF_{}_{}_{}_{}'.format(regist_type, preproc, data_type, maps_name)
        roi_param = {'subject': subject2draw, 'xfmname': xfm_name, 'roi_name': roi_name}
        print(roi_name)
        exec('param_{}.update(roi_param)'.format(maps_name))
        exec('volume_{maps_name} = draw_cortex_vertex(**param_{maps_name})'.format(maps_name=maps_name))
        exec("plt.savefig('{}/{}_task-pRF_space-{}_{}_{}_{}.pdf')".format(flatmaps_dir, subject, regist_type, preproc, data_type, maps_name))
        plt.close()

        # save flatmap as dataset
        exec('vol_description = param_{}["description"]'.format(maps_name))
        exec('volume = volume_{}'.format(maps_name))
        volumes.update({vol_description:volume})
        
    # save dataset
    dataset_file = "{}/{}_task-pRF_space-{}_{}_{}.hdf".format(datasets_dir, subject, regist_type, preproc, data_type)
    dataset = cortex.Dataset(data = volumes)
    dataset.save(dataset_file)