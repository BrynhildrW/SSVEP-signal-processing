# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 20:06:59 2019
Use benchmark dataset to complete my research
@author: Brynhildr
"""
#%% Import third part module
import numpy as np
from numpy import transpose
import scipy.io as io
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import seaborn as sns

import os

import mne
from mne.filter import filter_data
from sklearn.linear_model import LinearRegression

import signal_processing_function as SPF 

#%% prevent ticking 'F5'
???

#%%*************************Part I: processing data*************************
#%% Load benchmark dataset & relative information
# load data from .mat file
eeg = io.loadmat(r'E:\dataset\data\S01.mat')
info = io.loadmat(r'E:\dataset\Freq_Phase.mat')

data = eeg['data']
# (64, 1500, 40, 6) = (n_chans, n_times, n_events, n_blocks)
# total trials = n_conditions x n_blocks = 240
# all epochs are down-sampled to 250 Hz, HOLLY SHIT!

# reshape data array: (n_events, n_epochs, n_chans, n_times)
data = data.transpose((2, 3, 0, 1))  

# combine data array: np.concatenate(X, Y, axis=)

# condition infomation
sfreq = 250
freqs = info['freqs'].T
phases = info['phases'].T

# load channels information from .txt file
channels = {}
file = open(r'E:\dataset\64-channels.txt')
for line in file.readlines():
    line = line.strip()
    v = line.split(' ')[0]
    k = line.split(' ')[1]
    channels[k] = v
file.close()

del v, k, file, line       # release RAM
del eeg, info     

#%% Load multiple data file & also can be used to process multiple data
# CAUTION: may lead to RAM crash (5-D array takes more than 6125MB)
# Now I know why people need 32G's RAM...PLEASE SKIP THIS PART!!!
filepath = r'E:\dataset\data'

filelist = []
for file in os.listdir(filepath):
    full_path = os.path.join(filepath, file)
    filelist.append(full_path)

i = 0
eeg = np.zeros((35, 64, 1500, 40, 6))
for file in filelist:
    temp = io.loadmat(file)
    eeg[i,:,:,:,:] = temp['data']
    i += 1
    
# add more codes here to achieve multiple data processing (PLEASE DON'T)
    
del temp, i, file, filelist, filepath, full_path

#%% Data preprocessing
# filtering
f_data = np.zeros((40,6,64,1500))
for i in range(data.shape[0]):
    f_data[i,:,:,:] = filter_data(data[i,:,:,:], sfreq=sfreq, l_freq=5,
                      h_freq=20, n_jobs=6)

del data, i

# get data for linear regression
w1 = f_data[:,:,:,0:125]
w2 = f_data[:,:,:,0:63]
w3 = f_data[:,:,:,63:125]
w4 = f_data[:,:,:,1250:]

# get data for comparision
signal_data = f_data[:,:,:,125:1375]

del f_data

# save model data to release RAM, reload before use
w1_path = r'E:\dataset\model_data\S01\w1'
w2_path = r'E:\dataset\model_data\S01\w2'
w3_path = r'E:\dataset\model_data\S01\w3'
s_path = r'E:\dataset\signal_data\S01'

io.savemat(w1_path, {'w1':w1})
io.savemat(w2_path, {'w2':w2})
io.savemat(w3_path, {'w3':w3})
io.savemat(s_path, {'signal_data':signal_data})

del w1, w2, w3, signal_data
del w1_path, w2_path, w3_path, s_path

#%% Reload data 
# data size: (n_events, n_epochs, n_chans, n_times) 
w1 = io.loadmat(r'E:\dataset\model_data\S01\w1.mat')
w1 = w1['w1']
w2 = io.loadmat(r'E:\dataset\model_data\S01\w2.mat')
w2 = w2['w2']
w3 = io.loadmat(r'E:\dataset\model_data\S01\w3.mat')
w3 = w3['w3']
signal_data = io.loadmat(r'E:\dataset\signal_data\S01.mat')
signal_data = signal_data['signal_data']

#%% Divide input&output data for model

# pick input channels: P1, P3, P5, P7, PZ
# choose output channels: PO4

# w1 model data: 0-500ms
w1_i = w1[:,:,43:48,:]
w1_o = w1[:,:,56,:]

# w2 model data: 0-250ms
w2_i = w2[:,:,43:48,:]
w2_o = w2[:,:,56,:]

# w3 model data: 250-500ms
w3_i = w3[:,:,43:48,:]
w3_o = w3[:,:,56,:]

# signal part data: 500ms-1250ms
sig_i = signal_data[:,:,43:48,:]
sig_o = signal_data[:,:,56,:]

#%% Inter-channel correlation analysis: canonical correlation analysis (CCA)

#%% Inter-channel correlation analysis: Spearman correlation
w1_corr_sp = SPF.corr_coef(w1, 'spearman')
w2_corr_sp = SPF.corr_coef(w2, 'spearman')
w3_corr_sp = SPF.corr_coef(w3, 'spearman')

# may need to compute in different parts
sig_corr_sp = SPF.corr_coef(signal_data, mode='spearman')

#%% Binarization
def bina_corr(X,Y):
    '''
    Compare two correlation array and do binarization
    :param X&Y: two input array (n_chans, n_chans)
    '''
    compare = X-Y
    for i in range(X.shape[0]):
        for j in range(X.shape[0]):
            if compare[i,j] > 0.05:
                compare[i,j] = 1
            else:
                compare[i,j] = 0
    
    return compare

compare_corr = bina_corr(w1_corr_sp, sig_corr_sp)

#%% Inter-channel correlation analysis: Pearson correlation
w1_corr_sp = SPF.corr_coef(w1, mode='pearson')
w2_corr_sp = SPF.corr_coef(w2, mode='pearson')
w3_corr_sp = SPF.corr_coef(w3, mode='pearson')

# may need to compute in different parts
sig_corr_sp = SPF.corr_coef(signal_data[:,:,?,:], mode='pearson')

#%% Spatial filter: multi-linear regression method
# regression coefficient, intercept, R^2
rc_w1, ri_w1, r2_w1 = SPF.mlr_analysis(w1_i, w1_o)
# w1 estimate & extract data: (n_events, n_epochs, n_times)
w1_mes_w1, w1_mex_w1 = SPF.sig_extract(rc_w1, w1_i, w1_o, ri_w1, mode='b')

# the same but w2 part data:
rc_w2, ri_w2, r2_w2 = SPF.mlr_analysis(w2_i, w2_o, w2_i, 0,  mode='a')
w2_mes_w2, w2_mex_w2 = SPF.sig_extract(rc_w2, w2_i, w2_o, ri_w2, mode='b')

# the same but w3 part data (use w2)
w2_mes_w3, w2_mex_w3 = SPF.sig_extract(rc_w2, w3_i, w3_o, ri_w2, mode='b')

# the same but w3 part data (use w3)
rc_w3, ri_w3, r2_w3 = SPF.mlr_analysis(w3_i, w3_o, w3_i, 0, mode='a')
w3_mes_w3, w3_mex_w3 = SPF.sig_extract(rc_w3, w3_i, w3_o, ri_w3, mode='b')

# signal part data (use w1):
s_mes_w1, s_mex_w1 = SPF.sig_extract(rc_w1, sig_i, sig_o, ri_w1, mode='b')
# signal part data (use w2):
s_mes_w2, s_mex_w2 = SPF.sig_extract(rc_w2, sig_i, sig_o, ri_w2, mode='b')
# signal part data (use w3): 
s_mes_w3, s_mex_w3 = SPF.sig_extract(rc_w3, sig_i, sig_o, ri_w3, mode='b')

#%% Spatial filter: inverse array method
# filter coefficient
sp_w1 = SPF.inv_spa(w1_i, w1_o)
# w1 estimate & extract data: (n_events, n_epochs, n_times)
w1_ies_w1, w1_iex_w1 = SPF.sig_extract(sp_w1, w1_i, w1_o, 0, mode='a')

# the same but w2 part data:
sp_w2 = SPF.inv_spa(w2_i, w2_o)
w2_ies_w2, w2_iex_w2 = SPF.sig_extract(sp_w2, w2_i, w2_o, 0, mode='a')

# the same but w3 part data (use w2):
w2_ies_w3, w2_iex_w3 = SPF.sig_extract(sp_w2, w3_i, w3_o, 0, mode='a')

# the same but w3 part data (use w3):
sp_w3 = SPF.inv_spa(w3_i, w3_o)
w3_ies_w3, w3_iex_w3 = SPF.sig_extract(sp_w3, w3_i, w3_o, 0, mode='a')

# signal part data (use w1):
s_ies_w1, s_iex_w1 = SPF.sig_extract(sp_w1, sig_i, sig_o, 0, mode='a')
# signal part data (use w2):
s_ies_w2, s_iex_w2 = SPF.sig_extract(sp_w2, sig_i, sig_o, 0, mode='a')
# signal part data (use w3):
s_ies_w3, s_iex_w3 = SPF.sig_extract(sp_w3, sig_i, sig_o, 0, mode='a')

#%% Cosine similarity (background part): normal
# w1 estimate (w1 model) & w1 original, mlr, normal similarity, the same below
w1_w1_m_nsim = SPF.cos_sim(w1_o, w1_mes_w1, mode='normal')
w2_w2_m_nsim = SPF.cos_sim(w2_o, w2_mes_w2, mode='normal')
w2_w3_m_nsim = SPF.cos_sim(w3_o, w2_mes_w3, mode='normal')
w3_w3_m_nsim = SPF.cos_sim(w3_o, w3_mes_w3, mode='normal')

w1_w1_i_nsim = SPF.cos_sim(w1_o, w1_ies_w1, mode='normal')
w2_w2_i_nsim = SPF.cos_sim(w2_o, w2_ies_w2, mode='normal')
w2_w3_i_nsim = SPF.cos_sim(w3_o, w2_ies_w3, mode='normal')
w3_w3_i_nsim = SPF.cos_sim(w3_o, w3_ies_w3, mode='normal')

#%% Cosine similarity (background part): Tanimoto (generalized Jaccard)
# w1 estimate (w1 model) & w1 original, mlr, Tanimoto, the same below
#w1_w1_m_tsim = SPF.cos_sim(w1_o, w1_mes_w1, mode='normal')
#w2_w2_m_tsim = SPF.cos_sim(w2_o, w2_mes_w2, mode='normal')
#w2_w3_m_tsim = SPF.cos_sim(w3_o, w2_mes_w3, mode='normal')
#w3_w3_m_tsim = SPF.cos_sim(w3_o, w3_mes_w3, mode='normal')

w1_w1_i_tsim = SPF.cos_sim(w1_o, w1_ies_w1, mode='normal')
w2_w2_i_tsim = SPF.cos_sim(w2_o, w2_ies_w2, mode='normal')
w2_w3_i_tsim = SPF.cos_sim(w3_o, w2_ies_w3, mode='normal')
w3_w3_i_tsim = SPF.cos_sim(w3_o, w3_ies_w3, mode='normal')

#%% Power spectrum density
w1_p, f = SPF.welch_p(s_iex_w1, 250, 0, 30, 1250, 0, 1250)
w2_p, f = SPF.welch_p(s_iex_w2, 250, 0, 30, 1250, 0, 1250)
w3_p, f = SPF.welch_p(s_iex_w3, 250, 0, 30, 1250, 0, 1250)
sig_p, f = SPF.welch_p(sig_o, 250, 0, 30, 1250, 0, 1250)

#%% Precise FFT transform

#%% Variance
# original signal variance
var_o_t = var_estimation(sig_o)

# extract signal variance (w1 model) 
var_w1_m_t = var_estimation(w1_mex_w1)
var_w1_i_t = var_estimation(w1_iex_w1)

# extract signal variance (w2 model) 
var_w2_m_t = var_estimation(w2_mex_w2)
var_w2_i_t = var_estimation(w2_iex_w2)

# extract signal variance (w3 model) 
var_w3_m_t = var_estimation(w3_mex_w3)
var_w3_i_t = var_estimation(w3_iex_w3)

#%% SNR in time domain
# original signal snr
snr_o_t = SPF.snr_time(sig_o, mode='time')

# extract signal snr (w1 model) 
#snr_w1_m_t = snr_time(s_mex_w1, mode='time')
snr_w1_i_t = SPF.snr_time(s_iex_w1, mode='time')

# extract signal snr (w2 model) 
#snr_w2_m_t = snr_time(s_mex_w2, mode='time')
snr_w2_i_t = SPF.snr_time(s_iex_w2, mode='time')

# extract signal snr (w3 model) 
#snr_w3_m_t = snr_time(s_mex_w3, mode='time')
snr_w3_i_t = SPF.snr_time(s_iex_w3, mode='time')

#%% SNR in frequency domain


#%%*************************Part II: plot figures*************************
#%% Model descrpition (Comoplex)
fig = plt.figure(figsize=(20,12))
gs = GridSpec(3, 5, figure=fig)

# 1. Boxplot of R^2 

# 2. Histogram of R^2
# 3. Inter-channel correlation (2 parts)
# 4. Waveform in time domain
X = 
Y = 

compare_corr = X - Y

vmin = min(np.min(X), np.min(Y))
vmax = max(np.max(X), np.max(Y))

inter_chan = cm.get_cmap('Blues', 6)

fig, axes = plt.subplots(1, 3, figsize=(24,6))
fig.subtitle(r'$\ Inter-channel\ correlation$', fontsize=26, fontweight='bold')

mesh = axes[0].pcolormesh(X, cmap=inter_chan, vmin=vmin, vmax=vmax)
axes[0].set_title(r'$\ rest\ part$', fontsize=20)
axes[0].set_xlabel(r'$\ channels$', fontsize=20)
axes[0].set_ylabel(r'$\ channels$', fontsize=20)
axes[0].tick_params(axis='both', labelsize=20)
fig.colorbar(mesh, ax=axes[0])

mesh = axes[1].pcolormesh(Y, cmap=inter_chan, vmin=vmin, vmax=vmax)
axes[1].set_title(r'$\ signal\ part$', fontsize=20)
fig.colorbar(mesh, ax=axes[1])

mesh = axes[2].pcolormesh(compare_corr, cmap=inter_chan,
           vmin=np.min(compare_corr), vmax=np.max(compare_corr))
fig.colorbar(mesh, ax=axes[2])

plt.show()

#%%
fig, axes = plt.subplots(2,1, figsize=(16,16))

axes[0].set_title('signal', fontsize=20)
axes[0].set_xlabel('time/ms', fontsize=20)
axes[0].set_ylabel('SNR', fontsize=20)
axes[0].plot(np.mean(sig_o[7,:,:], axis=0), label='origin:125-1375')
axes[0].plot(np.mean(s_iex_w1[7,:,:], axis=0), label='w1:0-125')
axes[0].plot(np.mean(s_iex_w2[7,:,:], axis=0), label='w2:0-63')
axes[0].plot(np.mean(s_iex_w3[7,:,:], axis=0), label='w3:63-125')
axes[0].tick_params(axis='both', labelsize=20)
axes[0].legend(loc='upper right', fontsize=20)

axes[1].set_title('time snr', fontsize=20)
axes[1].set_xlabel('time/ms', fontsize=20)
axes[1].set_ylabel('SNR', fontsize=20)
axes[1].plot(snr_o_t[7,:], label='origin:125-1375')
axes[1].plot(snr_w1_i_t[7,:], label='w1:0-125')
axes[1].plot(snr_w2_i_t[7,:], label='w2:0-63')
axes[1].plot(snr_w3_i_t[7,:], label='w3:63-125')
axes[1].tick_params(axis='both', labelsize=20)
axes[1].legend(loc='best', fontsize=20)

#%%
plt.title('signal psd', fontsize=20)
plt.xlabel('frequency/Hz', fontsize=20)
plt.plot(f[1,1,:], np.mean(sig_p[7,:,:], axis=0), label='origin:125-1375')
plt.plot(f[1,1,:], np.mean(w1_p[7,:,:], axis=0), label='w1:0-125')
plt.plot(f[1,1,:], np.mean(w2_p[7,:,:], axis=0), label='w2:0-63')
plt.plot(f[1,1,:], np.mean(w3_p[7,:,:], axis=0), label='w3:63-125')
plt.legend(loc='best', fontsize=20)

#%%
def strain(X):
    strain = np.zeros((40,50))
    
    for i in range(40):
        k=0
        for j in range(50):
            strain[i,j] = np.mean(X[i,k:k+25])
            k += 25
    return strain

#%%
snr1 = strain(snr_o_t)
snr2 = strain(snr_w1_i_t)
snr3 = strain(snr_w2_i_t)
snr4 = strain(snr_w3_i_t)

#%%
plt.plot(snr1[7,:], label='origin:125-1375')
plt.plot(snr2[7,:], label='w1:0-125')
plt.plot(snr3[7,:], label='w2:0-63')
plt.plot(snr4[7,:], label='w3:63-125')
plt.tick_params(axis='both', labelsize=20)
plt.legend(loc='best', fontsize=20)