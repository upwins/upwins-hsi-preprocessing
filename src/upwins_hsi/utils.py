
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt 
import platform
import psutil
import sys
import os
import spectral
import numpy as np
import pandas as pd
import math       
import importlib
import copy

def class_vars(myClass):
    for name in dir(myClass):
        if not name.startswith("__"):
            print(f'{name}: {myClass.name}')

def R2Normalize(x,y):  
    normalized_x =   (x - np.mean(x))/np.std(x)
    result =   normalized_x*np.std(y) + np.mean(y)
    return result

def spatial_smoothing(arr, mask=None):
    '''
    Smooths the image by averaging each pixel spectrum with its neighbors.
    mask_sum is used to sum the number of nonzeo neighbors (neighbors with data)
        for the averaging.
    '''
    if mask is None:
        mask = (np.max(arr, axis=2) > 0).astype(np.float32)
    mask_sum = copy.copy(mask)
    # Smooth the image by taking the mean of each pixel at location (r,c) with the pixels at:
    # (r,c), (r+1,c), (r,c+1), and (r+1,c+1). 
    # Edge cases are handeled by averaging with pixels mirror imaged back into the array.
    nr, nc, nb = arr.shape
    arr_out = copy.copy(arr)
    # average each pixel spectrum with the spectrum for the pixel directly below (one row down).
    # for the last row, take its average with the second-to-last row.
    arr_out[0:(nr-1), :, :] = arr_out[0:(nr-1), :, :] + arr[1:, :, :]
    arr_out[(nr-1), :, :] = arr_out[(nr-1), :, :] + arr[(nr-2), :, :]
    mask_sum[0:(nr-1), :] = mask_sum[0:(nr-1), :] + mask[1:, :]
    mask_sum[(nr-1), :] = mask_sum[(nr-1), :] + mask[(nr-2), :]
    # average each pixel spectrum with the spectrum for the pixel directly to the right (one column to the right).
    # for the last column, take its average with the second-to-last column .
    arr_out[:, 0:(nc-1), :] = arr_out[:, 0:(nc-1), :] + arr[:, 1:, :]
    arr_out[:, (nc-1), :] = arr_out[:, (nc-1), :] + arr[:, (nc-2), :]
    mask_sum[:, 0:(nc-1)] = mask_sum[:, 0:(nc-1)] + mask[:, 1:]
    mask_sum[:, (nc-1)] = mask_sum[:, (nc-1)] + mask[:, (nc-2)]
    # average each pixel spectrum with the spectrum for the pixel diagnol down and to the right (plus one column, plus one row).
    # for the last row and column, average with previous row or column appropriately.
    arr_out[0:(nr-1), 0:(nc-1), :] = arr_out[0:(nr-1), 0:(nc-1), :] + arr[1:, 1:, :]
    mask_sum[0:(nr-1), 0:(nc-1)] = mask_sum[0:(nr-1), 0:(nc-1)] + mask[1:, 1:]
    # bottom-right corner, average with pixel one row up, one column left
    arr_out[(nr-1), (nc-1), :] = arr_out[(nr-1), (nc-1), :] + arr[(nr-2), (nc-1), :]
    mask_sum[(nr-1), (nc-1)] = mask_sum[(nr-1), (nc-1)] + mask[(nr-2), (nc-1)]
    # last row, average with pixels up one row, right one column
    arr_out[(nr-1), 0:(nc-1), :] = arr_out[(nr-1), 0:(nc-1), :] + arr[(nr-2), 1:, :]
    mask_sum[(nr-1), 0:(nc-1)] = mask_sum[(nr-1), 0:(nc-1)] + mask[(nr-2), 1:]
    # last coumn, average with left one column, down one row
    arr_out[0:(nr-1), (nc-1), :] = arr_out[0:(nr-1), (nc-1), :] + arr[1:, (nc-2), :]
    mask_sum[0:(nr-1), (nc-1)] = mask_sum[0:(nr-1), (nc-1)] + mask[1:, (nc-2)]
    '''
    plt.figure(figsize=(20,20))
    plt.imshow(mask_sum, interpolation='nearest')
    plt.colorbar()
    plt.savefig(f'mask_sum_{np.random.randint(1, 101)}.png', dpi=200, bbox_inches='tight')
    plt.close()
    '''
    # Set the values of zero in the mask to 1 to avoid dividing by zero
    mask_sum[mask_sum==0] = 1
    for i in range(arr_out.shape[2]):
        arr_out[:,:,i] = arr_out[:,:,i]/mask_sum
    return arr_out




def makePDF(results, data, fname_pdf, settings):
    # Open the PDF file. 
    p = PdfPages(fname_pdf)     
    
    # ======== Plot the RGB and Mask Images, Side-by-Side ========
    # Plot the RGB image
    fig, ax = plt.subplots(ncols=2, layout='compressed')
    im0 = ax[0].imshow(results['RGB_image'], interpolation=None)
    ax[0].set_xticks([])
    ax[0].set_yticks([])
    #ax.set_facecolor('lightgray') # If we want to see the plot area
    # Main Title Line (using default or larger size)
    main_title = results['RGB_image_main_title']
    ax[0].text(0.5,    # x-coordinate (0.5 is center)
            1.07,   # y-coordinate (slightly above the axes)
            main_title,
            horizontalalignment='center',
            verticalalignment='bottom', # Aligns bottom of text with y-coordinate
            transform=ax[0].transAxes,  # Use Axes coordinates (0,0 to 1,1)
            fontsize=plt.rcParams['axes.titlesize'], # Default title size
                fontweight=plt.rcParams['axes.titleweight'] # Default title weight
            )
    # Subtitle Line (smaller font size)
    sub_title = results['RGB_image_sub_title']
    subtitle_fontsize = 8
    ax[0].text(0.5,    # x-coordinate (center)
            1.01,   # y-coordinate (below the main title)
            sub_title,
            horizontalalignment='center',
            verticalalignment='bottom',
            transform=ax[0].transAxes,
            fontsize=subtitle_fontsize
        )      
    # Plot the Mask image
    plt.subplot(1, 2, 2)
    im1 = ax[1].imshow(results['Mask_image'], interpolation=None)
    ax[1].set_title(results['Mask_image_title'])
    ax[1].set_xticks([])
    ax[1].set_yticks([])
    plt.colorbar(im1, ax=ax);
    plt.savefig(p, format='pdf')     
    plt.close() 
    
    # ======== Show the Classification Images ========   
    
    for i,output in enumerate(results['method_outputs']):
        class_image = output['class_image']
        print(f'output[class_image] shape: {class_image.shape}')
        plt.figure(figsize=(7,3))
        # Generate a colormap with a unique color for each unique non-zero value
        num_colors = len(output['class_indices'])  
        colors = plt.cm.nipy_spectral(np.linspace(0, 1, num_colors+1))
        # Create a dictionary mapping integer values to colors
        color_map_dict = {0: [0, 0, 0, 1]}  # 0 is black (RGBA)
        for i, val in enumerate(output['class_indices'][1:]):
            color_map_dict[val] = colors[i+1]
        # Create a ListedColormap from the dictionary
        cmap_name = 'labeled_integer_colormap'
        labeled_integer_colormap = ListedColormap([color_map_dict[val] for val in sorted(color_map_dict.keys())], name=cmap_name)
        # Display the array using imshow with the custom colormap
        plt.imshow(output['class_image'], cmap=labeled_integer_colormap, interpolation='none')
        plt.title(f'{output["method_name"]} Classmap Image')
        ax = plt.gca()
        ax.set_xticks([])
        ax.set_yticks([])
        # Create legend patches and labels
        patches = [mpatches.Patch(color=color_map_dict[val], label=output['class_names'][i])
                    for i, val in enumerate(output['class_indices'])]
        # Add the legend to the plot
        ax.legend(handles=patches, bbox_to_anchor=(1.05, 1.0), loc='upper left', borderaxespad=0.1, fontsize=8) 
        plt.tight_layout()
        plt.savefig(p, format='pdf')  
        plt.close()
        
        plot_class_spectra(data, output, results['Mask_image'], p)
        
    p.close()    
    
    


def plot_abundance_info(data, outputs, mask, p):
    print('plotting abundance info...')



def plot_class_spectra(data, outputs, mask, p):
    '''
        outputs = {
            'method_name': 'MF',
            'det_arr': MF_det_arr,
            'class_indices': mineral_indices,
            'library_indices': library_indices,
            'class_names': mineral_names,
            'class_image': class_image,
            'model_spectra': model_spectra
        }
        
    data = { 
            'imList': imList,
            'imList_fullWl': imList_fullWl,
            'wl': wl, 
            'nr': nr, 
            'nc': nc, 
            'nb': nb, 
            'nPix': nPix, 
            'spectra': spectra, 
            'spectra_fullWl': spectra_fullWl, 
            'names': names
        }
    '''
    method_name = outputs['method_name']
    det_arr = outputs['det_arr']
    class_image = outputs['class_image']
    mineral_names = outputs['class_names']
    library_indices = outputs['library_indices']
    nClasses = len(mineral_names)
    nPix = data['nPix']
    nr = data['nr']
    nc = data['nc']
    nb = data['nb']
    imList = data['imList']
    imList_fullWl = data['imList_fullWl']
    wl = data['wl']
    wl_fullWl = data['wl_fullWl']
    spectra = data['spectra']
    spectra_fullWl = data['spectra_fullWl']
    names = data['names']
    
    maskList = np.reshape(mask, (nPix))
    det_image_list = np.zeros((nPix,nClasses))
    print(f'det_image_list shape: {det_image_list.shape}')
    print(f'det_arr shape: {det_arr.shape}')
    print(f'mask shape: {mask.shape}')
    print(f'class_image shape: {class_image.shape}')
    try:
        for i in range(nClasses):
            if isinstance(library_indices[i], list):
                det_image_list[:,i] = np.max(det_arr[:,library_indices[i]], axis=1)
            else:
                det_image_list[:,i] = det_arr[:,library_indices[i]]
    except:
        print('Dimension mismatch.')
    det_image = np.reshape(det_image_list, (nr, nc, nClasses))
    
    # plot the abundance barchart and images
    if outputs['method_name'] == 'Unmixing':
        for i in range(1,nClasses):
            mineral_names[i] = mineral_names[i].split()[0]
        # create abundances, which are the coefficients normalized to sum to one
        abundances = (det_arr.T / np.sum(det_arr, axis=1) ).T # shape = nPix x nSpec, same as det_arr
        abundances = (abundances.T*maskList).T # set abundances to zero for mask pixels
         # class abundance is the sum of abundances for all spectra in the class, averaged over all non-mask pixels
         # it is the fraction of the image comprised of the given mineral               
        class_abundance = np.zeros((nClasses))
        for i in range(1,nClasses):
            if isinstance(library_indices[i], list):
                class_abundance[i] = np.sum(abundances[:,library_indices[i]])/np.sum(maskList)
            else:
                class_abundance[i] = np.sum(abundances[:,library_indices[i]])/np.sum(maskList)
        idx_sorted = np.argsort(-class_abundance)
        mineral_names = np.asarray(mineral_names)
        
        fig, ax = plt.subplots()
        plt.grid(True)
        y_pos = np.arange(1,nClasses)
        ax.barh(y_pos, class_abundance[idx_sorted[:-1]])
        ax.set_yticks(y_pos, labels=mineral_names[idx_sorted[:-1]])
        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_xlabel('% Abundance')
        ax.set_title('Mineral Abundances from Unmixing')
        plt.tight_layout()
        #plt.show()
        plt.savefig(p, format='pdf') 
        

    # Plot class image, detection image, and spectra for each class present
    for i in range(1,nClasses):
        plt.figure(figsize=(9,6))        
        ax1 = plt.subplot2grid((2, 3), (0, 0))
        ax2 = plt.subplot2grid((2, 3), (1, 0))
        ax3 = plt.subplot2grid((2, 3), (0, 1), colspan=2, rowspan=2)
        image_for_plot = np.squeeze(det_image[:,:,i])
        single_class_image = (class_image==i)*mask

        # Detection Imaeg
        ax1.set_title(f'{method_name} Detection Image')
        image_for_plot = image_for_plot - np.min(image_for_plot[mask==1])
        image_for_plot = image_for_plot*mask
        image_for_plot = image_for_plot/(np.max(image_for_plot)+0.000001)
        ax1.imshow(image_for_plot, interpolation=None)
        ax1.set_xticks([])
        ax1.set_yticks([])
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['left'].set_visible(False)

        # Class Location Image
        ax2.set_title(f'{method_name} Class Location')
        ax2.imshow(single_class_image, cmap='gray', interpolation=None)
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        
        # Pixel Spectrum with Library Spectra
        ax3.set_title(mineral_names[i]+'\n Image Class Mean (Black) and Library Spectra')
        mean_spectrum = np.mean(imList_fullWl[np.reshape(single_class_image, (nPix))==1], axis=0)
        if isinstance(library_indices[i], list):
            for j in library_indices[i]:
                spec = R2Normalize(spectra_fullWl[j,:], mean_spectrum)
                ax3.plot(wl_fullWl, spec, label=names[j], linewidth=0.5)
        else:
            j = library_indices[i]
            spec = R2Normalize(spectra_fullWl[j,:], mean_spectrum)
            ax3.plot(wl_fullWl, spec, label=names[j], linewidth=0.5)     
        if method_name == 'Unmixing':
            ax3.set_title(mineral_names[i]+'\n Image Class Mean (Black), Mixture Model (Blue) and Library Spectra')  
            model_spectra = outputs['model_spectra']     
            mean_model_spectrum = np.mean(model_spectra[np.reshape(single_class_image, (nPix))==1], axis=0)
            spec = R2Normalize(mean_model_spectrum, mean_spectrum)     
            ax3.plot(wl_fullWl, spec, label='Model', color='b', alpha=0.8) 
        ax3.plot(wl_fullWl, mean_spectrum, label='Mean Class Spectrum', color='k', alpha=0.8) 
        ax3.set_xlabel('Wavelength (nm)')           
        ax3.set_ylabel('Reflectance (scaled to pixel spectrum)')
        ax3.minorticks_on()
        ax3.grid(which='major', linewidth='0.75', color='black')
        ax3.grid(which='minor', linewidth='0.1', color='black', alpha=0.5)
        plt.tight_layout()
        
        plt.savefig(p, format='pdf') 
        plt.close()  
    
    
    
    
    
    
    
    

def add_metadata_to_bandnames(im_bma):
    net_abundance = np.sum(np.sum(im_bma.Arr, axis=0), axis=0)
    srt_abundance = np.argsort(-net_abundance)
    names = im_bma.metadata['band names']
    im_bma.bnames = []
    im_bma_idx = []
    for i in srt_abundance:
        im_bma.bnames.append(f"{net_abundance[i]:.1f} | "+names[i])
        im_bma_idx.append(i)
    im_bma.bnames = np.asarray(im_bma.bnames)
    im_bma.idx = np.asarray(im_bma_idx)
    return im_bma, im_bma_idx


def create_RGB(imArr, wl, stretch_pct=[2,98], method='SWIR'):
    
    # determine the indices for the red, green, and blue bands
    if method == 'SWIR':
        red_band_idx = np.argmin(np.abs(wl-1250))
        green_band_idx = np.argmin(np.abs(wl-1600))
        blue_band_idx = np.argmin(np.abs(wl-2200))
        imRGB_wavelengths =  [1250, 1600, 2200]
    elif np.min(wl)<550:
        red_band_idx = np.argmin(np.abs(wl-640))
        green_band_idx = np.argmin(np.abs(wl-550))
        blue_band_idx = np.argmin(np.abs(wl-460))
        imRGB_wavelengths =  [460, 550, 640]
    else:
        nb = len(wl)
        red_band_idx = int(nb*0.2)
        green_band_idx = int(nb*0.5)
        blue_band_idx = int(nb*0.8)   
        imRGB_wavelengths =  wl[[red_band_idx, green_band_idx, blue_band_idx]]
    
    # Create a numpy array for the RGB image with shape (nrows, ncold, 3)
    imRGB = imArr[:,:,[red_band_idx, green_band_idx, blue_band_idx]]
    
    # Clip the bands
    imRGB_clipped = imArr[:,:,[red_band_idx, green_band_idx, blue_band_idx]]
    for i in range(3):
        # Create a variable to hold a single band from the image. 
        # This is not the most computationally efficient method, but simplifies the code.
        single_band = imRGB_clipped[:,:,i]
        # Clip the band
        lower_thresh = np.percentile(single_band.flatten(), stretch_pct[0])
        single_band[single_band < lower_thresh] = lower_thresh
        upper_thresh = np.percentile(single_band.flatten(), stretch_pct[1])
        single_band[single_band > upper_thresh] = upper_thresh
        # Rescale to [0,1].
        single_band = single_band - lower_thresh
        single_band = single_band / np.max(single_band)
        # Put the values for this band back into the RGB image.
        imRGB_clipped[:,:,i] = single_band
    
    return imRGB_wavelengths, imRGB_clipped
    
    
def display_RGB(imArr, wl, stretch_pct=[2,98], rotate=False, clean_axis=True):
    
    # determine the indices for the red, green, and blue bands
    if np.min(wl)<550:
        red_band_idx = np.argmin(np.abs(wl-640))
        green_band_idx = np.argmin(np.abs(wl-550))
        blue_band_idx = np.argmin(np.abs(wl-460))
    else:
        nb = len(wl)
        red_band_idx = int(nb*0.2)
        green_band_idx = int(nb*0.5)
        blue_band_idx = int(nb*0.8)    
    
    # Create a numpy array for the RGB image with shape (nrows, ncold, 3)
    imRGB = imArr[:,:,[red_band_idx, green_band_idx, blue_band_idx]]
    
    # Clip the bands
    imRGB_clipped = imArr[:,:,[red_band_idx, green_band_idx, blue_band_idx]]
    for i in range(3):
        # Create a variable to hold a single band from the image. 
        # This is not the most computationally efficient method, but simplifies the code.
        single_band = imRGB_clipped[:,:,i]
        # Clip the band
        lower_thresh = np.percentile(single_band.flatten(), stretch_pct[0])
        single_band[single_band < lower_thresh] = lower_thresh
        upper_thresh = np.percentile(single_band.flatten(), stretch_pct[1])
        single_band[single_band > upper_thresh] = upper_thresh
        # Rescale to [0,1].
        single_band = single_band - lower_thresh
        single_band = single_band / np.max(single_band)
        # Put the values for this band back into the RGB image.
        imRGB_clipped[:,:,i] = single_band
    
    # Plot the clipped and rescaled image.
    plt.figure(figsize=(15,5)) 
    if rotate:
        plt.imshow(np.flip(np.rot90(imRGB_clipped), axis=0))
        plt.gca().invert_yaxis()  
    else:
        plt.imshow(imRGB_clipped)
    if clean_axis:
        plt.gca().set_xticks([])
        plt.gca().set_yticks([])
    else:
        plt.ylabel('Row');
        plt.xlabel('Column');


    
def display_PCA(imPCA, PCs = [0,1,2], stretch_pct=[2,98], rotate=False):
    
    # determine the indices for the red, green, and blue bands
    red_band_idx = PCs[0]
    green_band_idx = PCs[1]
    blue_band_idx = PCs[2]
    
    
    # Create a numpy array for the RGB image with shape (nrows, ncold, 3)
    imRGB = imPCA[:,:,[red_band_idx, green_band_idx, blue_band_idx]]
    
    # Clip the bands
    imRGB_clipped = imPCA[:,:,[red_band_idx, green_band_idx, blue_band_idx]]
    for i in range(3):
        # Create a variable to hold a single band from the image. 
        # This is not the most computationally efficient method, but simplifies the code.
        single_band = imRGB_clipped[:,:,i]
        # Clip the band
        lower_thresh = np.percentile(single_band.flatten(), stretch_pct[0])
        single_band[single_band < lower_thresh] = lower_thresh
        upper_thresh = np.percentile(single_band.flatten(), stretch_pct[1])
        single_band[single_band > upper_thresh] = upper_thresh
        # Rescale to [0,1].
        single_band = single_band - lower_thresh
        if np.max(single_band) > 0:
            single_band = single_band / np.max(single_band)
        # Put the values for this band back into the RGB image.
        imRGB_clipped[:,:,i] = single_band
    
    # Plot the clipped and rescaled image.
    plt.figure(figsize=(15,5)) 
    if rotate:
        plt.imshow(np.flip(np.rot90(imRGB_clipped), axis=0))
        plt.gca().invert_yaxis()  
        plt.xlabel('Row');
        plt.ylabel('Column');
    else:
        plt.imshow(imRGB_clipped)
        plt.ylabel('Row');
        plt.xlabel('Column');
        
        
class image_name_struc:
    def __init__(self, fname_im = '', fname_hdr = ''):
        self.im = fname_im
        self.hdr = fname_hdr
        
        
class image_struc:
    def __init__(self):
        # descriptive data
        self.fname = None
        self.full_path = None
        self.file_type = None
        self.description = None
        self.acquisition_data = None
        self.sensor_type = None
        self.map_info = None
        self.im = None
        # image info
        self.arr = None # the 3d image array, [rows, cols, bands]
        self.wl = None # 1-d numpy array of numbers 
        self.arrList = None # the image spectra in a list form [rows*cols, bands]
        self.nr = None # number of rows, self.arr.shape[0]
        self.nc = None # number of columns, self.arr.shape[1]
        self.nb = None # number of bands, self.arr.shape[2]
        self.nPix = None # number of pixels, = self.nr*self.nc
        self.bbl = None # numpy 1d boolean array of 0s and 1s, 0 => bad, 1 => good
        self.gb_indices = None # numpy array if integer indices for good bands, from np.where(self.im.bbl==1)[0]
        self.data_mask = None # numpy 2d array of 0s and 1s
        self.ground_sample_distance = None # [GSD in x-direction, GSD in y-direction,]
        self.GSD_units = None
        self.deaulft_stretch_type = None # text: 'linear' or 'pct stretch'
        self.deaulft_stretch_values = None # list with two numbers, [lower stretch value, upper stretch value]
        # for analysis output (such as anomaly detection, target detection, and classification)
        self.band_names = None
        # for classification images (1-band, 2d-image, with an integer values for each class)
        self.nClasses = None
        self.class_colors = None
        self.class_names = None
        # for spectral libraries
        self.nSpectra = None # number of spectra in the library, integer
        self.spectra_names = None # the name of the spectra, list of strings
        self.spectra_metadata = None # python dictionary, each key is the metadata name, with a value for each spectrum
        self.spectra = None # 2d numpy array [number of spectra, number of bands]
        # additional optional information from ENVI image metadata
        self.metadata = None

def load_image(fname):
    '''read a spectral image from a file and populate a image_struc:
        fname = a image_name_struc instance for a valid image
    returns: im
            im = image_name_structure instance'''
    
    # create an instance of image_name_structure
    im = image_struc() 
    # Open the image 
    im_read = spectral.envi.open(fname.hdr, fname.im)
    # load the data into an array
    im.Arr = im_read.load()
    # determine metadata
    im.wl = np.asarray(im_read.bands.centers)
    im.fwhm = np.asarray(im_read.bands.bandwidths)
    if 'bbl' in im_read.metadata.keys():
        # read bad bands list of metadata if present
        im.bbl = np.asarray((im.metadata['bbl']))
    else: 
        # creat bad bands list with no bad bands
        num_bands = len(im.wl)
        im.bbl = np.asarray(([1]*num_bands))        
    im.gb_indices = np.where(im.bbl==1)[0]
    # subset to only the good bands
    if True:
        # subset the data to just the good bands
        im.Arr  = im.Arr[:,:,im.gb_indices]
        im.wl = im.wl[im.gb_indices]
        im.fwhm = im.fwhm[im.gb_indices]
    # get the number of rows, columns, and bands
    if len(im.Arr.shape) > 2:
        im.nr, im.nc, im.nb = im.Arr.shape
    else:
        im.nr, im.nc = im.Arr.shape
        im.nb = 1
    # compute the number of pixels
    im.nPix = im.nr*im.nc
    # create a version of the image as a 2d array of shape nPix by nb
    # (it does not actually create new data in memory)
    im.ArrList = np.reshape(im.Arr, (im.nPix, im.nb))
    
    # common text information
    im.filename = os.path.basename(fname.im)
    im.full_fname_data = fname.im
    im.full_fname_header = fname.hdr        
    if 'description' in im_read.metadata.keys():
        im.description = im_read.metadata['description']
    if 'file type' in im_read.metadata.keys():
        im.file_type = im_read.metadata['file type']
    if 'sensor type' in im_read.metadata.keys():
        im.sensor_type = im_read.metadata['sensor type']
    if 'coordinate system string' in im_read.metadata.keys():
        im.coordinate_system_string = im_read.metadata['coordinate system string']
    if 'map info' in im_read.metadata.keys():
        im.map_info = im_read.metadata['map info']
    if 'acquisition_data' in im_read.metadata.keys():
        im.acquisition_data = im_read.metadata['acquisition_data']
    if 'wavelength units' in im_read.metadata.keys():
        im.wavelength_units = im_read.metadata['wavelength units']
    if 'spectir smoothing' in im_read.metadata.keys():
        im.spectir_smoothing = im_read.metadata['spectir smoothing']
    if 'savgolay version number' in im_read.metadata.keys():
        im.savgolay_version_number = im_read.metadata['savgolay version number']
    if 'data ignore value' in im_read.metadata.keys():
        im.data_ignore_value = im_read.metadata['data ignore value']
    if 'reflectance scale factor' in im_read.metadata.keys():
        im.reflectance_scale_factor = im_read.metadata['reflectance scale factor']
    if 'default bands' in im_read.metadata.keys():
        im.default_bands = im_read.metadata['default bands']
    if 'rpc info' in im_read.metadata.keys():
        im.rpc_info = im_read.metadata['rpc info']
    if 'sun azimuth' in im_read.metadata.keys():
        im.sun_azimuth = im_read.metadata['sun azimuth info']
    if 'sun elevation' in im_read.metadata.keys():
        im.sun_elevation = im_read.metadata['rpc sun elevation']
    if 'sensor azimuth' in im_read.metadata.keys():
        im.sensor_azimuth = im_read.metadata['sensor azimuth']
    if 'sensor elevation' in im_read.metadata.keys():
        im.sensor_elevation = im_read.metadata['sensor elevation']
    
    # store the full metadata from spectral.envi.read in native format
    im.im_from_envi_spectral_read = im_read
    
    return im


   
    


def display_labeled_integer_array_as_colored_image(image_array, integer_array, indices, names, min_abund, method=''):
    """
    Displays a 2D numpy array of integers as a colored image with a key
    mapping colors to names. 0 corresponds to black.

    Args:
        integer_array (np.ndarray): A 2D numpy array of integers.
        names (list of str): A list of strings where names[i] corresponds
                             to the i-th unique non-zero integer value found
                             in the array (in sorted order).
    """
    #unique_values = np.unique(integer_array)
    #non_zero_values = sorted([val for val in unique_values if val != 0])

    num_colors = len(indices)

    if num_colors > 0:
        plt.figure(figsize=(12,6))
        plt.title(f"{method} Classification Image with Key ({100*min_abund}% abundance threshold)")
        ax1 = plt.gca()
        ax1.set_xticks([])
        ax1.set_yticks([])
        # Remove spines for the first subplot
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['left'].set_visible(False)
        
        plt.subplot(1,2,1)
        plt.title("False Color Image")
        for i in range(3):
            band = image_array[:,:,i]
            image_array[:,:,i] -= np.min(image_array[:,:,i])
            image_array[:,:,i] /= 0.95*np.max(image_array[:,:,i])
            image_array[:,:,i] = np.clip(image_array[:,:,i], a_min=0, a_max=1)
        plt.imshow(image_array)
        plt.gca().set_xticks([])
        plt.gca().set_yticks([])
        plt.subplot(1,2,2)
        plt.title("method Classmap Image")
        
        if len(names) != num_colors:
            raise ValueError(f"The length of 'names' ({len(names)}) must match the number of unique non-zero integer values ({num_colors}).")

        # Generate a colormap with a unique color for each unique non-zero value
        colors = plt.cm.nipy_spectral(np.linspace(0, 1, num_colors+1))

        # Create a dictionary mapping integer values to colors
        color_map_dict = {0: [0, 0, 0, 1]}  # 0 is black (RGBA)
        for i, val in enumerate(indices[1:]):
            color_map_dict[val] = colors[i+1]

        # Create a ListedColormap from the dictionary
        cmap_name = 'labeled_integer_colormap'
        labeled_integer_colormap = ListedColormap([color_map_dict[val] for val in sorted(color_map_dict.keys())], name=cmap_name)

        # Display the array using imshow with the custom colormap
        plt.imshow(integer_array, cmap=labeled_integer_colormap, interpolation='none')
        plt.gca().set_xticks([])
        plt.gca().set_yticks([])

        # Create legend patches and labels
        patches = [mpatches.Patch(color=color_map_dict[val], label=names[i])
                   for i, val in enumerate(indices)]

        # Add the legend to the plot
        plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    else:
        # If only 0 is present, display as a black image
        plt.imshow(integer_array, cmap='gray', vmin=0, vmax=0, interpolation='nearest')
        plt.title("Image with only value 0 (Black)")

    plt.tight_layout()  # Adjust layout to prevent overlap with legend
    plt.show()


    def save_geotiffs(self, num=0):   
        
        # subset the indices for output if requested
        if num>0:
            indices = self.indices[:num]   
        else:
            indices = self.indices                     
          
        logger.info("Saving GeoTiff files.")
        # build the band data
        #for band_idx in range(self.coefficientsIm.shape[2]):
        for color_idx,band_idx in enumerate(indices):
            name = self.class_names[band_idx]
            prob = str(int(self.class_probs[band_idx]))
            output_tiff_fname = os.path.join(self.output_dir,prob+' abund_'+name+'.tiff')
            #abund = np.array(np.squeeze(self.coefficientsIm[:,:,band_idx]))
            abund = np.array(np.squeeze(self.probabilitiesIm[:,:,band_idx]))
            abund[np.where(abund<0)] = 0
            abund[np.where(abund>1)] = 1

            # save the geotiff of abundance 
            gdal.UseExceptions()
            im_gdal = gdal.Open(self.image_filename)
            self.write_single_geotiff(abund, im_gdal, output_tiff_fname, nbands=4, name=name,
                                    nodata=False, color_idx = color_idx, dtype=gdal.GDT_Byte)
        
        self.single_output_tiff_fname = output_tiff_fname
        
        
    def write_single_geotiff(self, array, gdal_obj, outputpath, nbands=4,name=None,
                             nodata=False, color_idx = 0, dtype=gdal.GDT_UInt16, options=0):
        """
        Description:
        Writes a geotiff from a Numpy array with appended georeferencing from parent geotiff.
        
        Parameters:
        array: numpy array to write as geotiff
        gdal_obj: object created by gdal.Open() using a tiff that has the SAME CRS, transformation, and resolution as the array you're writing
        outputpath: path including filename.tiff
        dtype (OPTIONAL): datatype to save as
        nodata (default: False): set to any value you want to use for nodata; if False, nodata is not set
        """

        gt = gdal_obj.GetGeoTransform()

        # Prepare color table
        r,g,b = self.get_cmap(color_idx)
        
        array = 0.1 + 0.8*array
        arrayA = (255*(array)).astype(np.uint8)
        arrayA[array == 0.1] = 0

        # Prepare destination file
        width = np.shape(arrayA)[1]
        height = np.shape(arrayA)[0]
        driver = gdal.GetDriverByName("GTiff")
        if options != 0:
            dest = driver.Create(outputpath, width, height, 4, dtype, options)
        else:
            dest = driver.Create(outputpath, width, height, 4, dtype)
        
        # Write output raster
        arrayR = np.zeros((arrayA.shape[0],arrayA.shape[1]), np.uint8) + r
        arrayG = np.zeros((arrayA.shape[0],arrayA.shape[1]), np.uint8) + g
        arrayB = np.zeros((arrayA.shape[0],arrayA.shape[1]), np.uint8) + b
        dest.GetRasterBand(1).WriteArray(arrayR)
        dest.GetRasterBand(2).WriteArray(arrayG)
        dest.GetRasterBand(3).WriteArray(arrayB)
        dest.GetRasterBand(4).WriteArray(arrayA)
        dest.GetRasterBand(1).SetRasterColorInterpretation(gdal.GCI_RedBand)
        dest.GetRasterBand(2).SetRasterColorInterpretation(gdal.GCI_GreenBand)
        dest.GetRasterBand(3).SetRasterColorInterpretation(gdal.GCI_BlueBand)
        dest.GetRasterBand(4).SetRasterColorInterpretation(gdal.GCI_AlphaBand)

        # Set transform and projection
        dest.SetGeoTransform(gt)
        wkt = gdal_obj.GetProjection()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(wkt)
        dest.SetProjection(srs.ExportToWkt())
        
        # Close output raster dataset 
        dest = None


def save_array_as_geotiff(fname_hdr: str,
                          fname_img: str,
                          result_array: np.ndarray,
                          out_tif: str) -> None:
    """
    Reads georeferencing info from an ENVI header + image pair,
    then writes `result_array` to `out_tif` as a GeoTIFF with matching
    CRS and affine transform.
    """
    # 1. Open the ENVI image and grab its metadata (including 'map info')
    img = envi.open(fname_hdr, fname_img)
    hdr = img.metadata
    map_info = hdr.get('map info')
    if map_info is None:
        raise ValueError("No 'map info' found in header")  # Spectral Python stores ENVI header fields in metadata dict :contentReference[oaicite:0]{index=0}

    # 2. Parse the map info string:
    #    Format: {projection, x_first_pix, y_first_pix, ulx, uly, x_size, y_size, datum, units}
    parts = map_info.strip('{}').split(',')
    ulx = float(parts[3])      # upper-left X coordinate :contentReference[oaicite:1]{index=1}
    uly = float(parts[4])      # upper-left Y coordinate :contentReference[oaicite:2]{index=2}
    xres = float(parts[5])     # pixel width :contentReference[oaicite:3]{index=3}
    yres = float(parts[6])     # pixel height :contentReference[oaicite:4]{index=4}

    # 3. Build an affine transform: west, north, xsize, ysize
    #    Note: rasterio.from_origin takes (west, north, xsize, ysize)
    transform = from_origin(ulx, uly, xres, yres) #:contentReference[oaicite:5]{index=5}

    # 4. Write the NumPy array to GeoTIFF
    #    - height/width come from array shape
    #    - count=1 for a single-band raster
    #    - dtype pulled from the NumPy array
    #    - crs is set to WGS84 (EPSG:4326) for Geographic Lat/Lon map info
    #      adjust CRS string if your header uses a different projection :contentReference[oaicite:6]{index=6}
    height, width = result_array.shape
    profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': result_array.dtype,
        'crs': 'EPSG:4326',      # WGS84 Geographic :contentReference[oaicite:7]{index=7}
        'transform': transform,
    }

    with rasterio.Env():     # initializes GDAL and rasterio drivers :contentReference[oaicite:8]{index=8}
        with rasterio.open(out_tif, 'w', **profile) as dst:
            dst.write(result_array, 1)  # write to band 1 :contentReference[oaicite:9]{index=9}


def lda_predict_proba(X, m1, m2, m3, cov, priors=None):
    """
    X     : [N, D] data matrix (1000, 50)
    m1,m2,m3 : class means (each is [50])
    cov   : shared covariance matrix [50, 50]
    priors: class prior probabilities (default = uniform)

    Returns:
        probs: [N, 3] matrix of class probabilities for each observation
    """
    means = np.stack([m1, m2, m3])  # [3, D]
    inv_cov = np.linalg.inv(cov)   # [D, D]

    # Default: uniform priors
    if priors is None:
        priors = np.array([1/3, 1/3, 1/3])

    # Compute the discriminant scores δ_k(x) for each class and observation
    # δ_k(x) = xᵀ Σ⁻¹ μ_k - 0.5 μ_kᵀ Σ⁻¹ μ_k + log(π_k)
    linear_terms = X @ inv_cov @ means.T                     # [N, 3]
    quad_terms = -0.5 * np.sum((means @ inv_cov) * means, axis=1)  # [3]
    log_priors = np.log(priors)                             # [3]
    scores = linear_terms + quad_terms + log_priors         # [N, 3]

    # Softmax to get probabilities
    scores -= np.max(scores, axis=1, keepdims=True)  # for numerical stability
    exp_scores = np.exp(scores)
    probs = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)  # [N, 3]

    return probs