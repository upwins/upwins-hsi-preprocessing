"""
Support code for the UPWINS hyperspectral preprocessing notebooks.

Trimmed to what the notebooks and the batch script actually use
(``spatial_smoothing``, plus the ENVI path helpers below). The fuller research
utilities — RGB/PCA display, GeoTIFF export, PDF reporting, LDA helpers — were
dropped here as unused dead code; they remain in the history of the research
repo this one was cut from (``research_species_mapping``).
"""
import copy
import os

import numpy as np


# ENVI stores a cube as a data file plus a text header. The data file may carry
# one of these extensions or none at all, so a bare `os.path.splitext` is not
# safe here: it strips whatever follows the last dot, which eats part of a real
# name like `raw_8-21-2025.v2` or `scene.2025.03`. Match a known extension
# instead, and leave anything else alone.
ENVI_DATA_EXTENSIONS = ('.img', '.bin', '.dat', '.raw')


def envi_basename(image_path):
    """Strip a known ENVI data extension from ``image_path``, if it has one.

    ``raw_0_or`` -> ``raw_0_or``            (extensionless: unchanged)
    ``raw_1.img`` -> ``raw_1``
    ``raw_2.bin`` -> ``raw_2``
    ``raw_8-21-2025.v2`` -> ``raw_8-21-2025.v2``   (``.v2`` is part of the name)
    """
    root, ext = os.path.splitext(image_path)
    return root if ext.lower() in ENVI_DATA_EXTENSIONS else image_path


def reflectance_paths(image_path):
    """Return ``(hdr, img)`` for the reflectance product of a raw cube.

    Derived from the raw cube's *basename*, so a data extension is not carried
    into the middle of the product name: ``raw_36286.bin`` yields
    ``raw_36286_ref.hdr`` / ``raw_36286_ref.img``, not ``raw_36286.bin_ref.*``.

    This is the single definition of that name. Both the writers (notebook 02,
    the batch script) and the readers (notebook 02's viewer cell, notebook 03's
    default) go through it, so a reader can never derive a name the writer did
    not produce.
    """
    base = envi_basename(image_path) + '_ref'
    return base + '.hdr', base + '.img'


def find_envi_header(image_path):
    """Return the ENVI header that accompanies ``image_path``.

    Looks for both conventions -- ``<file>.hdr`` (appended to the full filename)
    and ``<base>.hdr`` (replacing the data extension) -- because both are in use
    here and in the wild. Prefers the appended form when both exist, since that
    is the one ENVI itself writes. Raises ``FileNotFoundError`` naming both
    candidates if neither is present, rather than letting `spectral` fail later
    on a path the caller never chose.
    """
    candidates = [image_path + '.hdr']
    stripped = envi_basename(image_path) + '.hdr'
    if stripped != candidates[0]:
        candidates.append(stripped)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(
        'No ENVI header found for ' + image_path + '. Looked for: '
        + ', '.join(candidates))


def same_cube(image_path, header_path):
    """True if a data file and an ENVI header name the same cube.

    Both header conventions in circulation are accepted, because this repo
    already produces both: the batch script opens ``<file>.hdr`` (appending to
    the full filename), while ``config.yaml``'s pairs are written ``<base>.hdr``
    (replacing the extension). For ``raw_36286.bin`` that means

        raw_36286.bin.hdr   ->  True     (batch script's convention)
        raw_36286.hdr       ->  True     (config pairs' convention)
        raw_99999.hdr       ->  False    (a genuine mismatch still fails)
    """
    data = envi_basename(image_path)
    header = envi_basename(os.path.splitext(header_path)[0])
    return data == header


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
    # Edge cases are handled by averaging with pixels mirror imaged back into the array.
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
    # average each pixel spectrum with the spectrum for the pixel diagonal down and to the right (plus one column, plus one row).
    # for the last row and column, average with previous row or column appropriately.
    arr_out[0:(nr-1), 0:(nc-1), :] = arr_out[0:(nr-1), 0:(nc-1), :] + arr[1:, 1:, :]
    mask_sum[0:(nr-1), 0:(nc-1)] = mask_sum[0:(nr-1), 0:(nc-1)] + mask[1:, 1:]
    # bottom-right corner, average with pixel one row up, one column left
    arr_out[(nr-1), (nc-1), :] = arr_out[(nr-1), (nc-1), :] + arr[(nr-2), (nc-1), :]
    mask_sum[(nr-1), (nc-1)] = mask_sum[(nr-1), (nc-1)] + mask[(nr-2), (nc-1)]
    # last row, average with pixels up one row, right one column
    arr_out[(nr-1), 0:(nc-1), :] = arr_out[(nr-1), 0:(nc-1), :] + arr[(nr-2), 1:, :]
    mask_sum[(nr-1), 0:(nc-1)] = mask_sum[(nr-1), 0:(nc-1)] + mask[(nr-2), 1:]
    # last column, average with left one column, down one row
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
