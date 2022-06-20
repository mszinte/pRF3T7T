def set_pycortex_config_file(data_folder):

    # Import necessary modules
    import os
    import cortex
    # import ipdb
    from pathlib import Path
    # deb = ipdb.set_trace

    # Define the new database and colormaps folder
    pycortex_db_folder = data_folder + '/derivatives/pp_data/cortex/db/'
    pycortex_cm_folder = data_folder + '/derivatives/pp_data/cortex/colormaps/'

    # Get pycortex config file location
    pycortex_config_file  = cortex.options.usercfg

    # Create name of new config file that will be written
    new_pycortex_config_file = pycortex_config_file[:-4] + '_new.cfg'

    # Create the new config file
    Path(new_pycortex_config_file).touch()

    # Open the config file in read mode and the newly created one in write mode.
    # Loop over every line in the original file and copy it into the new one.
    # For the lines containing either 'filestore' or 'colormap', it will
    # change the saved folder path to the newly created one above (e.g. pycortex_db_folder)
    with open(pycortex_config_file, 'r') as fileIn:
        with open(new_pycortex_config_file, 'w') as fileOut:

            for line in fileIn:

                if 'filestore' in line:
                    newline = 'filestore=' + pycortex_db_folder
                    fileOut.write(newline)
                    newline = '\n'

                elif 'colormaps' in line:
                    newline = 'colormaps=' + pycortex_cm_folder
                    fileOut.write(newline)
                    newline = '\n'

                else:
                    newline = line

                fileOut.write(newline)

    
    # Renames the original config file als '_old' and the newly created one to the original name
    os.rename(pycortex_config_file, pycortex_config_file[:-4] + '_old.cfg')
    os.rename(new_pycortex_config_file, pycortex_config_file)
    return None

def draw_cortex_vertex(subject,xfmname,data,vmin,vmax,description,cortex_type='VolumeRGB',cmap='Viridis',cbar = 'discrete',cmap_steps = 255,\
                        alpha = None,depth = 1,thick = 1,height = 1024,sampler = 'nearest',\
                        with_curvature = True,with_labels = False,with_colorbar = False,\
                        with_borders = False,curv_brightness = 0.95,curv_contrast = 0.05,add_roi = False,\
                        roi_name = 'empty',col_offset = 0, zoom_roi = None, zoom_hem = None, zoom_margin = 0.0,):
    """
    Plot brain data onto a previously saved flatmap.
    Parameters
    ----------
    subject             : subject id (e.g. 'sub-001')
    xfmname             : xfm transform
    data                : the data you would like to plot on a flatmap
    cmap                : colormap that shoudl be used for plotting
    vmins               : minimal values of 1D 2D colormap [0] = 1D, [1] = 2D
    vmaxs               : minimal values of 1D/2D colormap [0] = 1D, [1] = 2D
    description         : plot title
    cortex_type         : cortex function to create the volume (VolumeRGB, Volume2D, VertexRGB)
    cbar                : color bar layout
    cmap_steps          : number of colormap bins
    alpha               : alpha map
    depth               : Value between 0 and 1 for how deep to sample the surface for the flatmap (0 = gray/white matter boundary, 1 = pial surface)
    thick               : Number of layers through the cortical sheet to sample. Only applies for pixelwise = True
    height              : Height of the image to render. Automatically scales the width for the aspect of the subject's flatmap
    sampler             : Name of sampling function used to sample underlying volume data. Options include 'trilinear', 'nearest', 'lanczos'
    with_curvature      : Display the rois, labels, colorbar, annotated flatmap borders, or cross-hatch dropout?
    with_labels         : Display labels?
    with_colorbar       : Display pycortex' colorbar?
    with_borders        : Display borders?
    curv_brightness     : Mean brightness of background. 0 = black, 1 = white, intermediate values are corresponding grayscale values.
    curv_contrast       : Contrast of curvature. 1 = maximal contrast (black/white), 0 = no contrast (solid color for curvature equal to curvature_brightness).
    add_roi             : add roi -image- to overlay.svg
    roi_name            : roi name
    col_offset          : colormap offset between 0 and 1
    zoom_roi            : name of the roi on which to zoom on
    zoom_hem            : hemifield fo the roi zoom
    zoom_margin         : margin in mm around the zoom
    Returns
    -------
    braindata - pycortex volumr or vertex file
    """
    
    import cortex
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    from matplotlib import cm
    import matplotlib as mpl
    import ipdb
    
    deb = ipdb.set_trace
    
    # define colormap
    try: base = plt.cm.get_cmap(cmap)
    except: base = cortex.utils.get_cmap(cmap)
    
    if '_alpha' in cmap: base.colors = base.colors[1,:,:]
    val = np.linspace(0, 1,cmap_steps+1,endpoint=False)
    colmap = colors.LinearSegmentedColormap.from_list('my_colmap',base(val), N = cmap_steps)
    
    if cortex_type=='VolumeRGB':
        # convert data to RGB
        vrange = float(vmax) - float(vmin)
        norm_data = ((data-float(vmin))/vrange)*cmap_steps
        mat = colmap(norm_data.astype(int))*255.0
        alpha = alpha*255.0

        # define volume RGB
        braindata = cortex.VolumeRGB(channel1 = mat[...,0].T.astype(np.uint8),
                                     channel2 = mat[...,1].T.astype(np.uint8),
                                     channel3 = mat[...,2].T.astype(np.uint8),
                                     alpha = alpha.T.astype(np.uint8),
                                     subject = subject,
                                     xfmname = xfmname)
    elif cortex_type=='Volume2D':
        braindata = cortex.Volume2D(dim1 = data.T,
                                 dim2 = alpha.T,
                                 subject = subject,
                                 xfmname = xfmname,
                                 description = description,
                                 cmap = cmap,
                                 vmin = vmin[0],
                                 vmax = vmax[0],
                                 vmin2 = vmin[1],
                                 vmax2 = vmax[1])
    elif cortex_type=='VertexRGB':
        
        # convert data to RGB
        vrange = float(vmax) - float(vmin)
        norm_data = ((data-float(vmin))/vrange)*cmap_steps
        mat = colmap(norm_data.astype(int))*255.0
        alpha = alpha*255.0
        
        # define Vertex RGB
        braindata = cortex.VertexRGB( red = mat[...,0].astype(np.uint8),
                                      green = mat[...,1].astype(np.uint8),
                                      blue = mat[...,2].astype(np.uint8),
                                      subject = subject,
                                      alpha = alpha.astype(np.uint8))
        
    braindata_fig = cortex.quickshow(braindata = braindata,
                                     depth = depth,
                                     thick = thick,
                                     height = height,
                                     sampler = sampler,
                                     with_curvature = with_curvature,
                                     with_labels = with_labels,
                                     with_colorbar = with_colorbar,
                                     with_borders = with_borders,
                                     curvature_brightness = curv_brightness,
                                     curvature_contrast = curv_contrast)

   
    if cbar == 'polar':
        
        try: base = plt.cm.get_cmap(cmap)
        except: base = cortex.utils.get_cmap(cmap)
        
        val = np.arange(1,cmap_steps+1)/cmap_steps - (1/(cmap_steps*2))
        val = np.fmod(val+col_offset,1)
        colmap = colors.LinearSegmentedColormap.from_list('my_colmap',base(val),N = cmap_steps)

        cbar_axis = braindata_fig.add_axes([0.5, 0.07, 0.8, 0.2], projection='polar')
        norm = colors.Normalize(0, 2*np.pi)
        t = np.linspace(0,2*np.pi,200,endpoint=True)
        r = [0,1]
        rg, tg = np.meshgrid(r,t)
        im = cbar_axis.pcolormesh(t, r, tg.T,norm= norm, cmap = colmap)
        cbar_axis.set_yticklabels([])
        cbar_axis.set_xticklabels([])
        cbar_axis.set_theta_zero_location("W")

        cbar_axis.spines['polar'].set_visible(False)

    elif cbar == 'ecc':
        
        # Ecc color bar
        colorbar_location = [0.5, 0.07, 0.8, 0.2]
        n = 200
        cbar_axis = braindata_fig.add_axes(colorbar_location, projection='polar')

        t = np.linspace(0,2*np.pi, n)
        r = np.linspace(0,1, n)
        rg, tg = np.meshgrid(r,t)
        c = tg
            
        im = cbar_axis.pcolormesh(t, r, c, norm = mpl.colors.Normalize(0, 2*np.pi), cmap = colmap)
        cbar_axis.tick_params(pad = 1,labelsize = 15)
        cbar_axis.spines['polar'].set_visible(False)
            
        # superimpose new axis for dva labeling
        box = cbar_axis.get_position()
        cbar_axis.set_yticklabels([])
        cbar_axis.set_xticklabels([])
        axl = braindata_fig.add_axes(  [1.8*box.xmin,
                                        0.5*(box.ymin+box.ymax),
                                        box.width/600,
                                        box.height*0.5])
        axl.spines['top'].set_visible(False)
        axl.spines['right'].set_visible(False)
        axl.spines['bottom'].set_visible(False)
        axl.yaxis.set_ticks_position('right')
        axl.xaxis.set_ticks_position('none')
        axl.set_xticklabels([])
        axl.set_yticklabels(np.linspace(vmin,vmax,3),size = 'x-large')
        axl.set_ylabel('$dva$\t\t', rotation = 0, size = 'x-large')
        axl.yaxis.set_label_coords(box.xmax+30,0.4)
        axl.patch.set_alpha(0.5)

    elif cbar == 'discrete':

        # Discrete color bars
        # -------------------
        colorbar_location= [0.9, 0.05, 0.03, 0.25]
        cmaplist = [colmap(i) for i in range(colmap.N)]

        # define the bins and normalize
        if cortex_type=='Volume2D':
            bounds = np.linspace(vmin[0], vmax[0], cmap_steps + 1)
            bounds_label = np.linspace(vmin[0], vmax[0], 3)
        else:
            bounds = np.linspace(vmin, vmax, cmap_steps + 1)  
            bounds_label = np.linspace(vmin, vmax, 3)

        norm = mpl.colors.BoundaryNorm(bounds, colmap.N)
            
        cbar_axis = braindata_fig.add_axes(colorbar_location)
        cb = mpl.colorbar.ColorbarBase(cbar_axis,cmap = colmap,norm = norm,ticks = bounds_label,boundaries = bounds)

    # add to overalt
    if add_roi == True:
        cortex.utils.add_roi(   data = braindata,
                                name = roi_name,
                                open_inkscape = False,
                                add_path = False,
                                depth = depth,
                                thick = thick,
                                sampler = sampler,
                                with_curvature = with_curvature,
                                with_colorbar = with_colorbar,
                                with_borders = with_borders,
                                curvature_brightness = curv_brightness,
                                curvature_contrast = curv_contrast)

    return braindata


def prf_fit2deriv(input_mat, stim_width, stim_height):
    """
    Convert pRF fitting value to pRF derivatives
   
    Parameters
    ----------
    input_mat: input matrix
    stim_width: stimulus width in deg [for pRF only]
    stim_heigth: stimulus height in deg [for pRF only]

    Returns
    -------
    deriv: derivative of pRF analysis

    stucture output:
    columns: 1->size of input
    row00 : R2
    row01 : eccentricity in deg
    row02 : polar angle real component in deg
    row03 : polar angle imaginary component in deg
    row04 : size in deg
    row05 : amplitude
    row06 : baseline
    row07 : coverage or nan
    row08 : x
    row09 : y
    row10 : leave-one-out test/prediction rsquare average
    ['rsq','ecc','polar_real','polar_imag','size','amp','baseline','x','y','cov','loo_rsq']
    """

    # Imports
    # -------
    # General imports
    import os
    import nibabel as nb
    import glob
    import numpy as np
    import ipdb
    deb = ipdb.set_trace
    
    # Popeye imports
    from popeye.spinach import generate_og_receptive_fields

    # Get data details
    # ----------------
    fit = []
    fit = input_mat

    # Compute derived measures from prfs/pmfs
    # ---------------------------------------
    # get data index
    x_idx, y_idx, sigma_idx, beta_idx, baseline_idx, rsq_idx = 0, 1, 2, 3, 4, 5

    # change to nan empty voxels
    fit[fit[...,rsq_idx] == 0] = np.nan
    
    # r-square
    rsq = fit[...,rsq_idx]

    # eccentricity
    ecc = np.nan_to_num(np.sqrt(fit[...,x_idx]**2 + fit[...,y_idx]**2))

    # polar angle
    complex_polar = fit[...,x_idx] + 1j * fit[...,y_idx]
    normed_polar = complex_polar / np.abs(complex_polar)
    polar_real = np.real(normed_polar)
    polar_imag = np.imag(normed_polar)
    
    # size
    size_ = fit[...,sigma_idx].astype(np.float64)
    size_[size_<1e-4] = 1e-4

    # amplitude
    amp = fit[...,beta_idx]
    
    # baseline
    baseline = fit[...,baseline_idx]

    # coverage
    deg_x, deg_y = np.meshgrid(np.linspace(-30, 30, 50), np.linspace(-30, 30, 50))         # define prfs in visual space
    flat_fit = fit.reshape((-1, fit.shape[-1])).astype(np.float64)
    rfs = generate_og_receptive_fields( flat_fit[:,x_idx],
                                        flat_fit[:,y_idx],
                                        flat_fit[:,sigma_idx],
                                        flat_fit[:,beta_idx].T*0+1,
                                        deg_x,
                                        deg_y)

    total_prf_content = rfs.reshape((-1, flat_fit.shape[0])).sum(axis=0)
    log_x = np.logical_and(deg_x >= -stim_width/2.0, deg_x <= stim_width/2.0)
    log_y = np.logical_and(deg_y >= -stim_height/2.0, deg_y <= stim_height/2.0)
    stim_vignet = np.logical_and(log_x,log_y)
    cov = rfs[stim_vignet, :].sum(axis=0) / total_prf_content
    cov = cov.reshape(baseline.shape)

    # x
    x = fit[...,x_idx]

    # y
    y = fit[...,y_idx]

    # Save results
    if np.ndim(fit) == 4:
        deriv = np.zeros((fit.shape[0],fit.shape[1],fit.shape[2],11))*np.nan
    elif np.ndim(fit) == 2:
        deriv = np.zeros((fit.shape[0],11))*np.nan
        
    deriv[...,0]  = rsq
    deriv[...,1]  = ecc
    deriv[...,2]  = polar_real
    deriv[...,3]  = polar_imag
    deriv[...,4]  = size_
    deriv[...,5]  = amp
    deriv[...,6]  = baseline
    deriv[...,7]  = cov
    deriv[...,8]  = x
    deriv[...,9]  = y
        
    deriv = deriv.astype(np.float32)

    return deriv