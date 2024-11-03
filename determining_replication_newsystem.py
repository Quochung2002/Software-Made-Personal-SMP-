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
NumCrossTrained = 8  # Initial guess, can adjust based on results

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
EndingTime = []

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
        CrossTrainedOperatorQueue.Add(Call)

def CrossTrainedEndOfService(DepartingCall):
    '''Called when a call finishes service in the cross-trained system.'''
    TIS = SimClasses.Clock - DepartingCall.CreateTime
    CrossTrainedTIS.Record(TIS)
    CrossTrainedWithin5.Record((TIS < 5.5))  # Adjusted to account for 10% longer time

    if CrossTrainedOperatorQueue.NumQueue() > 0 and CrossTrainedOperator.NumberOfUnits >= CrossTrainedOperator.CurrentNumBusy:
        NextCall = CrossTrainedOperatorQueue.Remove()
        if np.random.rand() < 0.59:
            ServiceTime = SimRNG.Erlang(2, FinMean, 2)
        else:
            ServiceTime = SimRNG.Erlang(3, ContactMean, 2)
        SimFunctions.SchedulePlus(Calendar, "CrossTrainedEndOfService", ServiceTime, NextCall)
    else:
        CrossTrainedOperator.Free(1)


# Set initial parameters
relative_error_threshold = 0.05  # 5% relative error
NumReps = 2  # Initial number of replications
max_reps = 1000  # Set a limit to avoid infinite loop

# Initialize lists to store statistics for each replication
CrossTrainedTISavg = []
CrossTrainedPropWithin5 = []

def calculate_relative_error(data):
    """Calculate relative error for a list of replication means."""
    mean = np.mean(data)
    variance = np.var(data, ddof=1)
    half_width = 1.96 * np.sqrt(variance / len(data))
    relative_error = half_width / mean if mean != 0 else np.inf
    return relative_error, half_width

# Main loop to add replications until relative error is within the threshold
for reps in range(max_reps):
    # Run single replication
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

    # Store replication statistics
    CrossTrainedTISavg.append(CrossTrainedTIS.Mean())
    CrossTrainedPropWithin5.append(CrossTrainedWithin5.Mean())

    # Check relative error every 10 replications
    if (reps + 1) % 10 == 0:
        rel_error_tis, hw_tis = calculate_relative_error(CrossTrainedTISavg)
        rel_error_prop, hw_prop = calculate_relative_error(CrossTrainedPropWithin5)

        # Stop if relative error is within threshold for all KPIs
        if rel_error_tis <= relative_error_threshold and rel_error_prop <= relative_error_threshold:
            print(f"Converged after {reps + 1} replications.")
            break
else:
    print("Max replications reached without convergence.")

# Output results to CSV
output = pd.DataFrame({
    "CrossTrainedTISavg": CrossTrainedTISavg,
    "CrossTrainedPropWithin5": CrossTrainedPropWithin5,
})
output.to_csv("cross_trained_output.csv", sep=",")
print("Means")
print(output.mean())
print("95% CI Half-Width")
print(1.96 * np.sqrt(output.var(ddof=0) / len(output)))
