"""
-----------------------------------------------------------------------------------------
roi_plots.py
-----------------------------------------------------------------------------------------
Goal of the script:
Draw roi plots (maps, ecc vs. params, laterality, time course)
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject name (e.g. 'sub-01')
sys.argv[2]: task (ex: 'pRF', 'pMF')
sys.argv[3]: pre-processing steps (fmriprep_dct or fmriprep_dct_pca)
sys.argv[4]: registration (e.g. T1w)
sys.argv[6]: sub_task (e.g. 'sac', 'sp')
-----------------------------------------------------------------------------------------
Output(s):
HTML figures per ROI
-----------------------------------------------------------------------------------------
To run:
>> cd to function
>> python post_fit/roi_plots.py [subject] [task] [preproc] [reg] [sub-task]
-----------------------------------------------------------------------------------------
Exemple:
cd /home/mszinte/projects/PredictEye/mri_analysis/
python post_fit/roi_plots.py sub-01 pRF fmriprep_dct T1w 
python post_fit/roi_plots.py sub-01 pMF fmriprep_dct T1w sac
python post_fit/roi_plots.py sub-01 pMF fmriprep_dct T1w sp
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
import glob
import numpy as np
import matplotlib.pyplot as pl
import ipdb
import platform
import h5py
import scipy.io
opj = os.path.join
deb = ipdb.set_trace

# MRI imports
# -----------
import nibabel as nb
import cortex

# Functions import
# ----------------
from plot_class import PlotOperator
from utils import set_pycortex_config_file

# Bokeh imports
# ---------------
from bokeh.io import output_notebook, show, save, output_file
from bokeh.layouts import row, column, gridplot

# Get inputs
# ----------
subject = sys.argv[1]
task = sys.argv[2]
preproc = sys.argv[3]
regist_type = sys.argv[4]
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
sample_ratio = analysis_info['sample_ratio']

rois_mask_dir = "{}/pp_data/{}/gauss/roi_masks/".format(base_dir, subject)

deriv_dir = "{}/pp_data/{}/gauss/fit/{}".format(base_dir, subject,task)
h5_dir = "{}/pp_data/{}/gauss/h5/{}{}".format(base_dir, subject, task, sub_task)
bokeh_dir = "{}/pp_data/{}/gauss/figures/{}{}".format(base_dir, subject, task, sub_task)
try: os.makedirs(bokeh_dir)
except: pass

# Draw main analysis figure
# -------------------------
print('creating bokeh plots')
rsq_idx, ecc_idx, polar_real_idx, polar_imag_idx , size_idx, \
    amp_idx, baseline_idx, cov_idx, x_idx, y_idx, hemi_idx = 0,1,2,3,4,5,6,7,8,9,10

# Initialize data
# ---------------
for roi_num, roi in enumerate(rois):
    
    # create html folder
    exec("html_dir = '{}/{}{}_{}_{}/'".format(bokeh_dir, task, sub_task, preproc, regist_type))
    try: os.makedirs(html_dir)
    except: pass

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

    # threshold data
    voxel_num_ini = deriv_data.shape[0]
    voxel_num = 0
    if voxel_num_ini > 0:
        # take out nan
        tc_data = tc_data[~np.isnan(deriv_data[:,rsq_idx]),:]
        tc_model_data = tc_model_data[~np.isnan(deriv_data[:,rsq_idx]),:]
        coord_data = coord_data[~np.isnan(deriv_data[:,rsq_idx]),:]
        deriv_data = deriv_data[~np.isnan(deriv_data[:,rsq_idx]),:]

        # threshold on eccentricity and size
        deriv_data_th = deriv_data
        rsqr_th_down = deriv_data_th[:,rsq_idx] >= analysis_info['rsqr_th'][0]
        rsqr_th_up = deriv_data_th[:,rsq_idx] <= analysis_info['rsqr_th'][1]
        size_th_down = deriv_data_th[:,size_idx] >= analysis_info['size_th'][0]
        size_th_up = deriv_data_th[:,size_idx] <= analysis_info['size_th'][1]
        ecc_th_down = deriv_data_th[:,ecc_idx] >= analysis_info['ecc_th'][0]
        ecc_th_up = deriv_data_th[:,ecc_idx] <= analysis_info['ecc_th'][1]
        all_th = np.array((rsqr_th_up,rsqr_th_down,size_th_down,size_th_up,ecc_th_down,ecc_th_up)) 

        deriv_data = deriv_data[np.logical_and.reduce(all_th),:]
        tc_data = tc_data[np.logical_and.reduce(all_th),:]
        tc_model_data = tc_model_data[np.logical_and.reduce(all_th),:]
        coord_data = coord_data[np.logical_and.reduce(all_th),:]
        voxel_num = deriv_data.shape[0]
        
    # Draw and save figures
    # ---------------------
    if voxel_num > 0:
        # randomize order and take 10 %
        new_order = np.random.permutation(voxel_num)
        deriv_data = deriv_data[new_order,:]
        tc_data = tc_data[new_order,:]
        tc_model_data = tc_model_data[new_order,:]
        coord_data = coord_data[new_order,:]
        deriv_data_sample = deriv_data[0:int(np.round(voxel_num*sample_ratio)),:]

        print("drawing {}_{}_{} figures, n = {}".format(roi, task, preproc, voxel_num)) 

        data_source = { 'rsq': deriv_data[:,rsq_idx],
                        'ecc': deriv_data[:,ecc_idx],
                        'sigma': deriv_data[:,size_idx],
                        'beta': deriv_data[:,amp_idx],
                        'baseline': deriv_data[:,baseline_idx],
                        'cov': deriv_data[:,cov_idx],
                        'x': deriv_data[:,x_idx],
                        'y': deriv_data[:,y_idx],
                        'colors_ref': deriv_data[:,ecc_idx]}
        
        data_source_sample = { 
                        'rsq': deriv_data_sample[:,rsq_idx],
                        'ecc': deriv_data_sample[:,ecc_idx],
                        'sigma': deriv_data_sample[:,size_idx],
                        'beta': deriv_data_sample[:,amp_idx],
                        'baseline': deriv_data_sample[:,baseline_idx],
                        'cov': deriv_data_sample[:,cov_idx],
                        'x': deriv_data_sample[:,x_idx],
                        'y': deriv_data_sample[:,y_idx],
                        'colors_ref': deriv_data_sample[:,ecc_idx]}

        param_all = {   'roi_t': roi, 
                        'p_width': 400, 
                        'p_height': 400, 
                        'min_border_large': 10, 
                        'min_border_small': 5,
                        'bg_color': tuple([229,229,229]), 
                        'stim_color': tuple([250,250,250]), 
                        'hist_fill_color': tuple([255,255,255]),
                        'hist_line_color': tuple([0,0,0]), 
                        'stim_height': analysis_info['stim_height'],
                        'stim_width': analysis_info['stim_width'],
                        'cmap': 'Spectral',
                        'cmap_steps': 15,
                        'col_offset': 0,
                        'vmin': 0,
                        'vmax': 15,
                        'leg_xy_max_ratio': 1.8,
                        'dataMat': deriv_data,
                        'data_source': data_source,
                        'data_source_sample': data_source_sample,
                        'hist_range': (0,0.5),
                        'hist_steps': 0.5,
                        'h_hist_bins': 16,
                        'link_x': False,
                        'link_y': False,
                        }

        plotter = PlotOperator(**param_all)

        # # FIG 1: ECC VS...
        # # --------------------

        old_main_fig = []
        f_ecc = []
        if sub_task == '':
            type_comp_list = ['Size','R2','Coverage','Baseline']
        else:
            type_comp_list = ['Size','R2','Baseline']
        
        for numData, type_comp in enumerate(type_comp_list):

            params_ecc = param_all
            params_ecc.update(
                       {    'x_range': (0, 15),
                            'x_label': 'Eccentricity (dva)',
                            'x_tick_steps': 5,
                            'x_source_label': 'ecc',
                            'draw_reg': False,
                            'h_hist_bins': 15,
                            'link_x': True})

            title = '{}: Eccentricity vs. {}'.format(roi, type_comp)
            params_ecc.update({'main_fig_title': title})


            if type_comp == 'Size':
                params_ecc.update(
                            {   'y_range': (0, 15),
                                'y_label': 'Size (dva)',
                                'y_source_label': 'sigma',
                                'y_tick_steps': 5,
                                'v_hist_bins': 15,
                                'draw_reg': True})

            elif type_comp == 'R2':
                params_ecc.update(
                            {   'y_range': (0, 1),
                                'y_label': 'R2',
                                'y_source_label': 'rsq',
                                'y_tick_steps': 0.2,
                                'v_hist_bins': 20})

            elif type_comp == 'Non-Linearity':
                params_ecc.update(
                            {   'y_range': (0, 1.5),
                                'y_label': 'Non-linearity',
                                'y_source_label': 'non_lin',
                                'y_tick_steps': 0.25,
                                'v_hist_bins': 30})

            elif type_comp == 'Coverage':
                params_ecc.update(
                            {   'y_range': (0, 1),
                                'y_label': 'coverage (%)',
                                'y_source_label': 'cov',
                                'y_tick_steps': 0.2,
                                'v_hist_bins': 20})

            elif type_comp == 'Baseline':
                params_ecc.update(
                            {   'y_range': (-1, 1),
                                'y_label': 'Baseline',
                                'y_source_label': 'baseline',
                                'y_tick_steps': 0.5,
                                'v_hist_bins': 16})

            out1, old_main_fig  = plotter.draw_figure(  parameters = params_ecc,
                                                        plot = 'ecc',
                                                        old_main_fig = old_main_fig)
            f_ecc.append(out1)

        if sub_task == '':
            all_fig1 = gridplot([ [f_ecc[0],f_ecc[1]],
                                  [f_ecc[2],f_ecc[3]]],toolbar_location='right')
        else:
            all_fig1 = gridplot([ [f_ecc[0],f_ecc[1]],
                                  [f_ecc[2],None]],toolbar_location='right')

        exec('output_file_html = opj(html_dir,"{}_{}{}_{}_{}_ecc.html")'.format(roi, task, sub_task, preproc, regist_type))
        html_title = "Subject: {} | ROI: {} | Data: {}{} {} {} | Voxel num: {} | Figures: maps eccentricity vs.".format(
                                            subject, roi, task, sub_task, preproc, regist_type, voxel_num)
        output_file(output_file_html, title = html_title)
        save(all_fig1)
        
        # FIG 2: MAP + COV
        # -----------------

        # map
        old_main_fig = []
        title = '{}: map (n = {})'.format(roi, voxel_num)
        params_map = param_all

        params_map.update({   
                        'x_range': (-15, 15),
                        'y_range': (-15, 15),
                        'x_label': 'Horizontal coordinate (dva)',
                        'y_label': 'Vertical coordinate (dva)',
                        'x_source_label': 'x',
                        'y_source_label': 'y',
                        'x_tick_steps': 5,
                        'y_tick_steps': 5,
                        'v_hist_bins': 12,
                        'h_hist_bins': 12,
                        'main_fig_title': title})

        f_map, old_main_fig1 = plotter.draw_figure(  parameters=params_map, 
                                                     plot='map',
                                                     old_main_fig=old_main_fig)


        # cov
        if sub_task == '':

            title = '{}: density map'.format(roi)
            params_cov = param_all
            params_cov.update({   
                            'x_range': (-15, 15), 
                            'y_range': (-15, 15),
                            'x_label': 'Horizontal coordinate (dva)',
                            'y_label': 'Vertical coordinate (dva)',
                            'x_tick_steps': 5,
                            'y_tick_steps': 5,
                            'smooth_factor': 15,
                            'cmap': 'viridis',
                            'cmap_steps': 10,
                            'col_offset': 0,
                            'vmin': 0,
                            'vmax': 1,
                            'cb_tick_steps': 0.2,
                            'cb_label': 'coverage (norm.)',
                            'link_x': True,
                            'link_y': True})

            params_cov.update({'main_fig_title':   title})

            f_cov, old_main_fig1 = plotter.draw_figure( parameters=params_cov, 
                                                        plot='cov',
                                                        old_main_fig=old_main_fig1)

            all_fig2 = gridplot([ [f_map,f_cov]], toolbar_location='right')
            title_html = "maps parameters and density"

        else:
            all_fig2 = gridplot([ [f_map]], toolbar_location='right')
            title_html = "maps parameters"


        exec('output_file_html = opj(html_dir,"{}_{}{}_{}_{}_map.html")'.format(roi, task, sub_task, preproc, regist_type))
        html_title = "Subject: {} | ROI: {} | Data: {}{} {} {} | Voxel num: {} | Figures: {}".format(
                                            subject, roi, task, sub_task, preproc, regist_type, voxel_num, title_html)
        output_file(output_file_html, title=html_title)
        save(all_fig2)
        

        # FIG 3: laterality
        # ---------------------
        old_main_fig = []
        title = '{}: laterality histogram'.format(roi)
        params_lat = param_all
        params_lat.update(
                    {   'p_width': 500, 
                        'p_height': 500,
                        'dataMat': deriv_data,
                        'x_range': (-2.6, 2.6), 
                        'y_range': (-2.6, 2.6),
                        'vmin': 0,
                        'vmax': 0.2,
                        'weighted_data': True,
                        'main_fig_title': title,
                        'cmap': 'hsv',
                        'cmap_steps': 16,
                        'ang_bins': 36})

        
        params_lat.update({'main_fig_title':   title})
        f_lat, old_main_fig1 = plotter.draw_figure( parameters=params_lat, 
                                                    plot= 'lat',
                                                    old_main_fig=old_main_fig)

        all_fig3 = gridplot([[f_lat]],toolbar_location='right')
        exec('output_file_html = opj(html_dir,"{}_{}{}_{}_{}_lat.html")'.format(roi, task, sub_task, preproc, regist_type))
        html_title = "Subject: {} | ROI: {} | Data: {}{} {} {} | Voxel num: {} | Figures: laterality histogram".format(
                                        subject, roi, task, sub_task, preproc, regist_type, voxel_num)
        
        output_file(output_file_html, title=html_title)
        save(all_fig3)

        # FIG 4: time course
        # ----------------------
        step_r2 = [0,100/3.0,250/3.0,100]
        list_r2_level = ['High','Low']
        step_params = [0,100/3.0,200/3.0,100]
        list_params_level = ['Low','High']
        if sub_task == '':
            list_params = ['ecc','amp','size','cov']
        else:
            list_params = ['ecc','amp','size']

        # tc
        params_tc = param_all
        
        trs = analysis_info['TRs']
        stim_on = ([17,48],[65,96],[113,144],[161,192])
        if sub_task =='':
            stim_dir = (['right'],['top'],['left'],['bottom'])
        elif sub_task == 'sac':
            stim_dir = (['sac'],['sac'],['sac'],['sac'])
        elif sub_task == 'sp':
            stim_dir = (['sp'],['sp'],['sp'],['sp'])

        params_tc.update(
                    {   'p_width': 500, 
                        'p_height': 500,
                        'x_range_map': (-15,15),
                        'y_range_map': (-15,15),
                        'x_label_map': 'Horizontal coord. (dva)',
                        'y_label_map': 'Vertical coord. (dva)',
                        'x_tick_map': 5,
                        'y_tick_map': 5,
                        'x_range_tc': (0,trs*analysis_info['TR']), 
                        'x_label_tc': 'Time (s)',
                        'y_label_tc': 'z score',
                        'x_tick_tc': 50,
                        'tr_dur': analysis_info['TR'],
                        'model_line_color': tuple([254,51,10]),
                        'model_fill_color': tuple([254,51,10])
                    })

        f_tc = []

        # get index matrices
        prct_r2 = np.nanpercentile(a=deriv_data[:,rsq_idx], q=step_r2)
        idx_r2 = []

        for r2_step in np.arange(0,len(step_r2)-1,2):
            idx_r2.append(np.logical_and(deriv_data[:,rsq_idx]>=prct_r2[r2_step],deriv_data[:,rsq_idx]<=prct_r2[r2_step+1]))

        # get voxel number to draw
        for param in list_params:

            exec('prct_{param} = np.nanpercentile(a = deriv_data[:,{param}_idx],q = step_params)'.format(param=param))
            exec('idx_{} = []'.format(param))

            for param_step in np.arange(0,len(step_params)-1,2):
                exec('idx_{param}.append(np.logical_and(deriv_data[:,{param}_idx]>=prct_{param}[param_step],deriv_data[:,{param}_idx]<=prct_{param}[param_step+1]))'.format(param=param))


            exec('num_{} = []'.format(param))

            for r2_step in np.arange(0,2,1):

                for param_step in np.arange(0,2,1):

                    exec('mat = np.where(np.logical_and(idx_r2[r2_step],idx_{}[param_step]))'.format(param))

                    if mat[0].size == 0:
                        exec('num_{}.append(-1)'.format(param))
                    else:
                        exec('num_{}.append(mat[0][np.random.choice(len(mat[0]))])'.format(param))


        for param in list_params:
            exec('num_voxel = num_{}'.format(param))

            for r2_level in list_r2_level:
                if r2_level == 'Low':
                    num_voxel2draw = num_voxel[0:2]
                elif r2_level == 'High':
                    num_voxel2draw = num_voxel[2:4]

                params_tc.update(
                                {   'params': param,
                                    'r2_level': r2_level,
                                    'deriv_mat': deriv_data,
                                    'tc_mat': tc_data,
                                    'tc_model_mat': tc_model_data,
                                    'num_voxel': num_voxel2draw,
                                    'coord_mat':coord_data,
                                    'stim_on': stim_on,
                                    'stim_dir': stim_dir,
                                    'title': '{}'.format(roi)
                                })

                out4,main_fig4  = plotter.draw_figure(parameters=params_tc,
                                                      plot='tc')

                f_tc.append(out4)
        if sub_task == '':
            all_fig4 = gridplot([   [f_tc[0],f_tc[1]],
                                    [f_tc[2],f_tc[3]],
                                    [f_tc[4],f_tc[5]],
                                    [f_tc[6],f_tc[7]]], toolbar_location=None)
        else:
            all_fig4 = gridplot([   [f_tc[0],f_tc[1]],
                                    [f_tc[2],f_tc[3]],
                                    [f_tc[4],f_tc[5]]], toolbar_location=None)

        exec('output_file_html = opj(html_dir,"{}_{}{}_{}_{}_tc.html")'.format(roi, task, sub_task, preproc, regist_type))
        html_title = "Subject: {} | ROI: {} | Data: {}{} {} {} | Voxel num: {} | Figures: time course".format(
                                            subject, roi, task, sub_task, preproc, regist_type, voxel_num)
        output_file(output_file_html, title = html_title)
        save(all_fig4)

    else:

        print("drawing {}_{}_{}_{} figures not possible: n = {}".format(roi, task, preproc, regist_type, voxel_num))
