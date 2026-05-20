import numpy as np
# OpenDA version 3.4.0.-1 February 27 2026
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochObserver/timeSeriesFormatter.xml
# Starting Algorithm: 
# 	className: org.openda.algorithms.kalmanFilter.SequentialEnsembleSimulation
# 	dir.: ././algorithms
# 	config.: SequentialEnsembleSimulation.xml
# configstring = SequentialEnsembleSimulation.xml
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././algorithms/SequentialEnsembleSimulation.xml
# analysisTimes@type=fromObservationTimes
# mainModel@stochParameter=false
# mainModel@stochForcing=false
# mainModel@stochInit=false
# this.ensembleSize=5
# ensembleModel@stochParameter=false
# ensembleModel@stochForcing=false
# ensembleModel@stochInit=false
# saveGain/times@type=none
# Creating mainModel
# Create new BBModelInstance with number: 0
# Instance initialization done
#    Do not add noise to forcing
# model time 16071.0 16099.0
# analysisTimes acquired from OBSERVER:16073.0 -- 16099.0
# Creating ensemble model 0
# Create new BBModelInstance with number: 1
# Instance initialization done
# Creating ensemble model 1
# Create new BBModelInstance with number: 2
# Instance initialization done
# Creating ensemble model 2
# Create new BBModelInstance with number: 3
# Instance initialization done
# Creating ensemble model 3
# Create new BBModelInstance with number: 4
# Instance initialization done
# Creating ensemble model 4
# Create new BBModelInstance with number: 5
# Instance initialization done
# Application initializing finished
# Initializing Algorithm
# Algorithm initialized
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211180000UTC  to 190211200000UTC  (16071.0-->16073.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
xi_f_0=[]
#  state: temperature.state
xi_f_0.append([8.0452, 8.0761, 8.0832, 8.0749, 7.6216, 7.168, 6.658])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
xi_f_1=[]
#  state: temperature.state
xi_f_1.append([8.021, 8.0447, 8.0517, 8.0474, 7.6268, 7.1686, 6.658])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
xi_f_2=[]
#  state: temperature.state
xi_f_2.append([8.3809, 8.252, 8.1627, 8.0906, 7.6184, 7.1648, 6.6579])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
xi_f_3=[]
#  state: temperature.state
xi_f_3.append([8.1423, 8.1657, 8.1514, 8.0839, 7.6186, 7.1667, 6.6579])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
xi_f_4=[]
#  state: temperature.state
xi_f_4.append([8.0334, 8.0609, 8.0686, 8.0655, 7.6214, 7.1681, 6.658])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
x_f_central=[]
#  state: temperature.state
x_f_central.append([8.0682, 8.091, 8.0979, 8.0789, 7.6202, 7.1676, 6.658])
# ========================================================================
# 
#  analysis at 190211200000UTC (16073.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time=[]
analysis_time.append(16073.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
pred_f_central=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([8.0682, 8.091, 8.0979])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs=[]
obs.append([7.940208,7.916181,7.897431])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
pred_f_0=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([8.0452, 8.0761, 8.0832])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
pred_f_1=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([8.021, 8.0447, 8.0517])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
pred_f_2=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([8.3809, 8.252, 8.1627])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
pred_f_3=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([8.1423, 8.1657, 8.1514])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
pred_f_4=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([8.0334, 8.0609, 8.0686])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
x_f=[]
#  state: temperature.state
x_f.append([8.12456, 8.11988, 8.103520000000001, 8.07246, 7.62136, 7.16724, 6.65796])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
std_x_f=[]
#  state: temperature.state
std_x_f.append([0.15112720800702972, 0.0874678912515901, 0.05028018496386013, 0.01689920116455226, 0.003392344322146634, 0.0015339491516997387, 5.477225575087544E-5])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
pred_f=[]
#  predictions: T_0m, T_10m, T_20m
pred_f.append([8.12456, 8.11988, 8.103520000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
pred_f_std=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.15112720800702972, 0.0874678912515901, 0.05028018496386013])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
x_a=[]
#  state: temperature.state
x_a.append([8.12456, 8.11988, 8.103520000000001, 8.07246, 7.62136, 7.16724, 6.65796])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
pred_a_central=[]
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([8.0682, 8.091, 8.0979])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
x_a_central=[]
#  state: temperature.state
x_a_central.append([8.12456, 8.11988, 8.103520000000001, 8.07246, 7.62136, 7.16724, 6.65796])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211200000UTC  to 190211210000UTC  (16073.0-->16074.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.9953, 8.0529, 8.0514, 8.0289, 7.6271, 7.1794, 6.6583])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.9586, 7.9964, 8.0061, 7.9933, 7.6375, 7.1807, 6.6584])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([8.13, 8.1901, 8.1661, 8.0703, 7.6235, 7.175, 6.6582])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([8.1005, 8.1371, 8.1314, 8.0648, 7.6228, 7.1773, 6.6583])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.9228, 7.9569, 7.969, 7.9754, 7.6295, 7.1803, 6.6584])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.9856, 8.0259, 8.0378, 8.0389, 7.6256, 7.1788, 6.6583])
# ========================================================================
# 
#  analysis at 190211210000UTC (16074.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16074.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.9856, 8.0259, 8.0378])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.866181,7.861181,7.850764])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.9953, 8.0529, 8.0514])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.9586, 7.9964, 8.0061])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([8.13, 8.1901, 8.1661])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([8.1005, 8.1371, 8.1314])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.9228, 7.9569, 7.969])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([8.02144, 8.066679999999998, 8.0648, 8.02654, 7.628080000000001, 7.17854, 6.658320000000001])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.08999690550235645, 0.09665956755541558, 0.08291583081655743, 0.042144192957037474, 0.00592806882551151, 0.002375499947379563, 8.366600265363719E-5])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([8.02144, 8.066679999999998, 8.0648])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.08999690550235645, 0.09665956755541558, 0.08291583081655743])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([8.02144, 8.066679999999998, 8.0648, 8.02654, 7.628080000000001, 7.17854, 6.658320000000001])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.9856, 8.0259, 8.0378])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([8.02144, 8.066679999999998, 8.0648, 8.02654, 7.628080000000001, 7.17854, 6.658320000000001])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211210000UTC  to 190211220000UTC  (16074.0-->16075.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.9426, 7.9896, 7.998, 7.983, 7.6325, 7.191, 6.6587])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.8946, 7.9207, 7.9304, 7.9351, 7.6483, 7.193, 6.6588])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([8.068, 8.0939, 8.1025, 8.0617, 7.6264, 7.1856, 6.6585])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.9796, 8.0187, 8.0331, 8.0377, 7.6247, 7.1879, 6.6586])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.8377, 7.8659, 7.8763, 7.8821, 7.6314, 7.1933, 6.6588])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.9202, 7.9482, 7.9579, 7.9627, 7.6319, 7.1899, 6.6587])
# ========================================================================
# 
#  analysis at 190211220000UTC (16075.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16075.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.9202, 7.9482, 7.9579])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.803889,7.805556,7.795208])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.9426, 7.9896, 7.998])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.8946, 7.9207, 7.9304])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([8.068, 8.0939, 8.1025])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.9796, 8.0187, 8.0331])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.8377, 7.8659, 7.8763])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.9445, 7.977760000000001, 7.988060000000001, 7.97992, 7.6326600000000004, 7.1901600000000006, 6.65868])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.08715520638493139, 0.08813806215251163, 0.08808928992789058, 0.07350776829696272, 0.009337719207600898, 0.0033366150512157016, 1.3038404810415783E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.9445, 7.977760000000001, 7.988060000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.08715520638493139, 0.08813806215251163, 0.08808928992789058])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.9445, 7.977760000000001, 7.988060000000001, 7.97992, 7.6326600000000004, 7.1901600000000006, 6.65868])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.9202, 7.9482, 7.9579])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.9445, 7.977760000000001, 7.988060000000001, 7.97992, 7.6326600000000004, 7.1901600000000006, 6.65868])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211220000UTC  to 190211230000UTC  (16075.0-->16076.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([8.0275, 8.0119, 7.9703, 7.9583, 7.6352, 7.2015, 6.6591])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.8284, 7.855, 7.8622, 7.8662, 7.6508, 7.2056, 6.6591])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([8.0057, 8.0254, 8.032, 8.0293, 7.6283, 7.1961, 6.6589])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.9523, 7.9738, 7.9802, 7.98, 7.6258, 7.1985, 6.659])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.8609, 7.877, 7.8522, 7.85, 7.6278, 7.2055, 6.6592])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.8752, 7.8967, 7.9034, 7.9068, 7.6357, 7.2007, 6.659])
# ========================================================================
# 
#  analysis at 190211230000UTC (16076.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16076.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.8752, 7.8967, 7.9034])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.758264,7.764236,7.755139])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([8.0275, 8.0119, 7.9703])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.8284, 7.855, 7.8622])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([8.0057, 8.0254, 8.032])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.9523, 7.9738, 7.9802])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.8609, 7.877, 7.8522])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.93496, 7.94862, 7.93938, 7.93676, 7.633580000000001, 7.20144, 6.65906])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.08761905043995827, 0.07814679775908917, 0.07867319746902385, 0.07649073800140765, 0.01025875236078944, 0.00421165050781727, 1.1401754250992071E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.93496, 7.94862, 7.93938])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.08761905043995827, 0.07814679775908917, 0.07867319746902385])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.93496, 7.94862, 7.93938, 7.93676, 7.633580000000001, 7.20144, 6.65906])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.8752, 7.8967, 7.9034])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.93496, 7.94862, 7.93938, 7.93676, 7.633580000000001, 7.20144, 6.65906])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211230000UTC  to 190211240000UTC  (16076.0-->16077.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.967, 7.9938, 7.9742, 7.9414, 7.6317, 7.212, 6.6594])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.7822, 7.805, 7.812, 7.8157, 7.6483, 7.2185, 6.6595])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.9484, 7.9685, 7.975, 7.9763, 7.6307, 7.2061, 6.6592])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.916, 7.9361, 7.9428, 7.9453, 7.6261, 7.2083, 6.6593])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.799, 7.8289, 7.8352, 7.8374, 7.6176, 7.2169, 6.6596])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.8296, 7.8498, 7.8564, 7.8596, 7.6365, 7.211, 6.6594])
# ========================================================================
# 
#  analysis at 190211240000UTC (16077.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16077.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.8296, 7.8498, 7.8564])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.807917,7.750764,7.72375])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.967, 7.9938, 7.9742])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.7822, 7.805, 7.812])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.9484, 7.9685, 7.975])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.916, 7.9361, 7.9428])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.799, 7.8289, 7.8352])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.8825199999999995, 7.90646, 7.90784, 7.903220000000001, 7.630880000000001, 7.21236, 6.6594])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.08607794142519912, 0.08465437377950423, 0.07841905380709432, 0.07169579485576555, 0.011217932073247562, 0.0053411609224959244, 1.5811388300847177E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.8825199999999995, 7.90646, 7.90784])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.08607794142519912, 0.08465437377950423, 0.07841905380709432])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.8825199999999995, 7.90646, 7.90784, 7.903220000000001, 7.630880000000001, 7.21236, 6.6594])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.8296, 7.8498, 7.8564])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.8825199999999995, 7.90646, 7.90784, 7.903220000000001, 7.630880000000001, 7.21236, 6.6594])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211240000UTC  to 190211250000UTC  (16077.0-->16078.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.9611, 7.9898, 7.9652, 7.9275, 7.626, 7.2215, 6.6597])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.7016, 7.7401, 7.7506, 7.7562, 7.6466, 7.2311, 6.6599])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.9328, 7.9681, 7.952, 7.937, 7.6356, 7.2152, 6.6596])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.8743, 7.9112, 7.9115, 7.9049, 7.6246, 7.2173, 6.6597])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.7597, 7.7852, 7.7952, 7.7987, 7.6102, 7.227, 6.66])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.7793, 7.8107, 7.8199, 7.8242, 7.6371, 7.2208, 6.6597])
# ========================================================================
# 
#  analysis at 190211250000UTC (16078.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16078.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.7793, 7.8107, 7.8199])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.70875,7.700972,7.688056])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.9611, 7.9898, 7.9652])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.7016, 7.7401, 7.7506])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.9328, 7.9681, 7.952])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.8743, 7.9112, 7.9115])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.7597, 7.7852, 7.7952])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.8459, 7.878880000000001, 7.8749, 7.864859999999999, 7.6286000000000005, 7.22242, 6.659780000000001])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.11167154964448212, 0.11106739845697293, 0.09648917037678362, 0.08202940326492698, 0.013549169716259517, 0.006623971618296584, 1.6431676725162634E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.8459, 7.878880000000001, 7.8749])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.11167154964448212, 0.11106739845697293, 0.09648917037678362])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.8459, 7.878880000000001, 7.8749, 7.864859999999999, 7.6286000000000005, 7.22242, 6.659780000000001])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.7793, 7.8107, 7.8199])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.8459, 7.878880000000001, 7.8749, 7.864859999999999, 7.6286000000000005, 7.22242, 6.659780000000001])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211250000UTC  to 190211260000UTC  (16078.0-->16079.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.8904, 7.9066, 7.9126, 7.9132, 7.6204, 7.2305, 6.6601])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.6986, 7.7237, 7.7207, 7.7185, 7.6344, 7.2436, 6.6603])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.8959, 7.9213, 7.9267, 7.9159, 7.639, 7.2241, 6.6599])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.9087, 7.9187, 7.8892, 7.8811, 7.6232, 7.2254, 6.66])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.7578, 7.7743, 7.7673, 7.765, 7.6055, 7.2354, 6.6604])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.75, 7.7676, 7.7736, 7.7768, 7.6391, 7.2302, 6.6601])
# ========================================================================
# 
#  analysis at 190211260000UTC (16079.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16079.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.75, 7.7676, 7.7736])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.719167,7.699931,7.682986])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.8904, 7.9066, 7.9126])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.6986, 7.7237, 7.7207])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.8959, 7.9213, 7.9267])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.9087, 7.9187, 7.8892])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.7578, 7.7743, 7.7673])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.830279999999999, 7.8489200000000015, 7.843300000000001, 7.8387400000000005, 7.624500000000001, 7.2318, 6.66014])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.09573801230441335, 0.09311724867069467, 0.09310158430445767, 0.09108728231756621, 0.013112589370524869, 0.007970884518044452, 2.0736441353324365E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.830279999999999, 7.8489200000000015, 7.843300000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.09573801230441335, 0.09311724867069467, 0.09310158430445767])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.830279999999999, 7.8489200000000015, 7.843300000000001, 7.8387400000000005, 7.624500000000001, 7.2318, 6.66014])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.75, 7.7676, 7.7736])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.830279999999999, 7.8489200000000015, 7.843300000000001, 7.8387400000000005, 7.624500000000001, 7.2318, 6.66014])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211260000UTC  to 190211270000UTC  (16079.0-->16080.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.9562, 7.921, 7.8992, 7.8866, 7.6152, 7.238, 6.6604])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.6535, 7.6772, 7.6838, 7.6871, 7.6144, 7.2593, 6.6607])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.9404, 7.9616, 7.9133, 7.8991, 7.6382, 7.2323, 6.6602])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.8808, 7.8994, 7.8939, 7.8706, 7.6199, 7.2328, 6.6603])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.7743, 7.7941, 7.7616, 7.7563, 7.5954, 7.2424, 6.6607])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.719, 7.7409, 7.7469, 7.7498, 7.6283, 7.2392, 6.6604])
# ========================================================================
# 
#  analysis at 190211270000UTC (16080.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16080.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.719, 7.7409, 7.7469])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.656597,7.661458,7.64875])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.9562, 7.921, 7.8992])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.6535, 7.6772, 7.6838])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.9404, 7.9616, 7.9133])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.8808, 7.8994, 7.8939])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.7743, 7.7941, 7.7616])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.841040000000001, 7.8506599999999995, 7.830360000000001, 7.81994, 7.616620000000001, 7.24096, 6.6604600000000005])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.12682721711052397, 0.11501998956703129, 0.10230236067657501, 0.093505096117805, 0.01527815433879392, 0.011054094264117428, 2.3021728866460397E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.841040000000001, 7.8506599999999995, 7.830360000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.12682721711052397, 0.11501998956703129, 0.10230236067657501])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.841040000000001, 7.8506599999999995, 7.830360000000001, 7.81994, 7.616620000000001, 7.24096, 6.6604600000000005])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.719, 7.7409, 7.7469])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.841040000000001, 7.8506599999999995, 7.830360000000001, 7.81994, 7.616620000000001, 7.24096, 6.6604600000000005])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211270000UTC  to 190211280000UTC  (16080.0-->16081.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.8157, 7.8452, 7.8527, 7.8545, 7.6202, 7.2458, 6.6608])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.8449, 7.7443, 7.6742, 7.6563, 7.5971, 7.2759, 6.661])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.8487, 7.8769, 7.8854, 7.8829, 7.6375, 7.2411, 6.6606])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.8494, 7.8705, 7.8646, 7.8488, 7.6193, 7.2403, 6.6607])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.7279, 7.7545, 7.751, 7.7371, 7.5991, 7.2494, 6.6611])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.6694, 7.6923, 7.6996, 7.7033, 7.6342, 7.2487, 6.6607])
# ========================================================================
# 
#  analysis at 190211280000UTC (16081.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16081.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.6694, 7.6923, 7.6996])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.642639,7.615694,7.603889])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.8157, 7.8452, 7.8527])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.8449, 7.7443, 7.6742])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.8487, 7.8769, 7.8854])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.8494, 7.8705, 7.8646])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.7279, 7.7545, 7.751])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.81732, 7.818280000000001, 7.805579999999999, 7.79592, 7.6146400000000005, 7.2505, 6.660839999999999])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.05189664729055243, 0.06408753388920496, 0.08988126612370335, 0.09584749344662077, 0.01676567922871005, 0.014670207905820456, 2.0736441353332933E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.81732, 7.818280000000001, 7.805579999999999])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.05189664729055243, 0.06408753388920496, 0.08988126612370335])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.81732, 7.818280000000001, 7.805579999999999, 7.79592, 7.6146400000000005, 7.2505, 6.660839999999999])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.6694, 7.6923, 7.6996])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.81732, 7.818280000000001, 7.805579999999999, 7.79592, 7.6146400000000005, 7.2505, 6.660839999999999])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211280000UTC  to 190211290000UTC  (16081.0-->16082.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.826, 7.8565, 7.8263, 7.816, 7.6424, 7.2527, 6.6612])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.6819, 7.733, 7.6817, 7.653, 7.5749, 7.2988, 6.6614])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.7951, 7.8389, 7.8485, 7.8399, 7.6615, 7.2496, 6.6609])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.8445, 7.8719, 7.843, 7.8306, 7.6208, 7.247, 6.661])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.6981, 7.7377, 7.7271, 7.717, 7.5975, 7.256, 6.6615])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.593, 7.6396, 7.6519, 7.6579, 7.609, 7.2666, 6.6611])
# ========================================================================
# 
#  analysis at 190211290000UTC (16082.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16082.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.593, 7.6396, 7.6519])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.560833,7.541458,7.532431])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.826, 7.8565, 7.8263])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.6819, 7.733, 7.6817])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.7951, 7.8389, 7.8485])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.8445, 7.8719, 7.843])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.6981, 7.7377, 7.7271])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.76912, 7.8076, 7.785319999999999, 7.771300000000001, 7.61942, 7.260820000000002, 6.6612])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.07457145566501966, 0.06700104476797354, 0.07603408446216717, 0.08240740258010819, 0.03450807151957346, 0.021497255638801886, 2.5495097567991603E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.76912, 7.8076, 7.785319999999999])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.07457145566501966, 0.06700104476797354, 0.07603408446216717])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.76912, 7.8076, 7.785319999999999, 7.771300000000001, 7.61942, 7.260820000000002, 6.6612])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.593, 7.6396, 7.6519])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.76912, 7.8076, 7.785319999999999, 7.771300000000001, 7.61942, 7.260820000000002, 6.6612])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211290000UTC  to 190211300000UTC  (16082.0-->16083.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.9199, 7.9319, 7.8137, 7.8021, 7.6296, 7.2603, 6.6615])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.6013, 7.643, 7.6539, 7.6518, 7.5588, 7.3051, 6.6619])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.692, 7.7337, 7.7475, 7.7561, 7.6554, 7.2595, 6.6613])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.7411, 7.781, 7.7938, 7.8005, 7.618, 7.2537, 6.6614])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.5777, 7.6329, 7.6488, 7.657, 7.5878, 7.2637, 6.662])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.5426, 7.582, 7.595, 7.6029, 7.5789, 7.2886, 6.6615])
# ========================================================================
# 
#  analysis at 190211300000UTC (16083.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16083.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.5426, 7.582, 7.595])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.529722,7.489861,7.477847])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.9199, 7.9319, 7.8137])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.6013, 7.643, 7.6539])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.692, 7.7337, 7.7475])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.7411, 7.781, 7.7938])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.5777, 7.6329, 7.6488])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.7063999999999995, 7.7444999999999995, 7.73154, 7.733500000000001, 7.609920000000002, 7.268460000000001, 6.661620000000001])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.13656811487312845, 0.12178306532519194, 0.07706356467228859, 0.07455343721117111, 0.03749522636283205, 0.020795864973595223, 3.1144823004792155E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.7063999999999995, 7.7444999999999995, 7.73154])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.13656811487312845, 0.12178306532519194, 0.07706356467228859])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.7063999999999995, 7.7444999999999995, 7.73154, 7.733500000000001, 7.609920000000002, 7.268460000000001, 6.661620000000001])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.5426, 7.582, 7.595])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.7063999999999995, 7.7444999999999995, 7.73154, 7.733500000000001, 7.609920000000002, 7.268460000000001, 6.661620000000001])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211300000UTC  to 190212010000UTC  (16083.0-->16084.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.7726, 7.804, 7.8135, 7.7931, 7.6172, 7.2693, 6.6619])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.4842, 7.5291, 7.5437, 7.5533, 7.5474, 7.3119, 6.6623])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.718, 7.7474, 7.7042, 7.7003, 7.6382, 7.2724, 6.6616])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.669, 7.7102, 7.723, 7.7307, 7.6313, 7.2605, 6.6617])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.4885, 7.528, 7.5429, 7.5528, 7.5517, 7.2802, 6.6624])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.4813, 7.5199, 7.5338, 7.5432, 7.5356, 7.3112, 6.6618])
# ========================================================================
# 
#  analysis at 190212010000UTC (16084.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16084.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.4813, 7.5199, 7.5338])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.459375,7.418056,7.402847])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.7726, 7.804, 7.8135])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.4842, 7.5291, 7.5437])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.718, 7.7474, 7.7042])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.669, 7.7102, 7.723])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.4885, 7.528, 7.5429])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.626460000000001, 7.663740000000001, 7.66546, 7.66604, 7.59716, 7.278860000000001, 6.66198])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.13305731096035245, 0.127851155645931, 0.11892637638471958, 0.10843490213026413, 0.04414207743185655, 0.0197715199213411, 3.56370593624151E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.626460000000001, 7.663740000000001, 7.66546])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.13305731096035245, 0.127851155645931, 0.11892637638471958])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.626460000000001, 7.663740000000001, 7.66546, 7.66604, 7.59716, 7.278860000000001, 6.66198])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.4813, 7.5199, 7.5338])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.626460000000001, 7.663740000000001, 7.66546, 7.66604, 7.59716, 7.278860000000001, 6.66198])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212010000UTC  to 190212020000UTC  (16084.0-->16085.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.7825, 7.8124, 7.7743, 7.7672, 7.6068, 7.2768, 6.6622])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.3763, 7.4238, 7.4389, 7.4495, 7.4552, 7.3396, 6.6628])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.5983, 7.6337, 7.6469, 7.6551, 7.6129, 7.2911, 6.662])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.5885, 7.627, 7.6404, 7.6486, 7.6108, 7.2693, 6.6621])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.3866, 7.4324, 7.4474, 7.4576, 7.4629, 7.3089, 6.6629])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.4258, 7.4639, 7.4775, 7.4864, 7.4903, 7.3156, 6.6622])
# ========================================================================
# 
#  analysis at 190212020000UTC (16085.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16085.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.4258, 7.4639, 7.4775])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.397639,7.359236,7.344236])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.7825, 7.8124, 7.7743])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.3763, 7.4238, 7.4389])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.5983, 7.6337, 7.6469])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.5885, 7.627, 7.6404])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.3866, 7.4324, 7.4474])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.5464400000000005, 7.58586, 7.58958, 7.595600000000001, 7.549720000000001, 7.297140000000001, 6.6624])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.16932164067241975, 0.16210718059358137, 0.14396991699657252, 0.13800817004800842, 0.0828437505186722, 0.0281354402844526, 4.1833001326691205E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.5464400000000005, 7.58586, 7.58958])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.16932164067241975, 0.16210718059358137, 0.14396991699657252])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.5464400000000005, 7.58586, 7.58958, 7.595600000000001, 7.549720000000001, 7.297140000000001, 6.6624])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.4258, 7.4639, 7.4775])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.5464400000000005, 7.58586, 7.58958, 7.595600000000001, 7.549720000000001, 7.297140000000001, 6.6624])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212020000UTC  to 190212030000UTC  (16085.0-->16086.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.6654, 7.7105, 7.7231, 7.7296, 7.5986, 7.283, 6.6626])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.2814, 7.3347, 7.35, 7.3607, 7.3671, 7.3306, 6.6633])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.5692, 7.6073, 7.6163, 7.6113, 7.5812, 7.3008, 6.6624])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.6359, 7.6644, 7.6077, 7.604, 7.5736, 7.2789, 6.6625])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.3397, 7.3769, 7.3903, 7.3991, 7.4035, 7.3152, 6.6634])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.3731, 7.4113, 7.4245, 7.4331, 7.4369, 7.3254, 6.6626])
# ========================================================================
# 
#  analysis at 190212030000UTC (16086.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16086.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.3731, 7.4113, 7.4245])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.359722,7.318125,7.303194])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.6654, 7.7105, 7.7231])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.2814, 7.3347, 7.35])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.5692, 7.6073, 7.6163])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.6359, 7.6644, 7.6077])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.3397, 7.3769, 7.3903])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.49832, 7.538760000000001, 7.5374799999999995, 7.540939999999999, 7.5048, 7.3017, 6.662840000000002])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1761267640081998, 0.17162234120300301, 0.16000697484797347, 0.1558242054367678, 0.11021776172650219, 0.02172441023365164, 4.722287581247129E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.49832, 7.538760000000001, 7.5374799999999995])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1761267640081998, 0.17162234120300301, 0.16000697484797347])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.49832, 7.538760000000001, 7.5374799999999995, 7.540939999999999, 7.5048, 7.3017, 6.662840000000002])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.3731, 7.4113, 7.4245])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.49832, 7.538760000000001, 7.5374799999999995, 7.540939999999999, 7.5048, 7.3017, 6.662840000000002])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212030000UTC  to 190212040000UTC  (16086.0-->16087.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.5899, 7.6229, 7.6348, 7.6423, 7.5994, 7.2877, 6.663])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.2135, 7.2688, 7.2832, 7.294, 7.3008, 7.2888, 6.6639])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.5239, 7.5673, 7.5782, 7.5782, 7.5504, 7.321, 6.6628])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.5444, 7.5827, 7.5931, 7.5962, 7.5528, 7.2894, 6.6629])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.36, 7.3923, 7.3676, 7.3658, 7.3644, 7.3003, 6.6639])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.3288, 7.3667, 7.3789, 7.3869, 7.3907, 7.3177, 6.663])
# ========================================================================
# 
#  analysis at 190212040000UTC (16087.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16087.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.3288, 7.3667, 7.3789])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.280278,7.263889,7.248542])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.5899, 7.6229, 7.6348])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.2135, 7.2688, 7.2832])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.5239, 7.5673, 7.5782])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.5444, 7.5827, 7.5931])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.36, 7.3923, 7.3676])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.446340000000001, 7.4868, 7.4913799999999995, 7.4953, 7.473560000000001, 7.297440000000001, 6.6633])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1564527500557278, 0.15054444526451327, 0.15581589135900095, 0.1548823424409638, 0.13208046032627252, 0.014119242189296038, 5.522680508594028E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.446340000000001, 7.4868, 7.4913799999999995])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1564527500557278, 0.15054444526451327, 0.15581589135900095])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.446340000000001, 7.4868, 7.4913799999999995, 7.4953, 7.473560000000001, 7.297440000000001, 6.6633])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.3288, 7.3667, 7.3789])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.446340000000001, 7.4868, 7.4913799999999995, 7.4953, 7.473560000000001, 7.297440000000001, 6.6633])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212040000UTC  to 190212050000UTC  (16087.0-->16088.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.5253, 7.5634, 7.5764, 7.5846, 7.5674, 7.2929, 6.6634])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.2118, 7.245, 7.2554, 7.2606, 7.2615, 7.2467, 6.6645])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.4457, 7.4798, 7.4928, 7.5014, 7.5046, 7.3314, 6.6632])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.4459, 7.4874, 7.5004, 7.5091, 7.5128, 7.2932, 6.6633])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.3797, 7.409, 7.3573, 7.3546, 7.3512, 7.287, 6.6644])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.2915, 7.327, 7.3391, 7.3468, 7.3504, 7.3032, 6.6634])
# ========================================================================
# 
#  analysis at 190212050000UTC (16088.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16088.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.2915, 7.327, 7.3391])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.306736,7.219444,7.205])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.5253, 7.5634, 7.5764])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.2118, 7.245, 7.2554])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.4457, 7.4798, 7.4928])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.4459, 7.4874, 7.5004])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.3797, 7.409, 7.3573])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.401680000000001, 7.436920000000001, 7.43646, 7.4420600000000015, 7.4395, 7.290240000000001, 6.66376])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.118017591909003, 0.1204127567992693, 0.1283498656017994, 0.13125379232616485, 0.12791618349528733, 0.030067474120717464, 6.348228099242566E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.401680000000001, 7.436920000000001, 7.43646])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.118017591909003, 0.1204127567992693, 0.1283498656017994])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.401680000000001, 7.436920000000001, 7.43646, 7.4420600000000015, 7.4395, 7.290240000000001, 6.66376])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.2915, 7.327, 7.3391])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.401680000000001, 7.436920000000001, 7.43646, 7.4420600000000015, 7.4395, 7.290240000000001, 6.66376])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212050000UTC  to 190212060000UTC  (16088.0-->16089.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4745, 7.5033, 7.5158, 7.524, 7.5258, 7.3033, 6.6638])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.1674, 7.1964, 7.2079, 7.2161, 7.2214, 7.2191, 6.6652])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.439, 7.4713, 7.471, 7.4657, 7.4594, 7.3443, 6.6637])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.3877, 7.4151, 7.4265, 7.4346, 7.4391, 7.3094, 6.6637])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.2722, 7.3066, 7.3183, 7.3263, 7.3306, 7.2815, 6.665])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.2661, 7.2927, 7.303, 7.3092, 7.3117, 7.2823, 6.6638])
# ========================================================================
# 
#  analysis at 190212060000UTC (16089.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16089.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.2661, 7.2927, 7.303])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.228403,7.215278,7.2])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4745, 7.5033, 7.5158])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.1674, 7.1964, 7.2079])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.439, 7.4713, 7.471])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.3877, 7.4151, 7.4265])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.2722, 7.3066, 7.3183])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.34816, 7.37854, 7.387900000000001, 7.393340000000001, 7.3952599999999995, 7.29152, 6.66428])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1267095221362626, 0.12634917095098028, 0.12449712848094106, 0.12239155608129183, 0.11987993159824546, 0.04633909796273539, 7.529940238803638E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.34816, 7.37854, 7.387900000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1267095221362626, 0.12634917095098028, 0.12449712848094106])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.34816, 7.37854, 7.387900000000001, 7.393340000000001, 7.3952599999999995, 7.29152, 6.66428])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.2661, 7.2927, 7.303])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.34816, 7.37854, 7.387900000000001, 7.393340000000001, 7.3952599999999995, 7.29152, 6.66428])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212060000UTC  to 190212070000UTC  (16089.0-->16090.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4465, 7.471, 7.4784, 7.4835, 7.4858, 7.3095, 6.6643])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.1485, 7.1705, 7.1782, 7.1837, 7.1874, 7.1873, 6.6659])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.4366, 7.4552, 7.4581, 7.4554, 7.4479, 7.3271, 6.6642])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.3635, 7.3906, 7.398, 7.403, 7.4057, 7.3072, 6.6642])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.2522, 7.2747, 7.2829, 7.2884, 7.2915, 7.2665, 6.6656])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.2509, 7.2685, 7.2757, 7.2807, 7.2837, 7.2653, 6.6642])
# ========================================================================
# 
#  analysis at 190212070000UTC (16090.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16090.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.2509, 7.2685, 7.2757])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.213819,7.197986,7.177708])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4465, 7.471, 7.4784])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.1485, 7.1705, 7.1782])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.4366, 7.4552, 7.4581])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.3635, 7.3906, 7.398])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.2522, 7.2747, 7.2829])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.329460000000001, 7.3524, 7.359120000000001, 7.3628, 7.36366, 7.2795200000000015, 6.66484])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.12752616594252336, 0.12768901675555347, 0.1265681120977948, 0.12487139384182432, 0.12253221209135166, 0.05613129252030468, 8.384509526501572E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.329460000000001, 7.3524, 7.359120000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.12752616594252336, 0.12768901675555347, 0.1265681120977948])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.329460000000001, 7.3524, 7.359120000000001, 7.3628, 7.36366, 7.2795200000000015, 6.66484])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.2509, 7.2685, 7.2757])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.329460000000001, 7.3524, 7.359120000000001, 7.3628, 7.36366, 7.2795200000000015, 6.66484])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212070000UTC  to 190212080000UTC  (16090.0-->16091.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4364, 7.4562, 7.463, 7.4668, 7.4635, 7.3078, 6.6648])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.1161, 7.1415, 7.1491, 7.1546, 7.1583, 7.1598, 6.6667])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.4794, 7.4961, 7.4489, 7.4472, 7.4377, 7.3163, 6.6646])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.3271, 7.3546, 7.3617, 7.3665, 7.3692, 7.3091, 6.6647])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.2152, 7.2439, 7.251, 7.2561, 7.2592, 7.2467, 6.6662])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.2307, 7.2504, 7.2571, 7.2614, 7.2637, 7.248, 6.6647])
# ========================================================================
# 
#  analysis at 190212080000UTC (16091.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16091.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.2307, 7.2504, 7.2571])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.34625,7.230069,7.180278])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4364, 7.4562, 7.463])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.1161, 7.1415, 7.1491])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.4794, 7.4961, 7.4489])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.3271, 7.3546, 7.3617])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.2152, 7.2439, 7.251])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.314840000000001, 7.338460000000001, 7.33474, 7.338239999999999, 7.33758, 7.26794, 6.6654])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.15118932832710102, 0.1472314606325701, 0.13386987338456705, 0.13197463013776534, 0.1276366209204868, 0.066646552799076, 9.772410142845295E-4])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.314840000000001, 7.338460000000001, 7.33474])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.15118932832710102, 0.1472314606325701, 0.13386987338456705])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.314840000000001, 7.338460000000001, 7.33474, 7.338239999999999, 7.33758, 7.26794, 6.6654])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.2307, 7.2504, 7.2571])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.314840000000001, 7.338460000000001, 7.33474, 7.338239999999999, 7.33758, 7.26794, 6.6654])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212080000UTC  to 190212090000UTC  (16091.0-->16092.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4974, 7.4791, 7.4491, 7.4472, 7.4448, 7.3029, 6.6652])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.0715, 7.0997, 7.1105, 7.1185, 7.1243, 7.1272, 6.6677])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.5546, 7.5078, 7.459, 7.4478, 7.431, 7.3091, 6.665])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.395, 7.3757, 7.3475, 7.3464, 7.3455, 7.2965, 6.6652])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.1874, 7.2156, 7.2253, 7.2321, 7.2363, 7.2252, 6.6669])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.2261, 7.2555, 7.2456, 7.2457, 7.2458, 7.2331, 6.6651])
# ========================================================================
# 
#  analysis at 190212090000UTC (16092.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16092.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.2261, 7.2555, 7.2456])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.313403,7.242361,7.184583])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4974, 7.4791, 7.4491])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.0715, 7.0997, 7.1105])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.5546, 7.5078, 7.459])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.395, 7.3757, 7.3475])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.1874, 7.2156, 7.2253])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.3411800000000005, 7.33558, 7.318280000000001, 7.3184000000000005, 7.316380000000001, 7.25218, 6.666])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.20568481227353635, 0.1745722687026777, 0.14965594542148988, 0.1427633531407832, 0.13581692457127725, 0.07766045969475065, 0.001222701926063877])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.3411800000000005, 7.33558, 7.318280000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.20568481227353635, 0.1745722687026777, 0.14965594542148988])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.3411800000000005, 7.33558, 7.318280000000001, 7.3184000000000005, 7.316380000000001, 7.25218, 6.666])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.2261, 7.2555, 7.2456])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.3411800000000005, 7.33558, 7.318280000000001, 7.3184000000000005, 7.316380000000001, 7.25218, 6.666])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212090000UTC  to 190212100000UTC  (16092.0-->16093.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4046, 7.431, 7.4384, 7.4428, 7.437, 7.2967, 6.6657])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.0616, 7.0875, 7.0939, 7.0981, 7.1007, 7.1009, 6.6689])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.5349, 7.5309, 7.464, 7.4473, 7.4251, 7.3026, 6.6654])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.3, 7.3187, 7.3275, 7.3329, 7.3357, 7.2791, 6.6657])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.223, 7.2418, 7.2172, 7.217, 7.2168, 7.2051, 6.6675])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.2021, 7.2204, 7.227, 7.2315, 7.2341, 7.2232, 6.6655])
# ========================================================================
# 
#  analysis at 190212100000UTC (16093.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16093.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.2021, 7.2204, 7.227])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.257569,7.228403,7.203333])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4046, 7.431, 7.4384])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.0616, 7.0875, 7.0939])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.5349, 7.5309, 7.464])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.3, 7.3187, 7.3275])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.223, 7.2418, 7.2172])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.304820000000001, 7.32198, 7.308199999999999, 7.30762, 7.303060000000001, 7.236880000000001, 6.666640000000001])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1794202942813327, 0.17099224251409761, 0.154760831608001, 0.15044419895762046, 0.14343065571906172, 0.08541166196720441, 0.001512613632095065])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.304820000000001, 7.32198, 7.308199999999999])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1794202942813327, 0.17099224251409761, 0.154760831608001])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.304820000000001, 7.32198, 7.308199999999999, 7.30762, 7.303060000000001, 7.236880000000001, 6.666640000000001])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.2021, 7.2204, 7.227])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.304820000000001, 7.32198, 7.308199999999999, 7.30762, 7.303060000000001, 7.236880000000001, 6.666640000000001])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212100000UTC  to 190212110000UTC  (16093.0-->16094.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4954, 7.4974, 7.4251, 7.4233, 7.4214, 7.291, 6.6661])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.0365, 7.0685, 7.0777, 7.0824, 7.084, 7.0835, 6.6705])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.418, 7.4549, 7.4633, 7.4465, 7.4191, 7.2964, 6.6659])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.3472, 7.3731, 7.3217, 7.319, 7.3177, 7.2743, 6.6662])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.1456, 7.1805, 7.1902, 7.1973, 7.2023, 7.198, 6.6683])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.1859, 7.2159, 7.2168, 7.217, 7.2172, 7.2082, 6.666])
# ========================================================================
# 
#  analysis at 190212110000UTC (16094.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16094.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.1859, 7.2159, 7.2168])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.274375,7.185486,7.170208])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4954, 7.4974, 7.4251])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.0365, 7.0685, 7.0777])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.418, 7.4549, 7.4633])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.3472, 7.3731, 7.3217])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.1456, 7.1805, 7.1902])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.288540000000001, 7.314880000000001, 7.2956, 7.2937, 7.288900000000002, 7.228640000000002, 6.667400000000001])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.19166895418924784, 0.18375922289779079, 0.16137248836155432, 0.153886922771235, 0.14562048276255665, 0.09023504308194252, 0.001987460691435128])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.288540000000001, 7.314880000000001, 7.2956])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.19166895418924784, 0.18375922289779079, 0.16137248836155432])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.288540000000001, 7.314880000000001, 7.2956, 7.2937, 7.288900000000002, 7.228640000000002, 6.667400000000001])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.1859, 7.2159, 7.2168])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.288540000000001, 7.314880000000001, 7.2956, 7.2937, 7.288900000000002, 7.228640000000002, 6.667400000000001])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212110000UTC  to 190212120000UTC  (16094.0-->16095.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.5033, 7.5191, 7.4366, 7.4241, 7.4152, 7.2862, 6.6666])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.2083, 7.2071, 7.0715, 7.0689, 7.069, 7.0679, 6.6724])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.3564, 7.396, 7.4055, 7.4115, 7.4119, 7.2919, 6.6664])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.3643, 7.3861, 7.3312, 7.3241, 7.3162, 7.2615, 6.6667])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.2515, 7.2458, 7.1824, 7.1807, 7.1806, 7.1738, 6.6691])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.1807, 7.2046, 7.199, 7.1992, 7.1993, 7.1924, 6.6665])
# ========================================================================
# 
#  analysis at 190212120000UTC (16095.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16095.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.1807, 7.2046, 7.199])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.200694,7.182708,7.164931])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.5033, 7.5191, 7.4366])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.2083, 7.2071, 7.0715])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.3564, 7.396, 7.4055])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.3643, 7.3861, 7.3312])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.2515, 7.2458, 7.1824])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.336760000000002, 7.350820000000001, 7.28544, 7.281860000000001, 7.27858, 7.21626, 6.668240000000001])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1147290198685581, 0.12578623533598585, 0.15471368071376224, 0.15362964557662692, 0.15114427544568132, 0.09548980573862328, 0.0025735189915754484])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.336760000000002, 7.350820000000001, 7.28544])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1147290198685581, 0.12578623533598585, 0.15471368071376224])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.336760000000002, 7.350820000000001, 7.28544, 7.281860000000001, 7.27858, 7.21626, 6.668240000000001])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.1807, 7.2046, 7.199])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.336760000000002, 7.350820000000001, 7.28544, 7.281860000000001, 7.27858, 7.21626, 6.668240000000001])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212120000UTC  to 190212130000UTC  (16095.0-->16096.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4525, 7.476, 7.455, 7.4245, 7.4093, 7.2812, 6.667])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.5532, 7.223, 7.092, 7.0701, 7.0688, 7.0655, 6.6744])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.5701, 7.4346, 7.3992, 7.3962, 7.3909, 7.2966, 6.6669])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.3087, 7.3318, 7.3359, 7.3237, 7.3138, 7.2522, 6.6672])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.1573, 7.1779, 7.1826, 7.1807, 7.1797, 7.1674, 6.67])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.1641, 7.1789, 7.1846, 7.1883, 7.1905, 7.1844, 6.667])
# ========================================================================
# 
#  analysis at 190212130000UTC (16096.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16096.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.1641, 7.1789, 7.1846])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.282778,7.230625,7.179375])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4525, 7.476, 7.455])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.5532, 7.223, 7.092])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.5701, 7.4346, 7.3992])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.3087, 7.3318, 7.3359])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.1573, 7.1779, 7.1826])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.408360000000001, 7.328660000000001, 7.292940000000001, 7.279039999999999, 7.2725, 7.21258, 6.6691])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1746782985948741, 0.12926216770579077, 0.15161793429538628, 0.1501717949549782, 0.1453822719591352, 0.09619195392547131, 0.003231098884280821])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.408360000000001, 7.328660000000001, 7.292940000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1746782985948741, 0.12926216770579077, 0.15161793429538628])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.408360000000001, 7.328660000000001, 7.292940000000001, 7.279039999999999, 7.2725, 7.21258, 6.6691])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.1641, 7.1789, 7.1846])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.408360000000001, 7.328660000000001, 7.292940000000001, 7.279039999999999, 7.2725, 7.21258, 6.6691])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212130000UTC  to 190212140000UTC  (16096.0-->16097.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4467, 7.4639, 7.4386, 7.4317, 7.4032, 7.2763, 6.6675])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.5024, 7.3519, 7.1082, 7.071, 7.0686, 7.064, 6.6767])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.5279, 7.5281, 7.4046, 7.3967, 7.3856, 7.2909, 6.6673])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.316, 7.3318, 7.3182, 7.3169, 7.3097, 7.2463, 6.6678])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.1176, 7.1416, 7.1495, 7.1554, 7.1596, 7.1587, 6.6711])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.1638, 7.1842, 7.176, 7.1762, 7.1763, 7.1709, 6.6676])
# ========================================================================
# 
#  analysis at 190212140000UTC (16097.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16097.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.1638, 7.1842, 7.176])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.262917,7.219583,7.182153])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4467, 7.4639, 7.4386])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.5024, 7.3519, 7.1082])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.5279, 7.5281, 7.4046])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.316, 7.3318, 7.3182])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.1176, 7.1416, 7.1495])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.3821200000000005, 7.363460000000001, 7.28382, 7.274340000000001, 7.265339999999999, 7.207239999999999, 6.6700800000000005])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1689913814370423, 0.1479462503749249, 0.14883790511828646, 0.15575571578597056, 0.14605070352449523, 0.09508915816222156, 0.004013975585376768])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.3821200000000005, 7.363460000000001, 7.28382])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1689913814370423, 0.1479462503749249, 0.14883790511828646])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.3821200000000005, 7.363460000000001, 7.28382, 7.274340000000001, 7.265339999999999, 7.207239999999999, 6.6700800000000005])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.1638, 7.1842, 7.176])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.3821200000000005, 7.363460000000001, 7.28382, 7.274340000000001, 7.265339999999999, 7.207239999999999, 6.6700800000000005])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212140000UTC  to 190212150000UTC  (16097.0-->16098.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.4275, 7.4495, 7.4475, 7.4343, 7.3969, 7.2717, 6.6681])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.3603, 7.3656, 7.1444, 7.0716, 7.0683, 7.0618, 6.6797])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.4982, 7.5097, 7.4095, 7.3963, 7.3809, 7.2847, 6.6678])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.2806, 7.3019, 7.3076, 7.3109, 7.305, 7.241, 6.6684])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.1104, 7.1315, 7.1372, 7.1414, 7.1435, 7.1399, 6.6723])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.1386, 7.1579, 7.1634, 7.1673, 7.1696, 7.1652, 6.6682])
# ========================================================================
# 
#  analysis at 190212150000UTC (16098.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16098.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.1386, 7.1579, 7.1634])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.157222,7.157917,7.134792])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.4275, 7.4495, 7.4475])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.3603, 7.3656, 7.1444])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.4982, 7.5097, 7.4095])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.2806, 7.3019, 7.3076])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.1104, 7.1315, 7.1372])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.3354, 7.351640000000001, 7.289240000000001, 7.270900000000001, 7.258920000000001, 7.19982, 6.67126])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.1493605536947422, 0.14636436724831614, 0.14486249687203379, 0.15852086613439895, 0.14637172541170623, 0.09579544352420946, 0.005060928768516916])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.3354, 7.351640000000001, 7.289240000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.1493605536947422, 0.14636436724831614, 0.14486249687203379])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.3354, 7.351640000000001, 7.289240000000001, 7.270900000000001, 7.258920000000001, 7.19982, 6.67126])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.1386, 7.1579, 7.1634])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.3354, 7.351640000000001, 7.289240000000001, 7.270900000000001, 7.258920000000001, 7.19982, 6.67126])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212150000UTC  to 190212160000UTC  (16098.0-->16099.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
# computation for member (5):
# - member 0
# - member 1
# - member 2
# - member 3
# - member 4
#  resultItem id: xi_f_0, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_0.append([7.3797, 7.4046, 7.4122, 7.4167, 7.3977, 7.265, 6.6686])
#  resultItem id: xi_f_1, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_1.append([7.4741, 7.424, 7.1769, 7.0732, 7.067, 7.0581, 6.683])
#  resultItem id: xi_f_2, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_2.append([7.42, 7.4472, 7.432, 7.3955, 7.3717, 7.2769, 6.6683])
#  resultItem id: xi_f_3, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_3.append([7.2766, 7.2976, 7.3016, 7.2994, 7.293, 7.2354, 6.6691])
#  resultItem id: xi_f_4, outputLevel: All, context: forecast step
#  state: temperature.state
xi_f_4.append([7.088, 7.1138, 7.1219, 7.1273, 7.1303, 7.1253, 6.6738])
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([7.1104, 7.1399, 7.1475, 7.1523, 7.1548, 7.1496, 6.6688])
# ========================================================================
# 
#  analysis at 190212160000UTC (16099.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time.append(16099.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([7.1104, 7.1399, 7.1475])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([7.169236,7.141389,7.116667])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work1/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_0, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_0.append([7.3797, 7.4046, 7.4122])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work2/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_1, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_1.append([7.4741, 7.424, 7.1769])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work3/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_2, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_2.append([7.42, 7.4472, 7.432])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work4/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_3, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_3.append([7.2766, 7.2976, 7.3016])
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work5/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_4, outputLevel: Verbose, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_4.append([7.088, 7.1138, 7.1219])
#  resultItem id: x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_f.append([7.327680000000001, 7.33744, 7.288920000000001, 7.262419999999999, 7.251940000000001, 7.192140000000001, 6.672560000000001])
#  resultItem id: std_x_f, outputLevel: Verbose, context: analysis step
#  state: temperature.state
std_x_f.append([0.15225270769349217, 0.13752493592072662, 0.13808945289195712, 0.15567734902676109, 0.14686171386716143, 0.0959147694570551, 0.006251639784888334])
#  resultItem id: pred_f, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f.append([7.327680000000001, 7.33744, 7.288920000000001])
#  resultItem id: pred_f_std, outputLevel: Normal, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_f_std.append([0.15225270769349217, 0.13752493592072662, 0.13808945289195712])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([7.327680000000001, 7.33744, 7.288920000000001, 7.262419999999999, 7.251940000000001, 7.192140000000001, 6.672560000000001])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([7.1104, 7.1399, 7.1475])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([7.327680000000001, 7.33744, 7.288920000000001, 7.262419999999999, 7.251940000000001, 7.192140000000001, 6.672560000000001])
# Algorithm Done
# Application Done
# Try to merge lists into arrays
try :
   obs=np.vstack(obs)
except :
   print("Could not merge list into array for obs")
try :
   pred_f_0=np.vstack(pred_f_0)
except :
   print("Could not merge list into array for pred_f_0")
try :
   x_a_central=np.vstack(x_a_central)
except :
   print("Could not merge list into array for x_a_central")
try :
   analysis_time=np.vstack(analysis_time)
except :
   print("Could not merge list into array for analysis_time")
try :
   pred_f_2=np.vstack(pred_f_2)
except :
   print("Could not merge list into array for pred_f_2")
try :
   pred_f_1=np.vstack(pred_f_1)
except :
   print("Could not merge list into array for pred_f_1")
try :
   pred_f_std=np.vstack(pred_f_std)
except :
   print("Could not merge list into array for pred_f_std")
try :
   pred_a_central=np.vstack(pred_a_central)
except :
   print("Could not merge list into array for pred_a_central")
try :
   pred_f_4=np.vstack(pred_f_4)
except :
   print("Could not merge list into array for pred_f_4")
try :
   pred_f_3=np.vstack(pred_f_3)
except :
   print("Could not merge list into array for pred_f_3")
try :
   std_x_f=np.vstack(std_x_f)
except :
   print("Could not merge list into array for std_x_f")
try :
   xi_f_0=np.vstack(xi_f_0)
except :
   print("Could not merge list into array for xi_f_0")
try :
   xi_f_2=np.vstack(xi_f_2)
except :
   print("Could not merge list into array for xi_f_2")
try :
   xi_f_1=np.vstack(xi_f_1)
except :
   print("Could not merge list into array for xi_f_1")
try :
   xi_f_4=np.vstack(xi_f_4)
except :
   print("Could not merge list into array for xi_f_4")
try :
   xi_f_3=np.vstack(xi_f_3)
except :
   print("Could not merge list into array for xi_f_3")
try :
   pred_f_central=np.vstack(pred_f_central)
except :
   print("Could not merge list into array for pred_f_central")
try :
   x_f_central=np.vstack(x_f_central)
except :
   print("Could not merge list into array for x_f_central")
try :
   x_a=np.vstack(x_a)
except :
   print("Could not merge list into array for x_a")
try :
   pred_f=np.vstack(pred_f)
except :
   print("Could not merge list into array for pred_f")
try :
   x_f=np.vstack(x_f)
except :
   print("Could not merge list into array for x_f")

