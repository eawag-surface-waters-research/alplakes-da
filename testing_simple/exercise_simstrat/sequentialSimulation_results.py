import numpy as np
# OpenDA version 3.4.0.-1 February 27 2026
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochObserver/timeSeriesFormatter.xml
# Starting Algorithm: 
# 	className: org.openda.algorithms.kalmanFilter.SequentialSimulation
# 	dir.: ././algorithms
# 	config.: SequentialSimulation.xml
# configstring = SequentialSimulation.xml
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././algorithms/SequentialSimulation.xml
# analysisTimes@type=fromObservationTimes
# mainModel@stochParameter=false
# mainModel@stochForcing=false
# mainModel@stochInit=false
# Creating mainModel
# Create new BBModelInstance with number: 0
# Instance initialization done
#    Do not add noise to forcing
# model time 16071.0 16099.0
# analysisTimes acquired from OBSERVER:16078.0 -- 16085.0
# Application initializing finished
# Initializing Algorithm
# Algorithm initialized
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211180000UTC  to 190211250000UTC  (16071.0-->16078.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
x_f_central=[]
#  state: temperature.state
x_f_central.append([5.0453, 5.0912, 5.0798, 5.0009, 4.9251, 4.5663, 4.5017])
# ========================================================================
# 
#  analysis at 190211250000UTC (16078.0) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time=[]
analysis_time.append(16078.0)
# opening :/mnt/c/Users/toschith/Documents/Work/alplakes-da/testing_simple/exercise_simstrat/././stochModel/./../work/work0/timeSeriesFormatter.xml
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_f_central, outputLevel: Essential, context: analysis step
pred_f_central=[]
#  predictions: T_0m, T_10m, T_20m
pred_f_central.append([5.0453, 5.0912, 5.0798])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs=[]
obs.append([4.7564,4.8104,4.7854])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
x_a=[]
#  state: temperature.state
x_a.append([5.0453, 5.0912, 5.0798, 5.0009, 4.9251, 4.5663, 4.5017])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
pred_a_central=[]
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([5.0453, 5.0912, 5.0798])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
x_a_central=[]
#  state: temperature.state
x_a_central.append([5.0453, 5.0912, 5.0798, 5.0009, 4.9251, 4.5663, 4.5017])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211250000UTC  to 190212020000UTC  (16078.0-->16085.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([4.7672, 4.8431, 4.8632, 4.8688, 4.822, 4.6621, 4.5062])
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
pred_f_central.append([4.7672, 4.8431, 4.8632])
#  resultItem id: obs, outputLevel: Essential, context: analysis step
obs.append([4.612,4.765,4.74])
#  resultItem id: x_a, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a.append([4.7672, 4.8431, 4.8632, 4.8688, 4.822, 4.6621, 4.5062])
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_0m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_10m'.
# Getting model values at observed coordinates for scalar observation exchangeItem with id 'T_20m'.
#  resultItem id: pred_a_central, outputLevel: Essential, context: analysis step
#  predictions: T_0m, T_10m, T_20m
pred_a_central.append([4.7672, 4.8431, 4.8632])
#  resultItem id: x_a_central, outputLevel: Verbose, context: analysis step
#  state: temperature.state
x_a_central.append([4.7672, 4.8431, 4.8632, 4.8688, 4.822, 4.6621, 4.5062])
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190212020000UTC  to 190212160000UTC  (16085.0-->16099.0) 
# 
# ========================================================================
# 
# - mainModel 
# 
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
#  state: temperature.state
x_f_central.append([4.6463, 4.682, 4.6813, 4.6767, 4.6705, 4.6631, 4.6437])
# Algorithm Done
# Application Done
# Try to merge lists into arrays
try :
   obs=np.vstack(obs)
except :
   print("Could not merge list into array for obs")
try :
   pred_f_central=np.vstack(pred_f_central)
except :
   print("Could not merge list into array for pred_f_central")
try :
   x_a_central=np.vstack(x_a_central)
except :
   print("Could not merge list into array for x_a_central")
try :
   x_f_central=np.vstack(x_f_central)
except :
   print("Could not merge list into array for x_f_central")
try :
   analysis_time=np.vstack(analysis_time)
except :
   print("Could not merge list into array for analysis_time")
try :
   x_a=np.vstack(x_a)
except :
   print("Could not merge list into array for x_a")
try :
   pred_a_central=np.vstack(pred_a_central)
except :
   print("Could not merge list into array for pred_a_central")

