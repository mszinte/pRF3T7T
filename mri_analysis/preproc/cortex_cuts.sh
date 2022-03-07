# -----------------------------------------------------------------------------------------
# cortex_cuts.sh
# -----------------------------------------------------------------------------------------
# Goal of the script:
# Run tksurfer to cut the cortex
# -----------------------------------------------------------------------------------------
# Input(s):
# $1: project directory
# $2: subject name (e.g. sub-01)
# $3: hemisphere (lh or rh)
# $3: mesocentre login ID
# -----------------------------------------------------------------------------------------
# Output(s):
# edited brainmask.mgz and orignal brainmask_orog.mgz
# -----------------------------------------------------------------------------------------
# To run:
# 1. cd to function
# >> cd ~/disks/meso_H/projects/PredictEye/mri_analysis/
# 2. run shell command
# sh preproc/cortex_cuts.sh [main directory] [subject name] [hemisphere] [mesocentre_ID]
# -----------------------------------------------------------------------------------------
# Exemple:
# cd ~/disks/meso_H/projects/PredictEye/mri_analysis/
# sh preproc/cortex_cuts.sh /scratch/mszinte/data/PredictEye sub-01 rh mszinte
# -----------------------------------------------------------------------------------------
# Written by Martin Szinte (martin.szinte@gmail.com)
# -----------------------------------------------------------------------------------------

# rsync to desktop (faster processing)
echo "\n>> Copying the files to the desktop"
rsync -azuv  --progress $4@login.mesocentre.univ-amu.fr:$1/deriv_data/fmriprep/freesurfer/$2 ~/Desktop/temp_data/

# Check + edit pial surface
echo "\n>> Proceed to the cortex cuts : "
echo "\n>> When you are done, save the patch as '$2/surf/$3.full.patch.3d'\n"

freeview -f ~/Desktop/temp_data/$2/surf/$3.inflated:annot=aparc.a2009s

# move the file to the right place
while true; do
	read -p "Do you wish to transfer the patch to the mesocentre? (y/n) " yn
	case $yn in
		[Yy]* ) echo "\n>> Uploading the $3 patch to mesocentre";\
				rsync -avuz ~/Desktop/temp_data/$2/surf/$3.full.patch.3d $4@login.mesocentre.univ-amu.fr:$1/deriv_data/fmriprep/freesurfer/$2/surf/
        break;;
		[Nn]* ) echo "\n>> No uploading of the brainmasks to mesocentre";\
				exit;;
		* ) echo "Please answer yes or no.";;
	esac
done