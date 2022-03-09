# to run in mesocenter server
# cd ~/projects/pRF3T7T/mri_analysis/
# sh prf/post_fit/run_post_fit.sh sub-01

echo $1
python prf/post_fit/post_fit.py $1 pRF3T T1w fmriprep_dct
python prf/post_fit/post_fit.py $1 pRF7T T1w fmriprep_dct