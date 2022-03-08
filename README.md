# __*pRF3T7T*__
By :      Martin SZINTE <br>
With :    Penelope Tilsley, Jan-Patrick Stillmann<br>
Version:  1.0<br>

# Version description
Comparison of 3 and 7T pRF experiment for sub-01

# Task
1. pRFexp: population receptive field task adapted to 3T sequence ([repo](https://invibe.nohost.me/gitlab/mszinte/pRFexp))
1. pRFexp7T: population receptive field task adapted to 7T sequence ([repo](https://invibe.nohost.me/gitlab/mszinte/prfexp7t))

# MRI Analysis

## Data curation
1. Copy 3T data from PredictEye project
2. convert to BIDS 7T data (Penelope)
3. edit fmap json files by hand (ses-02 : 3T, ses-03 : 7T)
4. Put 3T anatomy and edited segmentation
4. transfer all data to server
4. check BIDS validity

## Pre-processing
1. run mriqc on mesocentre using _mri_analysis/preproc/mriqc_sbatch.py_
1. run fmriprep on mesocentre using _mri_analysis/preproc/fmriprep_sbatch.py_
3. run pybest (modified repo to save niftis) to high pass filter and denoised the data with _/preproc/pybest_sbatch.py_
4. copy files in pp_data and average task runs (including leave-one-out procedure) together with _preproc/preproc_end.py_
5. Import in pycortex with _preproc/pycortex_import.py_

## Post-processing

### Data saving structure
Subject(s) (sub-01)<br>
x 01 preprocessing steps (fmriprep_dct, fmriprep_dct_pca)<br>
x 02 contrasts (pRF3T, pRF7T)<br>
x 01 registration types (T1w)<br>
x 01 averaging methods (avg: fit across averaged runs)<br>

### pRF
1. run the prf fit with _prf/fit/run_prf_fit.sh_
2. compute pRF parameters with _prf/post_fit/run_post_fit.sh_
3. make pycortex maps using with _prf/post_fit/run_pycortex_maps.sh_ 

### Webgl
1. Combine pRF3T and pRF7T analysis in single webgl per subject using _webgl/pycortex_webgl.py_ or _webgl/run_webgl.sh_
2. send index.py to webapp using _webgl/send_index.sh_