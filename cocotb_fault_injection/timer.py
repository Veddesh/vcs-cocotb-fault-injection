import random

from cocotb.simulator import register_timed_callback
from cocotb.triggers import GPITrigger, Trigger
from cocotb.utils import get_sim_steps


class PoissonTimer(GPITrigger):
    def __init__(self, mttf, units=None):
        GPITrigger.__init__(self)
        self._mttf = mttf
        self._units = units

    def prime(self, callback):
        duration = random.expovariate(1.0 / self._mttf)
        self.sim_steps = get_sim_steps(max(int(duration), 1), self._units)
        if self.cbhdl is None:
            self.cbhdl = register_timed_callback(self.sim_steps, callback, self)
        if self.cbhdl is None:
            raise RuntimeError(f"Failed to register {str(self)}")
        Trigger.prime(self, callback)

    def __str__(self):
        return f"PoissonTimer(mttf={self._mttf} {self._units})"


class BoundedRandomTimer(GPITrigger):
    def __init__(self, mttf_min, mttf_max, units=None):
        GPITrigger.__init__(self)
        self._mttf_min = mttf_min
        self._mttf_max = mttf_max
        self._units = units

    def prime(self, callback):
        duration = random.randint(self._mttf_min, self._mttf_max)
        self.sim_steps = get_sim_steps(max(int(duration), 1), self._units)
        if self.cbhdl is None:
            self.cbhdl = register_timed_callback(self.sim_steps, callback, self)
        if self.cbhdl is None:
            raise RuntimeError(f"Failed to register {str(self)}")
        Trigger.prime(self, callback)

    def __str__(self):
        avg = (self._mttf_min + self._mttf_max) / 2
        return f"BoundedRandomTimer(avg={avg} {self._units})"
