# to run on mesocenter server
# cd ~/projects/pRF3T7T/mri_analysis/
# sh webgl/run_webgl.sh sub-01
echo $1
python webgl/pycortex_webgl.py $1 fmriprep_dct T1w 1 1
