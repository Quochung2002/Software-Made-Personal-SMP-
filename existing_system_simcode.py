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
NumReps = 480

# Statistics trackers
FinanceTIS = SimClasses.DTStat()
FinanceWithin5 = SimClasses.DTStat()
ContactTIS = SimClasses.DTStat()
ContactWithin5 = SimClasses.DTStat()
FinanceOperator = SimClasses.Resource()
FinanceOperatorQueue = SimClasses.FIFOQueue()
ContactOperator = SimClasses.Resource()
ContactOperatorQueue = SimClasses.FIFOQueue()
FinanceQueueTime = SimClasses.DTStat()
ContactQueueTime = SimClasses.DTStat()

# Statistics lists for output
FinanceTISavg = []
FinancePropWithin5 = []
ContactTISavg = []
ContactPropWithin5 = []
FinanceOperatorBusyAvg = []
FinanceOperatorQueueAvg = []
ContactOperatorBusyAvg = []
ContactOperatorQueueAvg = []
FinanceQueueTimeAvg = []
ContactQueueTimeAvg = []
EndingTime = []

# Modify the Finance_Arrival function to record entry time in the queue
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
        Call.EntryTime = SimClasses.Clock  # Record the time call enters the queue
        FinanceOperatorQueue.Add(Call)

# Modify the FinanceEndOfService function to record time spent in queue
def FinanceEndOfService(DepartingCall):
    '''Called when a financial call finishes service.'''
    TIS = SimClasses.Clock - DepartingCall.CreateTime
    FinanceTIS.Record(TIS)
    FinanceWithin5.Record((TIS < 5))

    if FinanceOperatorQueue.NumQueue() > 0 and FinanceOperator.NumberOfUnits >= FinanceOperator.CurrentNumBusy:
        NextCall = FinanceOperatorQueue.Remove()
        QueueTime = SimClasses.Clock - NextCall.EntryTime  # Calculate queue time
        FinanceQueueTime.Record(QueueTime)  # Record time spent in queue
        SimFunctions.SchedulePlus(Calendar, "FinanceEndOfService", SimRNG.Erlang(2, FinMean, 2), NextCall)
    else:
        FinanceOperator.Free(1)

# Modify the Contact_Arrival function to record entry time in the queue
def Contact_Arrival():
    '''Handles arrival of contact management calls to the contact operators.'''
    cInterarrivalTime = 1 / (1 * 0.41)  # 41% of calls are contact management
    if SimClasses.Clock + cInterarrivalTime > RunLength:
        return
    SimFunctions.Schedule(Calendar, "Contact_Arrival", cInterarrivalTime)

    Call = SimClasses.Entity()
    if ContactOperator.CurrentNumBusy < ContactOperator.NumberOfUnits:
        ContactOperator.Seize(1)
        SimFunctions.SchedulePlus(Calendar, "ContactEndOfService", SimRNG.Erlang(3, ContactMean, 3), Call)
    else:
        Call.EntryTime = SimClasses.Clock  # Record the time call enters the queue
        ContactOperatorQueue.Add(Call)

# Modify the ContactEndOfService function to record time spent in queue
def ContactEndOfService(DepartingCall):
    '''Called when a contact management call finishes service.'''
    TIS = SimClasses.Clock - DepartingCall.CreateTime
    ContactTIS.Record(TIS)
    ContactWithin5.Record((TIS < 5))

    if ContactOperatorQueue.NumQueue() > 0 and ContactOperator.NumberOfUnits >= ContactOperator.CurrentNumBusy:
        NextCall = ContactOperatorQueue.Remove()
        QueueTime = SimClasses.Clock - NextCall.EntryTime  # Calculate queue time
        ContactQueueTime.Record(QueueTime)  # Record time spent in queue
        SimFunctions.SchedulePlus(Calendar, "ContactEndOfService", SimRNG.Erlang(3, ContactMean, 3), NextCall)
    else:
        ContactOperator.Free(1)
 
# Run simulation for each replication
for reps in range(0,NumReps):
    # Initialize
    SimFunctions.SimFunctionsInit(Calendar)
    FinanceOperator.SetUnits(NumFinanceOperators)
    ContactOperator.SetUnits(NumContactOperators)
    SimFunctions.Schedule(Calendar, "Finance_Arrival", 1 / (1 * 0.59))
    SimFunctions.Schedule(Calendar, "Contact_Arrival", 1 / (1 * 0.41))

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
    FinanceOperatorQueueAvg.append(FinanceOperatorQueue.Mean())
    # FinancePropWithin5.append(FinanceWithin5.Mean())
    ContactTISavg.append(ContactTIS.Mean())
    ContactOperatorQueueAvg.append(ContactOperatorQueue.Mean())
    # ContactPropWithin5.append(ContactWithin5.Mean())
    FinanceOperatorBusyAvg.append(FinanceOperator.Mean())
    ContactOperatorBusyAvg.append(ContactOperator.Mean())
    EndingTime.append(SimClasses.Clock)
    FinanceQueueTimeAvg.append(FinanceQueueTime.Mean())
    ContactQueueTimeAvg.append(ContactQueueTime.Mean())

# Output results to a CSV
output = pd.DataFrame({
    "FinanceTISavg": FinanceTISavg,
    "FinanceOperatorQueueAvg": FinanceOperatorQueueAvg,
    "FinanceOperatorBusyAvg": FinanceOperatorBusyAvg,
    "ContactTISavg": ContactTISavg,
    "ContactOperatorQueueAvg": ContactOperatorQueueAvg,
    "ContactOperatorBusyAvg": ContactOperatorBusyAvg,
    # "FinancePropWithin5": FinancePropWithin5,
    # "ContactPropWithin5": ContactPropWithin5,
    "FinanceQueueTimeAvg": FinanceQueueTimeAvg,
    "ContactQueueTimeAvg": ContactQueueTimeAvg,
    "EndingTime": EndingTime
})
output.to_csv("current_system_output.csv", sep=",")
print("Means")
print(output.mean())
print("95% CI Half-Width")
print(1.96 * np.sqrt(output.var(ddof=0) / len(output)))