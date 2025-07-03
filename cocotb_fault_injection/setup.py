from setuptools import setup

setup(
    name='cocotb_fault_injection',
    version='0.2',
    description='Fault injection functionality for cocotb using yosys JSON',
    author='Updated by Veddesh RGM based on CERN original',
    packages=['cocotb_fault_injection'],
    install_requires=['cocotb'],
)
