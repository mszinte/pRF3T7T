# to run in mesocenter server
# cd ~/projects/PredictEye/mri_analysis/
# sh prf/post_fit/run_post_fit.sh sub-01

echo $1
python prf/post_fit/post_fit.py $1 T1w fmriprep_dct
python prf/post_fit/post_fit.py $1 fsLR_den-170k fmriprep_dct surf
python prf/post_fit/post_fit.py $1 fsLR_den-170k fmriprep_dct subc
python prf/post_fit/post_fit.py $1 T1w fmriprep_dct_pca
python prf/post_fit/post_fit.py $1 fsLR_den-170k fmriprep_dct_pca surf
python prf/post_fit/post_fit.py $1 fsLR_den-170k fmriprep_dct_pca subc

