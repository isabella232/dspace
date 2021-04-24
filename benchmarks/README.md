Latency breakdown (local)
--

Setup: 
* Digi-graph: parent (room) - child (lamp, stub) - physical lamp (lifx)
* Send a single request updating the room's control.brightness.intent
* Repeat it K times and collect metrics (below)
* Runtime (apiserver, etcd, digis) and the cli are run locally on the same machine

Metrics: 
* E2E latency: time between client send a request to update an intent until the client sees the status is set equal to the intent
* Request latency: time to complete and respond to a client request
* Time-to-fulfillment (TTF): time it takes to full-fill/reconcile an intent
* Forward propagation time (FPT): time for intent to reach the device
* Backward propagation time (BPT): time for status to reach the root digi
* Device actuation time (DT): time for the device to actuate according to the set-point

> TTF = FPT + BPT + DT

Methods:
* E2E latency: measured at the CLI, from the request submission to the status update (both at the parent)
* Request latency: measured at the CLI, from the request submission to the response
* TTF: E2E latency - request latency
* FPT:  


Remote deployment
--

Setup:
* Same as the local setup except the runtime components run in the cloud (cli still local)
* Add bandwidth-heavy digis, cam and scene: 

```
parent (room) - child (lamp) 
              \ child (cam) 
                        |
              \ child (scene)
```

Metrics:
* Same as local; plus:
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
* Digi-graph: { parent (room) - child (lamp, mock mode) } x N
* Send N concurrent requests each updating a unique room's control.brightness.intent
* Report the E2E latencies

HL abstraction scalability
--

Setup:
* Digi-graph: parent (city) - child (digit) x N
* TBD

