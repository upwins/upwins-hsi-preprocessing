"""
Support code for the UPWINS hyperspectral preprocessing notebooks.

Trimmed to the one function the notebooks and the batch script actually use
(``spatial_smoothing``). The fuller research utilities — RGB/PCA display,
GeoTIFF export, PDF reporting, LDA helpers — live in
``research_UPWINS_Microscene`` and were dropped here as unused dead code.
"""
import copy
import numpy as np


def spatial_smoothing(arr, mask=None):
    '''
    Smooths the image by averaging each pixel spectrum with its neighbors.
    mask_sum is used to sum the number of nonzero neighbors (neighbors with data)
        for the averaging.

    No-data pixels (mask == 0) are held at 0: the mask is re-applied after the
    neighbor averaging so smoothing never bleeds a valid spectrum into a no-data
    pixel and grows the valid-data region.
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
    # Set the values of zero in the mask to 1 to avoid dividing by zero
    mask_sum[mask_sum==0] = 1
    for i in range(arr_out.shape[2]):
        # Divide by the neighbor count, then re-apply the mask. Without the
        # *mask, a no-data pixel (mask == 0) that borders valid data would get a
        # nonzero smoothed value, growing the valid region by one pixel per pass
        # and breaking the band0>0 no-data convention the notebooks rely on.
        arr_out[:,:,i] = arr_out[:,:,i]/mask_sum*mask
    return arr_out
