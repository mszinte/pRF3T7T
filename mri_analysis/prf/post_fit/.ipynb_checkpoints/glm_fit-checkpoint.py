"""
-----------------------------------------------------------------------------------------
pycortex_glm.py
-----------------------------------------------------------------------------------------
Goal of the script:
Compute GLM for Localisers
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: mount_dir (e.g. )
sys.argv[2]: subject name (e.g. sub-01)
sys.argv[3]: session (e.g. ses-01)
sys.argv[4]: task (e.g. PurLoc, PurVELoc)
sys.argv[5]: registration (e.g. T1w)
sys.argv[6]: run number (e.g. run-1)
sys.argv[7]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
-----------------------------------------------------------------------------------------
Output(s):
GLM output on a flatmap
-----------------------------------------------------------------------------------------
To run:
>> cd to function
>> python post_fit/pycortex_glm.py [mount_dir] [subject] [session] [task] [reg] [run] [preproc] [save-svg] [save-webapp]
-----------------------------------------------------------------------------------------
Example:
cd /home/mszinte/projects/PredictEye/mri_analysis/
python post_fit/pycortex_glm.py /scratch/mszinte/data/PredictEye/ sub-01 ses-01 SacLoc T1w run-1 fmriprep_dct 0 1
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
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import ipdb
deb = ipdb.set_trace

# MRI imports
# -----------
import nibabel as nb
import cortex

# Functions import
# ----------------
from utils import draw_cortex_vertex, set_pycortex_config_file, eventsMatrix

# GLM imports
# ----------------
from nilearn import image, datasets, plotting, surface
from nilearn.glm.first_level import FirstLevelModel
from nilearn.glm import threshold_stats_img
from nilearn.plotting import plot_design_matrix, plot_stat_map, plot_anat, plot_img


# Get inputs
# ----------
mount_dir =  sys.argv[1]
subject = sys.argv[2]
session = sys.argv[3]
task = sys.argv[4] 
space = sys.argv[5] 
run = sys.argv[6] 
preproc = sys.argv[7] 

# Define analysis parameters
# --------------------------
with open('settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)
    
# Define folder
# -------------
base_dir = "{}".format(mount_dir)
deriv_dir = "{}/pp_data/{}/glm/fit".format(base_dir,subject)

task_name = [task[:3], 'Fix' ]
file_img = "{cwd}/pp_data/{subject}/func/{subject}_task-{task}_space-{space}_{preproc}_avg.nii.gz".\
                format(cwd=mount_dir, subject=subject,task=task,space=space,preproc=preproc)
file_mask_img = '{cwd}/deriv_data/fmriprep/fmriprep/{subject}/{session}/func/{subject}_{session}_task-{task}_run-1_space-{space}_desc-brain_mask.nii.gz'.\
                format(cwd=mount_dir, subject=subject, session=session, task=task, space=space)
output_folder = '{cwd}/pp_data/{subject}/glm/fit/'.format(cwd=mount_dir, subject=subject)

try: os.makedirs(output_folder)
except: pass

# create design table
design_file_run1 = '{cwd}/bids_data/{subject}/{session}/func/{subject}_{session}_task-{task}_{run}_events.tsv'.\
                    format(cwd=mount_dir, subject=subject, session=session, task=task, run='run-01')
events_glm = eventsMatrix(design_file_run1, task)

# first level GLM
mask_img = nb.load(file_mask_img)

fmri_glm = FirstLevelModel( t_r=analysis_info['TR'],
                            noise_model=analysis_info['glm_noise_model'],
                            standardize=False,
                            hrf_model='spm',
                            drift_model=None,
                            mask_img=mask_img)

fmri_glm = fmri_glm.fit(file_img, events_glm)
design_matrix = fmri_glm.design_matrices_[0]

# contrast
if 'VE' not in task:
    exec('conditions = { task_name[1]: np.array([1., 0., 0.]), task_name[0]: np.array([0., 1., 0.])}')
    contrasts = {  'Task-Fix':conditions[task_name[0]] - conditions[task_name[1]]}
else:
    conditions = { 'Fix': np.array([1., 0., 0., 0.]), 
                    'Vis': np.array([0., 1., 0., 0.]), 
                    'End': np.array([0., 0., 1., 0.])}
    contrasts = {   'Vis-End': conditions['Vis'] - conditions['End'],
                    'Vis-Fix': conditions['Vis'] - conditions['Fix'],
                    'End-Fix': conditions['End'] - conditions['Fix']}

# compute glm maps
for contrast in contrasts:
    print('computing contrast glm maps')
    output_fn = '{output_folder}{subject}_task-{task}_space-{space}_{preproc}_deriv_contrast-{contrast}.nii.gz'.\
            format(output_folder=output_folder, subject=subject,task=task,space=space,preproc=preproc,contrast=contrast)
    
    eff_map = fmri_glm.compute_contrast(contrasts[contrast],
                                        output_type='effect_size')

    z_map = fmri_glm.compute_contrast(contrasts[contrast],
                                        output_type='z_score')

    p_map = 1 - stats.norm.cdf(abs(z_map.dataobj))

    # stats maps
    glm_alpha = analysis_info['glm_alpha']
    fdr_map, th = threshold_stats_img(z_map, alpha=glm_alpha, height_control='fdr')
    fdr_cluster10_map, th = threshold_stats_img(z_map, alpha=glm_alpha, height_control='fdr', cluster_threshold=10)
    fdr_cluster50_map, th = threshold_stats_img(z_map, alpha=glm_alpha, height_control='fdr', cluster_threshold=50)
    fdr_cluster100_map, th = threshold_stats_img(z_map, alpha=glm_alpha, height_control='fdr', cluster_threshold=100)

    # Save results
    img = nb.load(file_img)
    deriv = np.zeros((img.shape[0],img.shape[1],img.shape[2],6))*np.nan
    deriv[...,0]  = z_map.dataobj
    deriv[...,1]  = p_map
    deriv[...,2]  = fdr_map.dataobj
    deriv[...,3]  = fdr_cluster10_map.dataobj
    deriv[...,4]  = fdr_cluster50_map.dataobj
    deriv[...,5]  = fdr_cluster100_map.dataobj

    deriv = deriv.astype(np.float32)
    new_img = nb.Nifti1Image(dataobj = deriv, affine = img.affine, header = img.header)
    new_img.to_filename(output_fn)
    
# Set pycortex db and colormaps
# -----------------------------
set_pycortex_config_file(base_dir)

# Pycortex plots
# --------------
xfm_name = analysis_info["xfm_name"]
cmap = 'RdBu_r_alpha'
cmap_steps = 255
maps_names = {'z_map':0, 'p_map':1, 'fdr_map':2, 'fdr_c10_map':3, 'fdr_c50_map':4, 'fdr_c100_map':5}

for contrast in contrasts:
    print('Contrast: {}'.format(contrast))
    print('save pycortex flatmaps')
    flatmaps_dir = '{}/pp_data/{}/glm/pycortex_outputs/flatmaps'.format(base_dir, subject)
    webviewer_dir = '{base_dir}/pp_data/{subject}/glm/pycortex_outputs/webviewer/{subject}_{task}_{reg}_{preproc}_{contrast}'.format(
        base_dir=base_dir, subject=subject, task=task, reg=space, preproc=preproc, contrast=contrast)

    try:
        os.makedirs(flatmaps_dir)
        os.makedirs(webviewer_dir)
    except:
        pass

    # Load data
    deriv_mat_file = "{deriv_dir}/{subject}_task-{task}_space-{reg}_{preproc}_deriv_contrast-{contrast}.nii.gz".format(
                      deriv_dir=deriv_dir, subject=subject, task=task, reg=space, preproc=preproc, contrast=contrast)

    img_deriv_mat = nb.load(deriv_mat_file)
    deriv_mat = img_deriv_mat.get_fdata()

    # Draw flatmaps
    volumes = {}
    param = dict()
    for map_name in maps_names:
        alpha = 1-deriv_mat[...,maps_names['p_map']]
        data  = deriv_mat[...,maps_names[map_name]]
        
        param[map_name] = {'data': data, 'xfmname': xfm_name, 'cmap': cmap, 'alpha': alpha, 'volume_type': 'Volume2D', 'vmin': [-3.5, 1-0.01],'vmax': [3.5, 1-0.0001],'cbar': 'discrete',
                     'description': '{} {}'.format(task, contrast), 'curv_brightness': 1, 'curv_contrast': 0.1, 'add_roi': False}

        roi_name = '{}_{}_{}_{}_{}'.format(map_name, task, space, preproc, contrast)
        roi_param = {'subject': subject, 'xfmname': xfm_name, 'roi_name': roi_name}
        print(roi_name)
        exec('param[\'{}\'].update(roi_param)'.format(map_name))
        exec('volume_{maps_name} = draw_cortex_vertex(**param[\'{maps_name}\'])'.format(maps_name=map_name))
        exec("plt.savefig('{}/{}_task-{}_space-{}_{}_{}.pdf')".format(flatmaps_dir, map_name, task, space, preproc, contrast))
        plt.close()
        exec('vol_description = param[\'{}\']["description"]'.format(map_name))
        exec('volume = volume_{}'.format(map_name))
        volumes.update({vol_description:volume})

    print('save pycortex webviewer')
    cortex.webgl.make_static(outpath=webviewer_dir, data=volumes, recache=True)

# Send to webapp
# --------------
if webapp == 1:
    
    webapp_dir = analysis_info['webapp_dir']
    os.system('rsync -avuz --progress {local_dir} {webapp_dir}'.format(local_dir=webviewer_dir, webapp_dir=webapp_dir))

