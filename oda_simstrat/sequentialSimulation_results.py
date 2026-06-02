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
# analysisTimes acquired from OBSERVER:16073.5 -- 16098.5
# Application initializing finished
# Initializing Algorithm
# Algorithm initialized
# Algorithm starting next step
# ========================================================================
# 
#  Forecast from 190211180000UTC  to 190211201200UTC  (16071.0-->16073.5) 
# 
# ========================================================================
# 
# - mainModel 
# 
#  resultItem id: x_f_central, outputLevel: Verbose, context: forecast step
x_f_central=[]
#  state: temperature.state
x_f_central.append([8.0658, 8.0627, 8.0602, 8.0538, 7.6232, 7.1733, 6.6581])
# ========================================================================
# 
#  analysis at 190211201200UTC (16073.5) 
# 
# ========================================================================
# 
#  resultItem id: analysis_time, outputLevel: Normal, context: analysis step
analysis_time=[]
analysis_time.append(16073.5)
# Error running algorithm step.
# Error message: announceObservedValues:
# No prediction subvector found for obs id "T_1m"
# Available subvectors are:
#       T_0m
#       T_10m
#       T_20m
# 
# 
# Error type :RuntimeException
# Stacktrace :java.lang.RuntimeException: announceObservedValues:
# No prediction subvector found for obs id "T_1m"
# Available subvectors are:
#       T_0m
#       T_10m
#       T_20m
# 
# 
# 	at org.openda.blackbox.wrapper.BBStochModelInstance.findPredictionVectorConfig(BBStochModelInstance.java:1433)
# 	at org.openda.blackbox.wrapper.BBStochModelInstance.getObservedValuesBB(BBStochModelInstance.java:938)
# 	at org.openda.blackbox.wrapper.BBStochModelInstance.getObservedValues(BBStochModelInstance.java:917)
# 	at org.openda.observationOperators.ObservationOperatorDeprecatedModel.getObservedValues(ObservationOperatorDeprecatedModel.java:56)
# 	at org.openda.algorithms.kalmanFilter.AbstractSequentialAlgorithm.next(AbstractSequentialAlgorithm.java:495)
# 	at org.openda.application.ApplicationRunnerSingleThreaded.runSingleThreaded(ApplicationRunnerSingleThreaded.java:86)
# 	at org.openda.application.OpenDaApplication.runApplicationBatch(OpenDaApplication.java:114)
# 	at org.openda.application.OpenDaApplication.main(OpenDaApplication.java:102)
# 
# Application Done
# Try to merge lists into arrays
try :
   x_f_central=np.vstack(x_f_central)
except :
   print("Could not merge list into array for x_f_central")
try :
   analysis_time=np.vstack(analysis_time)
except :
   print("Could not merge list into array for analysis_time")

