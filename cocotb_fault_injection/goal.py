import abc


class InjectionGoal(metaclass=abc.ABCMeta):
    def __init__(self):
        pass

    @abc.abstractmethod
    def eval(self, faults, num_nodes):
        pass


class InfiniteInjection(InjectionGoal):
    def eval(self, faults, num_nodes):
        return False


class TotalSEEs(InjectionGoal):
    def __init__(self, total_sees):
        self._total_sees = total_sees

    def eval(self, faults, num_nodes):
        return faults >= self._total_sees


class SEEsPerNode(InjectionGoal):
    def __init__(self, see_per_node):
        self._see_per_node = see_per_node

    def eval(self, faults, num_nodes):
        return faults >= self._see_per_node * num_nodes
