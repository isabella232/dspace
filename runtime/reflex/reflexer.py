from collections import defaultdict
from typing import Union, Callable, Set, List
import pyjq


class Reflex:
    def __init__(self,
                 condition: Union[str, bool], action: Union[str, Callable],
                 priority: int = 0):
        self.condition = condition
        self.action = action
        # less than 0 means disabled; otherwise the larger the higher-priority
        self.priority = priority
        self.status = ""


class Reflexer:
    def __init__(self):
        # reflexes keyed by name
        self.rfs = dict()

    @staticmethod
    def execute(rf: Reflex):
        if callable(rf.action):
            rf.action()
        elif type(rf.action) is str:
            pass

    def add(self, name: str, reflex: Reflex):
        self.rfs[name] = reflex

    def remove(self, name):
        return self.rfs.pop(name, None)

    def poll(self, names=Set[str]):
        """Iterate over all reflexes and execute them based on priority;
        the low priority ones will be executed first.

        TBD: compile an execution plan with better conflict resolution
        """
        exec_plan = list()
        for n, rf in self.rfs.items():
            if n in names:
                exec_plan.append((rf.priority, n, rf))
        exec_plan = sorted(exec_plan, key=lambda x: x[0], reverse=True)

        for p, _, rf in exec_plan:
            if p < 0:
                pass
            self.execute(rf)


def main():
    pass


if __name__ == '__main__':
    main()
