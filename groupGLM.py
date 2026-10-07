#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 23:19:21 2025

@author: in65
"""


# Import common libraries
import os
import matplotlib as mpl

# Import Plotting Library
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Import StatsModels
import statsmodels.formula.api as smf

# Import MNE processing
from mne.preprocessing.nirs import beer_lambert_law, optical_density



from mne_nirs.channels import get_long_channels, get_short_channels, picks_pair_to_idx
from mne_nirs.experimental_design import make_first_level_design_matrix

# Import MNE-NIRS processing
from mne_nirs.statistics import run_glm, statsmodels_to_results
from mne_nirs.visualisation import plot_glm_group_topo, plot_glm_surface_projection

from mne.io import read_raw_fif
import csv

############################ !!!!!! ##############################
root = '/Users/in65/Desktop/GroupGLM/'
############################ !!!!!! ##############################

#subject files
subjFiles = [f for f in os.listdir(root) if f.endswith('.fif') and \
        os.path.isfile(os.path.join(root, f))]

# subj = [os.path.splitext(f)[0] for f in os.listdir(root) 
#              if f.endswith('.fif') and os.path.isfile(os.path.join(root, f))]
print(subjFiles)

def individual_analysis(subjPath):
    dataPath = root + subjPath
    ID = os.path.splitext(subjPath)[0]
    raw_intensity = read_raw_fif(dataPath)
    
    # Convert signal to haemoglobin and resample
    raw_od = optical_density(raw_intensity)
    raw_haemo = beer_lambert_law(raw_od, ppf=0.1)
    raw_haemo.resample(0.6)

    # Cut out just the short channels for creating a GLM repressor
    sht_chans = get_short_channels(raw_haemo)
    raw_haemo = get_long_channels(raw_haemo)

    # Create a design matrix
    design_matrix = make_first_level_design_matrix(raw_haemo, stim_dur=30.0)

    # Append short channels mean to design matrix
    design_matrix["ShortHbO"] = np.mean(
        sht_chans.copy().pick(picks="hbo").get_data(), axis=0
    )
    design_matrix["ShortHbR"] = np.mean(
        sht_chans.copy().pick(picks="hbr").get_data(), axis=0
    )

    # Run GLM
    glm_est = run_glm(raw_haemo, design_matrix)

    ############################ !!!!!! ##############################
    # Define channels in each region of interest
    # List the optode pairs manually
    leftPFC = [[1, 1 ], [1, 2], [3, 1], [3, 2], [2, 1]]
    rightPFC = [[1, 17 ], [9, 17], [9, 2], [10, 17], [10, 19]]
    brocaPO = [[5, 5], [5, 3], [5, 4]]
    brocaPT = [[7, 4], [7, 5], [3, 4], [4, 4]]
    wernickeSG = [[27, 9], [26, 9], [27, 9]]
    wernickeAG = [[30, 9], [30, 12], [28, 9]]
    v1_2_3 = [[31, 13], [31, 16], [22, 28], [22, 16], [23, 16],
              [31, 14], [31, 18], [23, 15], [23, 30], [22, 30], [22, 29],
              [32, 14], [32, 15], [24, 29], [24, 30]]    
    ############################ !!!!!! ##############################    

    # Then generate the correct indices for each pair
    groups = dict(
        Left_PFC=picks_pair_to_idx(raw_haemo, leftPFC, on_missing='ignore'),
        BrocasPO=picks_pair_to_idx(raw_haemo, brocaPO, on_missing='ignore'),
        BrocasPT=picks_pair_to_idx(raw_haemo, brocaPT, on_missing='ignore'),
        WernickesSG=picks_pair_to_idx(raw_haemo, wernickeSG, on_missing='ignore'),
        WernickesAG=picks_pair_to_idx(raw_haemo, wernickeAG, on_missing='ignore'),
        Visual_Cortex=picks_pair_to_idx(raw_haemo, v1_2_3, on_missing='ignore'))


    # Extract channel metrics
    cha = glm_est.to_dataframe()

    # Compute region of interest results from channel data
    roi = glm_est.to_dataframe_region_of_interest(
        groups, design_matrix.columns, demographic_info=True
    )

    # Define left vs right tapping contrast
    contrast_matrix = np.eye(design_matrix.shape[1])
    basic_conts = dict(
        [(column, contrast_matrix[i]) for i, column in enumerate(design_matrix.columns)]
    )
    contrast_EvS = basic_conts['eng'] - basic_conts['span']
    contrast_EvD = basic_conts['eng'] - basic_conts['dis']
    contrast_SvD = basic_conts['span'] - basic_conts['dis']
    contrast_EvR = basic_conts['eng'] - basic_conts['rest']
    contrast_SvR = basic_conts['span'] - basic_conts['rest']
    contrast_DvR = basic_conts['dis'] - basic_conts['rest']

    # Compute defined contrast
    contrastEngSpan = glm_est.compute_contrast(contrast_EvS)
    conE_S = contrastEngSpan.to_dataframe()
    
    contrastEngDis = glm_est.compute_contrast(contrast_EvD)
    conE_D = contrastEngDis.to_dataframe()
  
    contrastSpanDis = glm_est.compute_contrast(contrast_SvD)
    conS_D = contrastSpanDis.to_dataframe()
    
    contrastEngRest = glm_est.compute_contrast(contrast_EvR)
    conE_R = contrastEngRest.to_dataframe()
      
    contrastSpanRest = glm_est.compute_contrast(contrast_SvR)
    conS_R = contrastSpanRest.to_dataframe()
      
    contrastDisRest = glm_est.compute_contrast(contrast_DvR)
    conD_R = contrastDisRest.to_dataframe()
    
    ############################################################################

    # Add the participant ID to the dataframes
    roi["ID"] = cha["ID"] = conE_S["ID"] = conE_D["ID"] = conS_D["ID"] \
         = conE_R["ID"] = conS_R["ID"] = conD_R["ID"] = ID

    #########################################################################
    # Convert to uM for nicer plotting below.
    cha["theta"] = [t * 1.0e6 for t in cha["theta"]]
    roi["theta"] = [t * 1.0e6 for t in roi["theta"]]
    conE_S["effect"] = [t * 1.e6 for t in conE_S["effect"]]
    conE_D["effect"] = [t * 1.e6 for t in conE_D["effect"]]
    conS_D["effect"] = [t * 1.e6 for t in conS_D["effect"]]
    conE_R["effect"] = [t * 1.e6 for t in conE_R["effect"]]
    conS_R["effect"] = [t * 1.e6 for t in conS_R["effect"]]
    conD_R["effect"] = [t * 1.e6 for t in conD_R["effect"]]

    return raw_haemo, roi, cha, conE_S, conE_D, conS_D, conE_R, conS_R, conD_R

    ############################################################################



#make your data frames
df_roi = pd.DataFrame()  # To store region of interest results
df_cha = pd.DataFrame()  # To store channel level results
df_conEngSpan = pd.DataFrame()  # To store channel level contrast results
df_conEngDis = pd.DataFrame()
df_conSpanDis = pd.DataFrame()  # To store channel level contrast results
df_conEngRest = pd.DataFrame()
df_conSpanRest = pd.DataFrame()
df_conDisRest = pd.DataFrame()

for i in range(len(subjFiles)):
    subj = subjFiles[i]
    raw_haemo, roi, cha, conE_S, conE_D, conS_D, conE_R, conS_R, \
        conD_R = individual_analysis(subj)

    df_roi = pd.concat([df_roi, roi], ignore_index=True)
    df_cha = pd.concat([df_cha, cha], ignore_index=True)
    df_conEngSpan = pd.concat([df_conEngSpan, conE_S], ignore_index=True)
    df_conEngDis = pd.concat([df_conEngDis, conE_D], ignore_index=True)
    df_conSpanDis = pd.concat([df_conSpanDis, conS_D], ignore_index=True)
    df_conEngRest = pd.concat([df_conEngRest, conE_R], ignore_index=True)
    df_conSpanRest = pd.concat([df_conSpanRest, conS_R], ignore_index=True)
    df_conDisRest = pd.concat([df_conDisRest, conD_R], ignore_index=True)
    

#compute group level results
grp_results = df_roi.query("Condition in ['rest', 'eng', 'span', 'dis']")

roi_model = smf.mixedlm("theta ~ -1 + ROI:Condition:Chroma",
                        grp_results, groups=grp_results["ID"]).fit(method='nm')
roi_model.summary()


# linear mixed model
grp_results = df_roi.query("Condition in ['rest', 'eng', 'span', 'dis']")
# grp_results = grp_results.query("Chroma in ['hbo']")

roi_model = smf.mixedlm(
    "theta ~ Condition", grp_results, groups=grp_results["ID"]
).fit(method="nm")
roi_model.summary()

# scatter plot
grp_results = df_roi.query("Condition in ['rest', 'eng', 'span', 'dis']")
roi_model = smf.mixedlm(
    "theta ~ -1 + ROI:Condition:Chroma", grp_results, groups=grp_results["ID"]
).fit(method="nm")

df = statsmodels_to_results(roi_model)

sns.catplot(
    x="Condition",
    y="Coef.",
    hue="ROI",
    data=df.query("Chroma == 'hbo'"),
    errorbar=None,
    palette="muted",
    height=4,
    s=10,
)

# visualize conditions
fig, axes = plt.subplots(
    nrows=2, ncols=2, figsize=(10, 10), gridspec_kw=dict(width_ratios=[1, 1])
)

# Cut down the dataframe just to the conditions we are interested in
ch_summary = df_cha.query("Condition in ['rest', 'eng', 'span', 'dis']")
ch_summary = ch_summary.query("Chroma in ['hbo']")

# Run group level model and convert to dataframe
ch_model = smf.mixedlm(
    "theta ~ -1 + ch_name:Chroma:Condition", ch_summary, groups=ch_summary["ID"]
).fit(method="nm")
ch_model_df = statsmodels_to_results(ch_model)


# HBO
# Plot the two conditions
plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbo"),
    ch_model_df.query("Condition in ['rest']"),
    colorbar=False,
    axes=axes[0, 0],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbo"),
    ch_model_df.query("Condition in ['eng']"),
    colorbar=True,
    axes=axes[0, 1],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbo"),
    ch_model_df.query("Condition in ['span']"),
    colorbar=False,
    axes=axes[1, 0],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbo"),
    ch_model_df.query("Condition in ['dis']"),
    colorbar=True,
    axes=axes[1, 1],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

# REMOVE CHANNEL LABELS
for ax in axes.ravel():
    for txt in ax.texts:
        label = txt.get_text()
        if label.startswith("S") and "_D" in label:
            txt.set_visible(False)
            
# Cut down the dataframe just to the conditions we are interested in
ch_summary = df_cha.query("Condition in ['rest', 'eng', 'span', 'dis']")
ch_summary = ch_summary.query("Chroma in ['hbr']")

# Run group level model and convert to dataframe
ch_model = smf.mixedlm(
    "theta ~ -1 + ch_name:Chroma:Condition", ch_summary, groups=ch_summary["ID"]
).fit(method="nm")
ch_model_df = statsmodels_to_results(ch_model)


# HBR
# Plot the two conditions
plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbr"),
    ch_model_df.query("Condition in ['rest']"),
    colorbar=False,
    axes=axes[0, 0],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbr"),
    ch_model_df.query("Condition in ['eng']"),
    colorbar=True,
    axes=axes[0, 1],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbr"),
    ch_model_df.query("Condition in ['span']"),
    colorbar=False,
    axes=axes[1, 0],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

plot_glm_group_topo(
    raw_haemo.copy().pick(picks="hbr"),
    ch_model_df.query("Condition in ['dis']"),
    colorbar=True,
    axes=axes[1, 1],
    vlim=(0, 20),
    cmap=mpl.cm.Oranges,
)

# REMOVE CHANNEL LABELS
for ax in axes.ravel():
    for txt in ax.texts:
        label = txt.get_text()
        if label.startswith("S") and "_D" in label:
            txt.set_visible(False)




#contrast: Eng/Span
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6, 6))
con_summary = df_conEngSpan.query("Chroma in ['hbo']")

# Run group level model and convert to dataframe
con_model = smf.mixedlm("effect ~ -1 + ch_name:Chroma",
                        con_summary, groups=con_summary["ID"]).fit(method='nm')
con_model_df = statsmodels_to_results(con_model,
                                      order=raw_haemo.copy().pick(
                                          picks="hbo").ch_names)

plot_glm_group_topo(raw_haemo.copy().pick(picks="hbo"),
                    con_model_df, colorbar=True, axes=axes)




#contrast: Eng/Dis
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6, 6))
con_summary = df_conEngDis.query("Chroma in ['hbo']")

# Run group level model and convert to dataframe
con_model = smf.mixedlm("effect ~ -1 + ch_name:Chroma",
                        con_summary, groups=con_summary["ID"]).fit(method='nm')
con_model_df = statsmodels_to_results(con_model,
                                      order=raw_haemo.copy().pick(
                                          picks="hbo").ch_names)

plot_glm_group_topo(raw_haemo.copy().pick(picks="hbo"),
                    con_model_df, colorbar=True, axes=axes)


# # Generate brain figure from data
# clim = dict(kind="value", pos_lims=(0, 8, 11))
# brain = plot_glm_surface_projection(
#     raw_haemo.copy().pick("hbo"),
#     con_model_df,
#     clim=clim,
#     view="dorsal",
#     colorbar=True,
#     size=(800, 700),
# )
# brain.add_text(0.05, 0.95, "Rest-Eng-Span-Dist", "title", font_size=16, color="k")

# # Run model code as above
# clim = dict(kind="value", pos_lims=(0, 11.5, 17))
# for idx, cond in enumerate(["rest", "eng", "span", "dist"]):
#     # Run same model as explained in the sections above
#     ch_summary = df_cha.query("Condition in [@cond]")
#     ch_summary = ch_summary.query("Chroma in ['hbo']")
#     ch_model = smf.mixedlm(
#         "theta ~ -1 + ch_name", ch_summary, groups=ch_summary["ID"]
#     ).fit(method="nm")
#     model_df = statsmodels_to_results(
#         ch_model, order=raw_haemo.copy().pick("hbo").ch_names
#     )

#     # Generate brain figure from data
#     brain = plot_glm_surface_projection(
#         raw_haemo.copy().pick("hbo"),
#         model_df,
#         clim=clim,
#         view="dorsal",
#         colorbar=True,
#         size=(800, 700),
#     )
#     brain.add_text(0.05, 0.95, cond, "title", font_size=16, color="k")





##table of channel level results
ch_summary = df_cha.query("Condition in ['rest', 'eng', 'span', 'dis']")
ch_summary = ch_summary.query("Chroma in ['hbo']")

# Run group level model and convert to dataframe
ch_model = smf.mixedlm("theta ~ -1 + ch_name:Chroma:Condition",
                       ch_summary, groups=ch_summary["ID"]).fit(method='nm')

# Here we can use the order argument to ensure the channel name order
ch_model_df = statsmodels_to_results(ch_model,
                                     order=raw_haemo.copy().pick(
                                         picks="hbo").ch_names)
# And make the table prettier
ch_model_df.reset_index(drop=True, inplace=True)
ch_model_df = ch_model_df.set_index(['ch_name', 'Condition'])
ch_model_df



# data = ["apple", "banana", "cherry"]
# with open("output.csv", "w", newline='') as f:
#     writer = csv.writer(f)
#     writer.writerow(data)