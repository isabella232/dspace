Piper
==

The `pipe controller` (piper) syncs data from an output port to an input port. It creates a `kind: Match` sync binding behind the scene.

```
apiVersion: ..
kind: Pipe
spec:
    source: [AURI]
    target: [AURI]
    mode: [] 
```

TBD: current implementation of `dq pipe` creates syncs directly and does not perform single-writer-per-port check (nor does the sync controller). Like mount, such check should be performed by the piper's admission controller. 

TBD: in the long run, both mount and pipe should be made first-class verbs of the apiserver. 
