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
ARate = 60

# Mean service time for financial and contact management calls
FinMean = 5
ContactMean = 5
RunLength = 480  # Total time for the call center to run in minutes

# Specify staffing for each service line
NumFinanceOperators = 4
NumContactOperators = 3

# Number of simulation replications
NumReps = 10

# Statistics trackers
FinanceTIS = SimClasses.DTStat()
FinanceWithin5 = SimClasses.DTStat()
ContactTIS = SimClasses.DTStat()
ContactWithin5 = SimClasses.DTStat()
FinanceOperator = SimClasses.Resource()
FinanceOperatorQueue = SimClasses.FIFOQueue()
ContactOperator = SimClasses.Resource()
ContactOperatorQueue = SimClasses.FIFOQueue()

# Statistics lists for output
FinanceTISavg = []
FinancePropWithin5 = []
ContactTISavg = []
ContactPropWithin5 = []
FinanceOperatorBusyAvg = []
FinanceOperatorQueueAvg = []
ContactOperatorBusyAvg = []
ContactOperatorQueueAvg = []
EndingTime = []

def Finance_Arrival():
    '''Handles arrival of financial tracking calls to the financial operators.'''
    InterarrivalTime = 1 / (1 * 0.59)  # 59% of calls are financial
    if SimClasses.Clock + InterarrivalTime > RunLength:
        return
    SimFunctions.Schedule(Calendar, "Finance_Arrival", InterarrivalTime)

    Call = SimClasses.Entity()
    if FinanceOperator.CurrentNumBusy < FinanceOperator.NumberOfUnits:
        FinanceOperator.Seize(1)
        SimFunctions.SchedulePlus(Calendar, "FinanceEndOfService", SimRNG.Erlang(2, FinMean, 2), Call)
    else:
        FinanceOperatorQueue.Add(Call)

def Contact_Arrival():
    '''Handles arrival of contact management calls to the contact operators.'''
    # InterarrivalTime = 1 / 1 * 0.41  # 41% of calls are contact management
    cInterarrivalTime = 1 / (1 * 0.41)  # 41% of calls are contact management
    if SimClasses.Clock + cInterarrivalTime > RunLength:
        return
    SimFunctions.Schedule(Calendar, "Contact_Arrival", cInterarrivalTime)

    Call = SimClasses.Entity()
    if ContactOperator.CurrentNumBusy < ContactOperator.NumberOfUnits:
        ContactOperator.Seize(1)
        SimFunctions.SchedulePlus(Calendar, "ContactEndOfService", SimRNG.Erlang(3, ContactMean, 3), Call)
    else:
        ContactOperatorQueue.Add(Call)

def FinanceEndOfService(DepartingCall):
    '''Called when a financial call finishes service.'''
    TIS = SimClasses.Clock - DepartingCall.CreateTime
    FinanceTIS.Record(TIS)
    FinanceWithin5.Record((TIS < 5))

    if FinanceOperatorQueue.NumQueue() > 0 and FinanceOperator.NumberOfUnits >= FinanceOperator.CurrentNumBusy:
        NextCall = FinanceOperatorQueue.Remove()
        SimFunctions.SchedulePlus(Calendar, "FinanceEndOfService", SimRNG.Erlang(2, FinMean, 2), NextCall)
    else:
        FinanceOperator.Free(1)

def ContactEndOfService(DepartingCall):
    '''Called when a contact management call finishes service.'''
    TIS = SimClasses.Clock - DepartingCall.CreateTime
    ContactTIS.Record(TIS)
    ContactWithin5.Record((TIS < 5))

    if ContactOperatorQueue.NumQueue() > 0 and ContactOperator.NumberOfUnits >= ContactOperator.CurrentNumBusy:
        NextCall = ContactOperatorQueue.Remove()
        SimFunctions.SchedulePlus(Calendar, "ContactEndOfService", SimRNG.Erlang(3, ContactMean, 3), NextCall)
    else:
        ContactOperator.Free(1)

# Define initial settings and desired relative error
target_relative_error = 0.05
initial_reps = 10
max_reps = 1000  # Set a maximum in case convergence takes too long

# Placeholder for storing results
all_results = []

current_reps = initial_reps
relative_errors_met = False

while not relative_errors_met and current_reps <= max_reps:
    FinanceTISavg = []
    FinancePropWithin5 = []
    ContactTISavg = []
    ContactPropWithin5 = []
    FinanceOperatorQueueAvg = []
    ContactOperatorQueueAvg = []

    # Run simulation for current number of replications
    for reps in range(current_reps):
        # Initialize simulation settings
        SimFunctions.SimFunctionsInit(Calendar)
        FinanceOperator.SetUnits(NumFinanceOperators)
        ContactOperator.SetUnits(NumContactOperators)
        SimFunctions.Schedule(Calendar, "Finance_Arrival", 1 / (1 * 0.59))
        SimFunctions.Schedule(Calendar, "Contact_Arrival", 1 / (1* 0.41))

        # Main simulation loop
        while Calendar.N() > 0:
            NextEvent = Calendar.Remove()
            SimClasses.Clock = NextEvent.EventTime

            if SimClasses.Clock >= RunLength:
                break

            if NextEvent.EventType == "Finance_Arrival":
                Finance_Arrival()
            elif NextEvent.EventType == "Contact_Arrival":
                Contact_Arrival()
            elif NextEvent.EventType == "FinanceEndOfService":
                FinanceEndOfService(NextEvent.WhichObject)
            elif NextEvent.EventType == "ContactEndOfService":
                ContactEndOfService(NextEvent.WhichObject)

        # Store statistics for this replication
        FinanceTISavg.append(FinanceTIS.Mean())
        FinancePropWithin5.append(FinanceWithin5.Mean())
        ContactTISavg.append(ContactTIS.Mean())
        ContactPropWithin5.append(ContactWithin5.Mean())
        FinanceOperatorQueueAvg.append(FinanceOperatorQueue.Mean())
        ContactOperatorQueueAvg.append(ContactOperatorQueue.Mean())

    # Convert to DataFrame for easier analysis
    results = pd.DataFrame({
        "FinanceTISavg": FinanceTISavg,
        "FinancePropWithin5": FinancePropWithin5,
        "ContactTISavg": ContactTISavg,
        "ContactPropWithin5": ContactPropWithin5,
        "FinanceOperatorQueueAvg": FinanceOperatorQueueAvg,
        "ContactOperatorQueueAvg": ContactOperatorQueueAvg,
    })
    
    all_results.append(results)

    # Calculate mean and half-width of CI for each metric
    means = results.mean()
    std_devs = results.std(ddof=1)
    half_widths = 1.96 * std_devs / np.sqrt(current_reps)

    # Calculate relative errors for each metric
    relative_errors = half_widths / means

    # Check if all relative errors are within the target
    if (relative_errors <= target_relative_error).all():
        relative_errors_met = True
    else:
        current_reps += 10  # Increase replications incrementally if not met

# Final output with relative error check
print(f"Final number of replications: {current_reps}")
print("Relative Errors:")
print(relative_errors)
print("Results Mean:")
print(means)
print("95% CI Half-Widths:")
print(half_widths)
