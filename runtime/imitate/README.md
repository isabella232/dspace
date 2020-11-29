#Imitate

The `imitator` meta actor implements logic to learn how a driver/app. actors makes decision. This package includes the following imitator implementations:
* _Native_: keeps track of what actions are performed under what condition and by what frequency; if the frequency exceeds a threshold, the action will be performed automatically in future. A wrong action (that a correction follows immediately) results in the memoization table to be reset.
* _Behavior cloning_: TBD 
* _Advanced RL_: TBD

The imitator is implemented in [kopf](https://github.com/nolar/kopf).