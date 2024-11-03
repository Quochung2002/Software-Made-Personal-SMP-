# Software-Made-Personal-SMP

Software Made Personal (SMP) customizes software products in two areas: financial tracking and contact management. They currently have a customer support call center that handles technical questions for owners of their software from the hours of 8 AM to 4 PM Eastern Time.

When a customer calls 888-555-4SMP, they listen to a recording that asks them to select among the two product lines (historically, 59% financial products and 41% contact management products). The number of customers who can be connected at any one time is essentially unlimited. Each product line has its own operators. If an appropriate operator is available, then the call is immediately routed to the operator; if an appropriate operator is not available, then the caller is placed in a hold queue (and listens to a combination of music and ads). SMP has observed that hang-ups very rarely happen.

SMP is hoping to reduce the total number of operators they need by cross-training operators so that they can answer calls for any product line. Since the operators will not be experts across all products, this is expected to increase the time to process a call by about 10%. The question that SMP has asked you to answer is how many cross-trained operators are needed to provide service at the same level as the current system.

Incoming calls can be modeled as a Poisson arrival process with a rate of 60 per hour. The mean time required for an operator to answer a question is 5 minutes, with the actual time being Erlang-2 for financial calls, and Erlang-3 for contact management calls. The current assignment of operators is as follows:

                                                     
-----------------------------------------------------
Current number of operators        financial      4
                                   contact mgmt   3
-----------------------------------------------------
 
