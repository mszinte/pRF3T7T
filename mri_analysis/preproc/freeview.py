"""
-----------------------------------------------------------------------------------------
freeview.py
-----------------------------------------------------------------------------------------
Goal of the script:
Make freeview sagital video of segmentation (to run before and after manual edit)
-----------------------------------------------------------------------------------------
Input(s):
sys.argv[1]: subject

sys.argv[2]: slice start number (e.g. 0)
sys.argv[3]: slice end number (e.g. 255)
sys.argv[4]: video name ('before_edit', 'after_edit')
-----------------------------------------------------------------------------------------
Output(s):
preprocessed files
-----------------------------------------------------------------------------------------
To run:
1. cd to function
>> cd ~/disks/meso_H/projects/PredictEye/mri_analysis/
2. run python command
python /preproc/freeview.py [main directory] [project name] [subject num] 
                            [slice start] [slice end] [video name]
-----------------------------------------------------------------------------------------
Exemple:
cd ~/disks/meso_H/projects/PredictEye/mri_analysis/
python preproc/freeview.py ~/disks/meso_S/data/ PredictEye sub-01 50 250 before_edit
-----------------------------------------------------------------------------------------
Written by Martin Szinte (martin.szinte@gmail.com)
-----------------------------------------------------------------------------------------
"""

# imports modules
import subprocess as sb
import os
import glob
import ipdb
import sys
import json
import numpy as np
deb = ipdb.set_trace

# Inputs

main_dir = sys.argv[1]
project_dir = sys.argv[2]
subject = sys.argv[3]
x_start = int(sys.argv[4])
x_end = int(sys.argv[5])
expl = sys.argv[6]

# define directory
fs_dir = "{main_dir}/{project_dir}/deriv_data/fmriprep/freesurfer/{subject}".format(main_dir = main_dir, project_dir = project_dir, subject = subject)
bids_dir = "{main_dir}/{project_dir}/bids_data/{subject}".format(main_dir = main_dir, project_dir = project_dir, subject = subject)
vid_dir = "{fs_dir}/vid/{expl}".format(fs_dir = fs_dir, expl = expl)
image_dir = "{vid_dir}/img".format(vid_dir = vid_dir)
sh_dir = "{vid_dir}/{subject}_{expl}.sh".format(vid_dir = vid_dir, subject = subject, expl = expl)
try: os.makedirs(image_dir)
except: pass

# list commands
anat_cmd = '-v {t1mgz}:grayscale=10,100'.format(t1mgz = '{fs_dir}/mri/T1.mgz'.format(fs_dir = fs_dir))
volumes_cmd = '-f {fs_dir}/surf/lh.white:color=red:edgecolor=red \
-f {fs_dir}/surf/rh.white:color=red:edgecolor=red \
-f {fs_dir}/surf/lh.pial:color=white:edgecolor=white \
-f {fs_dir}/surf/rh.pial:color=white:edgecolor=white '.format(fs_dir = fs_dir)

slice_cmd = ''
for x in np.arange(x_start,x_end):
    if x < 10:x_name = '00{x}'.format(x = x)
    elif x >= 10 and x < 100:x_name = '0{x}'.format(x = x)
    else: x_name = '{x}'.format(x = x)

    slice_cmd += ' -slice {x} 127 127 \n -ss {image_dir}/{x_name}.png \n'.format(x = x,image_dir = image_dir,x_name = x_name)

# main command
freeview_cmd = '{anat_cmd} {volumes_cmd} -viewport sagittal {slice_cmd}-quit '.format(
                            anat_cmd = anat_cmd,
                            volumes_cmd = volumes_cmd,
                            slice_cmd = slice_cmd)

of = open(sh_dir, 'w')
of.write(freeview_cmd)
of.close()

# run freeview cmd
sb.call('freeview -cmd {sh_dir}'.format(sh_dir = sh_dir),shell=True)

# convert images in video
video_command = 'ffmpeg -framerate 5 -pattern_type glob -i "{image_dir}/*.png" -b:v 2M -c:v mpeg4 {vid_dir}/{subject}_{expl}.mp4'.format(
                                        image_dir = image_dir, vid_dir = vid_dir, 
                                        subject = subject, expl = expl)

os.system(video_command)