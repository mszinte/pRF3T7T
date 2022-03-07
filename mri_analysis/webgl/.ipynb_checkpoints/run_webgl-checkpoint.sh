# to run on mesocenter server
# cd ~/projects/PredictEye/mri_analysis/
# sh webgl/run_webgl.sh

for sub in sub-01 sub-02 sub-03 sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-11 sub-12 sub-13 sub-14 sub-17 sub-20 sub-21 sub-22 sub-23 sub-24 sub-25
do
echo $sub
python webgl/pycortex_webgl.py /scratch/mszinte/data/PredictEye $sub fmriprep_dct T1w 1 1
done
exit 0