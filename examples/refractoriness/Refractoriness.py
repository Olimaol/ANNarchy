#
#   ANNarchy - SimpleSTDP
#
#   A simple model showing the usage of refractoriness in ANNarchy
# 
#   See e.g. Mainen & Sejnowski (1995) for experimental results in vitro.
#
#   Code adapted from the Brian example: https://brian2.readthedocs.org/en/latest/examples/non_reliability.html
#
#   authors: Helge Uelo Dinkelbach, Julien Vitay
#
from ANNarchy import *
from ANNarchy.extensions.poisson import PoissonPopulation

Neuron = SpikeNeuron(
parameters = """
    tau = 20.0 : population
    sigma = 0.015
""",
equations = """
    dx/dt = (1.1 - x) / tau + sigma * ( ( 2.0 / tau ) ** 0.5 ) * x
""",
spike = """
    x > 1
""",
reset = """
    x = 0
""",
refractory = 5.0
)

pop = Population( geometry=(25,), neuron = Neuron )

compile()

simulate ( 500.0 )

spikes = pop.raster_plot()
# Plot the results
import pylab as plt
plt.plot(spikes[:, 0], spikes[:, 1], '.')
plt.show()
