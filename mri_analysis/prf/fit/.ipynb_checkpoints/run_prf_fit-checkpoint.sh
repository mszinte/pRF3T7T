# to run in mesocenter server
# cd ~/projects/pRF3T7T/mri_analysis/
# sh prf/fit/run_prf_fit.sh sub-01

echo $1
python prf/fit/submit_fit_jobs.py $1 pRF3T T1w fmriprep_dct
python prf/fit/submit_fit_jobs.py $1 pRF7T T1w fmriprep_dct
