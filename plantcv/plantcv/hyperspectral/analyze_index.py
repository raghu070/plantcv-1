# Analyze reflectance signal data in an index

import os
import cv2
import numpy as np
import pandas as pd
from plantcv.plantcv import params
from plantcv.plantcv import outputs
from plantcv.plantcv import plot_image
from plantcv.plantcv import print_image
from plantcv.plantcv import fatal_error
from plotnine import ggplot, aes, geom_line, scale_x_continuous


def analyze_index(index_array, mask, histplot=False, bins=100):
    """This extracts the hyperspectral index statistics and writes the values  as observations out to
       the Outputs class.

    Inputs:
    index_array  = Instance of the Spectral_data class, usually the output from pcv.hyperspectral.extract_index
    mask         = Binary mask made from selected contours
    histplot     = if True plots histogram of intensity values
    bins         = optional, number of classes to divide spectrum into


    :param array: __main__.Spectral_data
    :param mask: numpy array
    :param histplot: bool
    :param bins: int
    """
    params.device += 1

    debug = params.debug
    params.debug = None

    if len(np.shape(mask)) > 2 or len(np.unique(mask)) > 2:
        fatal_error("Mask should be a binary image of 0 and nonzero values.")

    if len(np.shape(index_array.array_data)) > 2:
        fatal_error("index_array data should be a grayscale image.")

    # Mask data and collect statistics about pixels within the masked image
    masked_array = index_array.array_data[np.where(mask > 0)]
    index_mean = np.average(masked_array)
    index_median = np.median(masked_array)
    index_std = np.std(masked_array)

    # Calculate histogram
    maxval = round(np.amax(index_array.array_data[0]), 4)
    hist_nir = [float(l[0]) for l in cv2.calcHist([index_array.array_data.astype(np.float32)],
                                                  [0], mask, [bins], [-2, 2])]

    # Create list of bin labels
    bin_width = maxval / float(bins)
    b = 0
    bin_labels = [float(b)]
    plotting_labels = [float(b)]
    for i in range(bins - 1):
        b += bin_width
        bin_labels.append(b)
        plotting_labels.append(round(b, 2))

    # Make hist percentage for plotting
    pixels = cv2.countNonZero(mask)
    hist_percent = [(p / float(pixels)) * 100 for p in hist_nir]

    # Reset debug mode and make plot
    params.debug = debug

    if histplot is True:
        hist_x = hist_percent
        dataset = pd.DataFrame({'Index Reflectance': bin_labels,
                                'Proportion of pixels (%)': hist_x})
        fig_hist = (ggplot(data=dataset,
                           mapping=aes(x='Index Reflectance',
                                       y='Proportion of pixels (%)'))
                    + geom_line(color='red')
                    + scale_x_continuous(breaks=plotting_labels, labels=plotting_labels))

        analysis_image = fig_hist
        if params.debug == "print":
            fig_hist.save(os.path.join(params.debug_outdir, str(params.device) + index_array.array_type + '_hist.png'))
        elif params.debug == "plot":
            print(fig_hist)

    # Make sure variable names should be unique within a workflow
    outputs.add_observation(variable='mean_' + index_array.array_type,
                            trait='Average ' + index_array.array_type + ' reflectance',
                            method='plantcv.plantcv.hyperspectral.analyze_index', scale='reflectance', datatype=float,
                            value=float(index_mean), label='none')

    outputs.add_observation(variable='med_' + index_array.array_type,
                            trait='Median ' + index_array.array_type + ' reflectance',
                            method='plantcv.plantcv.hyperspectral.analyze_index', scale='reflectance', datatype=float,
                            value=float(index_median), label='none')

    outputs.add_observation(variable='std_' + index_array.array_type,
                            trait='Standard deviation ' + index_array.array_type + ' reflectance',
                            method='plantcv.plantcv.hyperspectral.analyze_index', scale='reflectance', datatype=float,
                            value=float(index_std), label='none')

    outputs.add_observation(variable='index_frequencies_' + index_array.array_type, trait='index frequencies',
                            method='plantcv.plantcv.analyze_nir_intensity', scale='frequency', datatype=list,
                            value=hist_percent, label=bin_labels)

    if params.debug == "plot":
        plot_image(masked_array)
    elif params.debug == "print":
        img_name = str(params.device) + index_array.array_type + ".png"
        print_image(img=masked_array, filename=os.path.join(params.debug_outdir, img_name))
