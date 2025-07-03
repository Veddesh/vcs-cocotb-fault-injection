import abc
import random


class _SEE:
    pass


class _SET(_SEE):
    def __init__(self, signal_handle, signal_index):
        self.signal_handle = signal_handle
        self.signal_index = signal_index
        self.oldval = 0  # Used in RMW


class _SEU(_SEE):
    def __init__(self, signal_spec, signal_index):
        self.signal_spec = signal_spec
        self.signal_index = signal_index


class InjectionStrategy(metaclass=abc.ABCMeta):
    def __init__(self, enable_seu=True, enable_set=True):
        self._enable_seu = enable_seu
        self._enable_set = enable_set
        if not any([self._enable_set, self._enable_seu]):
            raise AttributeError("Invalid strategy: must enable SEU, SET, or both.")

    @abc.abstractmethod
    def __iter__(self):
        pass

    def initialize(self, seu_signals, set_signals):
        self._seu_signals = seu_signals
        self._set_signals = set_signals


class SequentialInjectionStrategy(InjectionStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __iter__(self):
        while True:
            if self._enable_set:
                for sig in self._set_signals:
                    for index in range(len(sig)):
                        yield [_SET(sig, index)]
            if self._enable_seu:
                for sig in self._seu_signals:
                    for index in range(len(sig["handle"])):
                        yield [_SEU(sig, index)]


def _random_index(sig):
    if hasattr(sig, "_range") and sig._range:
        return random.randint(min(sig._range), max(sig._range))
    return 0


class RandomInjectionStrategy(InjectionStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __iter__(self):
        if self._enable_seu and self._enable_set:
            total = len(self._seu_signals) + len(self._set_signals)
            while True:
                if random.randint(0, total - 1) < len(self._set_signals):
                    sig = random.choice(self._set_signals)
                    yield [_SET(sig, _random_index(sig))]
                else:
                    sig = random.choice(self._seu_signals)
                    yield [_SEU(sig, _random_index(sig["handle"]))]
        elif self._enable_set:
            while True:
                sig = random.choice(self._set_signals)
                yield [_SET(sig, _random_index(sig))]
        elif self._enable_seu:
            while True:
                sig = random.choice(self._seu_signals)
                yield [_SEU(sig, _random_index(sig["handle"]))]
