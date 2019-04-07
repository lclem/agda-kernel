from ipykernel.kernelapp import IPKernelApp
from .kernel import AgdaKernel

IPKernelApp.launch_instance(kernel_class=AgdaKernel)