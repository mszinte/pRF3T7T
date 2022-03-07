# -----------------------------------------------------------------------------------------
# pial_edits.py
# -----------------------------------------------------------------------------------------
# Goal of the script:
# Run freeview to edit the segmentation brainmask localy before transfering it back to 
# the mesocentre
# -----------------------------------------------------------------------------------------
# Input(s):
# $1: project directory
# $2: subject name (e.g. sub-01)
# $3: mesocentre login ID
# -----------------------------------------------------------------------------------------
# Output(s):
# edited brainmask.mgz and orignal brainmask_orog.mgz
# -----------------------------------------------------------------------------------------
# To run:
# 1. cd to function
# >> cd ~/disks/meso_H/projects/PredictEye/mri_analysis/
# 2. run shell command
# sh preproc/pial_edits.sh [main directory] [subject name] [mesocentre_ID]
# -----------------------------------------------------------------------------------------
# Exemple:
# cd ~/disks/meso_H/projects/PredictEye/mri_analysis/
# sh preproc/pial_edits.sh /scratch/mszinte/data/PredictEye sub-01 mszinte
# -----------------------------------------------------------------------------------------
# Written by Martin Szinte (martin.szinte@gmail.com)
# -----------------------------------------------------------------------------------------


# rsync to desktop (faster processing)
echo "\n>> Copying the files to the desktop"
rsync -azuv  --progress $3@login.mesocentre.univ-amu.fr:$1/deriv_data/fmriprep/freesurfer/$2 ~/Desktop/temp_data/

# create a copy of the origninal brainmask
NEWFILE=~/Desktop/temp_data/$2/mri/brainmask_orig.mgz
if [ -f "$NEWFILE" ]; then
    echo "\n>> A copy of original brainmask already exists: $NEWFILE"
else
	echo "\n>> Creating a copy of original brainmask: $NEWFILE"
	cp ~/Desktop/temp_data/$2/mri/brainmask.mgz $NEWFILE
fi

# Check + edit pial surface
echo "\n>> Edit the brain mask following https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/PialEdits_freeview"
echo ">> When you are done, save the brainmask and quit freeview"
freeview -v ~/Desktop/temp_data/$2/mri/T1.mgz \
~/Desktop/temp_data/$2/mri/T2.mgz \
~/Desktop/temp_data/$2/mri/brainmask.mgz \
-f ~/Desktop/temp_data/$2/surf/lh.white:edgecolor=yellow \
~/Desktop/temp_data/$2/surf/lh.pial:edgecolor=red \
~/Desktop/temp_data/$2/surf/rh.white:edgecolor=yellow \
~/Desktop/temp_data/$2/surf/rh.pial:edgecolor=red

# move the file to the right place
while true; do
	read -p "Do you wish to transfer the edited brainmask to the mesocentre? (y/n) " yn
	case $yn in
		[Yy]* ) echo "\n>> Uploading of the brainmasks to mesocentre";\
				rsync -avuz ~/Desktop/temp_data/$2/mri/brainmask.mgz $3@login.mesocentre.univ-amu.fr:$1/deriv_data/fmriprep/freesurfer/$2/mri/
				rsync -avuz ~/Desktop/temp_data/$2/mri/brainmask_orig.mgz $3@login.mesocentre.univ-amu.fr:$1/deriv_data/fmriprep/freesurfer/$2/mri/
        break;;
		[Nn]* ) echo "\n>> No uploading of the brainmasks to mesocentre";\
				exit;;
		* ) echo "Please answer yes or no.";;
	esac
done
