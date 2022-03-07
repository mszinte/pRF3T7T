# to run in mesocenter server
# cd ~/projects/PredictEye/mri_analysis/
# sh prf/fit/run_prf_fit.sh sub-01

echo $1
python prf/fit/submit_fit_jobs.py $1 T1w fmriprep_dct
python prf/fit/submit_fit_jobs.py $1 fsLR_den-170k fmriprep_dct surf
python prf/fit/submit_fit_jobs.py $1 fsLR_den-170k fmriprep_dct subc
python prf/fit/submit_fit_jobs.py $1 T1w fmriprep_dct_pca
python prf/fit/submit_fit_jobs.py $1 fsLR_den-170k fmriprep_dct_pca surf
python prf/fit/submit_fit_jobs.py $1 fsLR_den-170k fmriprep_dct_pca subc

