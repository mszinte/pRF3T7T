# to run in invibe server
# cd ~/disks/meso_H/projects/pRF3T7T/mri_analysis/
# sh prf/post_fit/run_pycortex_maps.sh sub-01

echo $1
ipython prf/post_fit/pycortex_maps.py $1 pRF3T T1w fmriprep_dct 0
ipython prf/post_fit/pycortex_maps.py $1 pRF7T T1w fmriprep_dct 0
