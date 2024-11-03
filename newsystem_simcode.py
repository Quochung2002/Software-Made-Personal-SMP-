#PythonSim and Python package imports
import pandas as pd
import numpy as np
import math
import SimClasses
import SimFunctions
import SimRNG

# Initialize simulation
ZRNG = SimRNG.InitializeRNSeed()
Calendar = SimClasses.EventCalendar()

# Call service center is open from 8am-4pm (8 hours)
# 60 minutes in an hour ("period")
# ARate is arrival rate in calls per hour
NPeriods = 8
PeriodLength = 60
ARate = 1

# Mean and variance parameters for
# normal distribution for service time
# for both financial tracking and contact management
FinMean = 5 * 1.1  # Increased by 10% for cross-trained operators
ContactMean = 5 * 1.1  # Increased by 10% for cross-trained operators
RunLength = 480  # Total average customers calling to the support center

# Specify the initial estimate of cross-trained operators needed
NumCrossTrained = 7  # Initial guess, can adjust based on results

# Number of simulation replications
NumReps = 480

# Simulation statistics trackers for the unified (cross-trained) system
CrossTrainedTIS = SimClasses.DTStat()
CrossTrainedWithin5 = SimClasses.DTStat()
CrossTrainedOperator = SimClasses.Resource()
CrossTrainedOperatorQueue = SimClasses.FIFOQueue()

# Statistics lists
CrossTrainedTISavg = []
CrossTrainedPropWithin5 = []
CrossTrainedOperatorBusyAvg = []
CrossTrainedOperatorQueueAvg = []
CrossTrainedQueueTimeAvg= []
EndingTime = []

# Add this to initialize a new statistic tracker for queue time
CrossTrainedQueueTime = SimClasses.DTStat()

def CrossTrained_Arrival():
    '''Handles arrival of both financial and contact management calls to a cross-trained operator.'''
    InterarrivalTime = 1 / 1  # 60 calls per hour
    if SimClasses.Clock + InterarrivalTime > RunLength:
        return
    SimFunctions.Schedule(Calendar, "CrossTrained_Arrival", InterarrivalTime)

    # Determine call type based on historical probabilities
    if np.random.rand() < 0.59:  # Financial call
        ServiceTime = SimRNG.Erlang(2, FinMean, 2)
    else:  # Contact management call
        ServiceTime = SimRNG.Erlang(3, ContactMean, 2)

    Call = SimClasses.Entity()
    if CrossTrainedOperator.CurrentNumBusy < CrossTrainedOperator.NumberOfUnits:
        CrossTrainedOperator.Seize(1)
        SimFunctions.SchedulePlus(Calendar, "CrossTrainedEndOfService", ServiceTime, Call)
    else:
        Call.EntryTime = SimClasses.Clock  # Record the time the call enters the queue
        CrossTrainedOperatorQueue.Add(Call)

def CrossTrainedEndOfService(DepartingCall):
    '''Called when a call finishes service in the cross-trained system.'''
    TIS = SimClasses.Clock - DepartingCall.CreateTime
    CrossTrainedTIS.Record(TIS)
    CrossTrainedWithin5.Record((TIS < 5.5))  # Adjusted to account for 10% longer time

    if CrossTrainedOperatorQueue.NumQueue() > 0 and CrossTrainedOperator.NumberOfUnits >= CrossTrainedOperator.CurrentNumBusy:
        NextCall = CrossTrainedOperatorQueue.Remove()
        
        # Calculate the time spent in the queue
        QueueTime = SimClasses.Clock - NextCall.EntryTime
        CrossTrainedQueueTime.Record(QueueTime)  # Record the queue time
        
        # Determine service time for the next call
        if np.random.rand() < 0.59:
            ServiceTime = SimRNG.Erlang(2, FinMean, 2)
        else:
            ServiceTime = SimRNG.Erlang(3, ContactMean, 2)
        SimFunctions.SchedulePlus(Calendar, "CrossTrainedEndOfService", ServiceTime, NextCall)
    else:
        CrossTrainedOperator.Free(1)

# Running the simulation for each replication
for reps in range(NumReps):
    # Initialization
    SimFunctions.SimFunctionsInit(Calendar)
    CrossTrainedOperator.SetUnits(NumCrossTrained)
    SimFunctions.Schedule(Calendar, "CrossTrained_Arrival", 1 / 1)

    # Main simulation loop
    while Calendar.N() > 0:
        NextEvent = Calendar.Remove()
        SimClasses.Clock = NextEvent.EventTime

        if SimClasses.Clock >= RunLength:
                break

        if NextEvent.EventType == "CrossTrained_Arrival":
            CrossTrained_Arrival()
        elif NextEvent.EventType == "CrossTrainedEndOfService":
            CrossTrainedEndOfService(NextEvent.WhichObject)

    # Store statistics after each replication
    CrossTrainedTISavg.append(CrossTrainedTIS.Mean())
    CrossTrainedOperatorQueueAvg.append(CrossTrainedOperatorQueue.Mean())
    # CrossTrainedPropWithin5.append(CrossTrainedWithin5.Mean())
    CrossTrainedOperatorBusyAvg.append(CrossTrainedOperator.Mean())
    EndingTime.append(SimClasses.Clock)
    CrossTrainedQueueTimeAvg.append(CrossTrainedQueueTime.Mean())  # Record average queue time for this replication

# Output results to a CSV
output = pd.DataFrame({
    "CrossTrainedTISavg": CrossTrainedTISavg,
    "CrossTrainedOperatorQueueAvg": CrossTrainedOperatorQueueAvg,
    "CrossTrainedOperatorBusyAvg": CrossTrainedOperatorBusyAvg,
    # "CrossTrainedPropWithin5": CrossTrainedPropWithin5,
    "CrossTrainedQueueTimeAvg": CrossTrainedQueueTimeAvg,  # Add average queue time to output
    "EndingTime": EndingTime
})
output.to_csv("cross_trained_output.csv", sep=",")
print("Means")
print(output.mean())
print("95% CI Half-Width")
print(1.96 * np.sqrt(output.var(ddof=0) / len(output)))
