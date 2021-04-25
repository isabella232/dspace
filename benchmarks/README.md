Latency breakdown (local)
--

Setup: 
* Digi-graph:
```
parent (room) - child (lamp) - physical lamp   (lifx, geeni)
              \ child (cam)  - physical camera (wyze)
                        |
              \ child (scene) 
```
* Send a single request updating the room's control.brightness.intent
* Repeat it K times and collect metrics (below)
* Runtime (apiserver, etcd, digis) and the cli are run locally on the same machine

Metrics: 
* E2E latency (E2E): time between client send a request to update an intent until the client sees the status is set equal to the intent
* Request latency (RT): time to complete and respond to a client request
* Time-to-fulfillment (TTF): time it takes to full-fill/reconcile an intent
* Forward propagation time (FPT): time for intent to reach the device
* Backward propagation time (BPT): time for status to reach the root digi
* Device actuation time (DT): time for the device to actuate according to the set-point

> TTF = FPT + BPT + DT

Methods:
* E2E: measured at the CLI, the elapsed time between the request submission to the status update (both at the parent)
* RT: measured at the CLI, the elapsed time betwen the request submission to receiving the response
* FPT: measure the timestamps at the root (when the intent is written) and the leaf digi (after setting the device's setpoint)
* BPT: measure the timestamps at the leaf (when the status update is received at the device) and the root digi (after setting the root's status)
* DT: measure at the leaf digi for the elapsed time between setting the device setpoint and receiving its status update


Remote deployment
--

Setup:
* Same as the local setup except the runtime components run in the cloud (cli still local)

Metrics:
* Same as in the local setup; plus:
* Network latency (in-band or out-of-band/ping measurements)
* Bandwidth consumption (total bytes), measured at the network interface on the cloud machine

Hybrid deployment
--

Setup
* Same as the remote setup except the cam and scene digis are run on-prem/locally

Metrics:
* Same as the remote setup

 
Throughput (local)
--

Setup:
* Digi-graph:
```
parent (room1) - child (mock lamp1)
parent (room2) - child (mock lamp2)
... x N
```
* Send N concurrent requests each updating a unique room's control.brightness.intent
* Report the E2E latencies

HL abstraction scalability
--

Setup:
* Digi-graph: parent (city) - child (digit) x N
```
parent (room) - child (mock lamp1)
              \ child (mock lamp2)
              ... x N
              \ child (mock lampN)
```
* TBD

