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

TBD: python operator with kopf
