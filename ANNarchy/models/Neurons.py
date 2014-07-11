from ANNarchy.core.Neuron import Neuron


##################
### Izhikevich
##################
class IzhikevichClass(Neuron):
    """ 
    Izhikevich neuron.

        du/dt = 0.04 * v^2 + 5.0 * v + 140.0 - u + I 

        du/dt = a * (b * v - u) 

    By default, the conductance is "g_exc - g_inh", but this can be changed with the ``conductance`` method::

        neuron = Izhikevich.conductance('g_ampa * (1 + g_nmda) - g_gaba')

    The synapses are instantaneous, i.e the corresponding conductance is increased from the synaptic effeciency w at the time step when a spike is received.

    Parameters:

    * a = 0.2 : Speed of the recovery variable
    * b = 0.2: Scaling of the recovery variable
    * c = -65.0 : Reset potential.
    * d = 2.0 : Increment of the recovery variable after a spike.
    * v_thresh = 30.0 : Spike threshold (mV).
    * i_offset = 0.0 : external current (nA).
    * noise = 0.0 : Amplitude of the normal additive noise.
    * tau_refrac = 0.0 : Duration of refractory period (ms).

    Variables:

    * I : input current (user-defined conductance/current + external current + normal noise).

        I = conductance + i_offset + noise * Normal(0.0, 1.0)

    * v : membrane potential in mV (init=-65.0).

        dv/dt = 0.04 * v^2 + 5.0 * v + 140.0 - u + I 

    * u : recovery variable (init=0.0).

        du/dt = a * (b*v - u) 

    Spike emission:

        v > v_thresh

    Reset:

        v = c
        u += d : unless_refractory 

    The ODEs are solved using the explicit Euler method.
    """
    def __init__(self, conductance="g_exc - g_inh"):
        # Extract which targets are defined in the conductance
        import re
        targets = re.findall(r'g_([\w]+)', conductance)
        # Create the arguments
        parameters = """
    noise = 0.0
    a = 0.02
    b = 0.2
    c = -65.0
    d = 2.0 
    v_thresh = 30.0
    i_offset = 0.0
"""
        # Equations for the variables
        equations="""
    I = %(conductance)s + noise * Normal(0.0, 1.0) + i_offset
    dv/dt = 0.04 * v^2 + 5.0 * v + 140.0 - u + I : init = -65.0
    du/dt = a * (b*v - u) 
""" % { 'conductance' : conductance }

        # Default behavior for the conductances (avoid warning)
        for target in targets:
            equations += """
    g_%(target)s = 0.0""" % {'target' : target}

        spike = """
    v >= v_thresh
"""
        reset = """
    v = c
    u += d: unless_refractory
"""
        Neuron.__init__(self, parameters=parameters, equations=equations, spike=spike, reset=reset, refractory='tau_refrac')

    def conductance(self, conductance):
        """
        Sets the input current or conductance in the equation of I.

        Default: "g_exc - g_inh"
        """
        return IzhikevichClass(conductance=conductance)

    def __repr__(self):
        return self.__doc__




##################
### IF neurons
##################
class IF_curr_expClass(Neuron):
    """ 
    IF_curr_exp neuron.

    Leaky integrate and fire model with fixed threshold and decaying-exponential post-synaptic current. (Separate synaptic currents for excitatory and inhibitory synapses).

    Parameters:

    * v_rest = -65.0 :  Resting membrane potential (mV)
    * cm  = 1.0 : Capacity of the membrane (nF)
    * tau_m  = 20.0 : Membrane time constant (ms)
    * tau_refrac = 0.0 : Duration of refractory period (ms)
    * tau_syn_E = 5.0 : Decay time of excitatory synaptic current (ms)
    * tau_syn_I = 5.0 : Decay time of inhibitory synaptic current (ms)
    * i_offset = 0.0 : Offset current (nA)
    * v_reset = -65.0 : Reset potential after a spike (mV)
    * v_thresh = -50.0 : Spike threshold (mV)

    Variables:

    * v : membrane potential in mV (init=-65.0).

        cm * dv/dt = cm/tau_m*(v_rest -v)   + g_exc - g_inh + i_offset

    * g_exc : excitatory current (init = 0.0)

        tau_syn_E * dg_exc/dt = - g_exc

    * g_inh : inhibitory current (init = 0.0)

        tau_syn_I * dg_inh/dt = - g_inh


    Spike emission:

        v > v_thresh

    Reset:

        v = v_reset

    The ODEs are solved using the exponential Euler method.
"""
    def __init__(self):
        # Create the arguments
        parameters = """
    v_rest = -65.0
    cm  = 1.0
    tau_m  = 20.0
    tau_refrac = 0.0
    tau_syn_E = 5.0
    tau_syn_I = 5.0
    v_thresh = -50.0
    v_reset = -65.0
    i_offset = 0.0
"""
        # Equations for the variables
        equations="""    
    cm * dv/dt = cm/tau_m*(v_rest -v)   + g_exc - g_inh + i_offset : exponential, init=-65.0
    tau_syn_E * dg_exc/dt = - g_exc : exponential
    tau_syn_I * dg_inh/dt = - g_inh : exponential
""" 

        spike = """
    v >= v_thresh
"""
        reset = """
    v = v_reset
"""
        Neuron.__init__(self, parameters=parameters, equations=equations, spike=spike, reset=reset, refractory='tau_refrac')

    def __repr__(self):
        return self.__doc__

class IF_cond_expClass(Neuron):
    """ 
    IF_cond_exp neuron.

    Leaky integrate and fire model with fixed threshold and decaying-exponential post-synaptic conductance.

    Parameters:

    * v_rest = -65.0 :  Resting membrane potential (mV)
    * cm  = 1.0 : Capacity of the membrane (nF)
    * tau_m  = 20.0 : Membrane time constant (ms)
    * tau_refrac = 0.0 : Duration of refractory period (ms)
    * tau_syn_E = 5.0 : Decay time of excitatory synaptic current (ms)
    * tau_syn_I = 5.0 : Decay time of inhibitory synaptic current (ms)
    * e_rev_E = 0.0 : Reversal potential for excitatory input (mV)
    * e_rev_I = -70.0 : Reversal potential for inhibitory input (mv)
    * i_offset = 0.0 : Offset current (nA)
    * v_reset = -65.0 : Reset potential after a spike (mV)
    * v_thresh = -50.0 : Spike threshold (mV)

    Variables:

    * v : membrane potential in mV (init=-65.0).

        cm * dv/dt = cm/tau_m*(v_rest -v)  + g_exc * (e_rev_E - v) + g_inh * (e_rev_I - v) + i_offset

    * g_exc : excitatory current (init = 0.0)

        tau_syn_E * dg_exc/dt = - g_exc

    * g_inh : inhibitory current (init = 0.0)

        tau_syn_I * dg_inh/dt = - g_inh


    Spike emission:

        v > v_thresh

    Reset:

        v = v_reset

    The ODEs are solved using the exponential Euler method.
"""
    def __init__(self):
        # Create the arguments
        parameters = """
    v_rest = -65.0
    cm  = 1.0
    tau_m  = 20.0
    tau_refrac = 0.0
    tau_syn_E = 5.0
    tau_syn_I = 5.0
    e_rev_E = 0.0 
    e_rev_I = -70.0
    v_thresh = -50.0
    v_reset = -65.0
    i_offset = 0.0
"""
        # Equations for the variables
        equations="""    
    cm * dv/dt = cm/tau_m*(v_rest -v)   + g_exc * (e_rev_E - v) + g_inh * (e_rev_I - v) + i_offset : exponential, init=-65.0
    tau_syn_E * dg_exc/dt = - g_exc : exponential
    tau_syn_I * dg_inh/dt = - g_inh : exponential
"""

        spike = """
    v >= v_thresh
"""
        reset = """
    v = v_reset
"""
        Neuron.__init__(self, parameters=parameters, equations=equations, spike=spike, reset=reset, refractory='tau_refrac')

    def __repr__(self):
        return self.__doc__

# Alpha conductances
class IF_curr_alphaClass(Neuron):
    """ 
    IF_curr_alpha neuron.

    Leaky integrate and fire model with fixed threshold and alpha post-synaptic current. (Separate synaptic currents for excitatory and inhibitory synapses).

    The alpha currents are calculated through a system of two linears ODEs. After a spike is received at t_spike, it peaks at t_spike + tau_syn_X, with a maximum equal to the synaptic efficiency.

    Parameters:

    * v_rest = -65.0 :  Resting membrane potential (mV)
    * cm  = 1.0 : Capacity of the membrane (nF)
    * tau_m  = 20.0 : Membrane time constant (ms)
    * tau_refrac = 0.0 : Duration of refractory period (ms)
    * tau_syn_E = 5.0 : Rise time of excitatory synaptic current (ms)
    * tau_syn_I = 5.0 : Rise time of inhibitory synaptic current (ms)
    * i_offset = 0.0 : Offset current (nA)
    * v_reset = -65.0 : Reset potential after a spike (mV)
    * v_thresh = -50.0 : Spike threshold (mV)

    Variables:

    * v : membrane potential in mV (init=-65.0).

        cm * dv/dt = cm/tau_m*(v_rest -v) + alpha_exc - alpha_inh + i_offset

    * g_exc : excitatory current (init = 0.0)

        tau_syn_E * dg_exc/dt = - g_exc

    * alpha_exc : alpha function of excitatory current (init = 0.0)

        tau_syn_E * dalpha_exc/dt = exp((tau_syn_E - dt/2.0)/tau_syn_E) * g_exc - alpha_exc

    * g_inh : inhibitory current (init = 0.0)

        tau_syn_I * dg_inh/dt = - g_inh

    * alpha_inh : alpha function of inhibitory current (init = 0.0)

        tau_syn_I * dalpha_inh/dt = exp((tau_syn_I - dt/2.0)/tau_syn_I) * g_inh - alpha_inh


    Spike emission:

        v > v_thresh

    Reset:

        v = v_reset

    The ODEs are solved using the exponential Euler method.
"""
    def __init__(self):
        # Create the arguments
        parameters = """
    v_rest = -65.0
    cm  = 1.0
    tau_m  = 20.0
    tau_refrac = 0.0
    tau_syn_E = 5.0
    tau_syn_I = 5.0
    v_thresh = -50.0
    v_reset = -65.0
    i_offset = 0.0
"""
        # Equations for the variables
        equations="""  
    gmax_exc = exp((tau_syn_E - dt/2.0)/tau_syn_E)
    gmax_inh = exp((tau_syn_I - dt/2.0)/tau_syn_I)  
    cm * dv/dt = cm/tau_m*(v_rest -v)   + alpha_exc - alpha_inh + i_offset : exponential, init=-65.0
    tau_syn_E * dg_exc/dt = - g_exc : exponential
    tau_syn_I * dg_inh/dt = - g_inh : exponential
    tau_syn_E * dalpha_exc/dt = gmax_exc * g_exc - alpha_exc  : exponential
    tau_syn_I * dalpha_inh/dt = gmax_inh * g_inh - alpha_inh  : exponential
""" 

        spike = """
    v >= v_thresh
"""
        reset = """
    v = v_reset
"""
        Neuron.__init__(self, parameters=parameters, equations=equations, spike=spike, reset=reset, refractory='tau_refrac')

    def __repr__(self):
        return self.__doc__

class IF_cond_alphaClass(Neuron):
    """ 
    IF_cond_exp neuron.

    Leaky integrate and fire model with fixed threshold and decaying-exponential post-synaptic conductance.

    Parameters:

    * v_rest = -65.0 :  Resting membrane potential (mV)
    * cm  = 1.0 : Capacity of the membrane (nF)
    * tau_m  = 20.0 : Membrane time constant (ms)
    * tau_refrac = 0.0 : Duration of refractory period (ms)
    * tau_syn_E = 5.0 : Rise time of excitatory synaptic current (ms)
    * tau_syn_I = 5.0 : Rise time of inhibitory synaptic current (ms)
    * e_rev_E = 0.0 : Reversal potential for excitatory input (mV)
    * e_rev_I = -70.0 : Reversal potential for inhibitory input (mv)
    * i_offset = 0.0 : Offset current (nA)
    * v_reset = -65.0 : Reset potential after a spike (mV)
    * v_thresh = -50.0 : Spike threshold (mV)

    Variables:

    * v : membrane potential in mV (init=-65.0).

        cm * dv/dt = cm/tau_m*(v_rest -v)  + alpha_exc * (e_rev_E - v) + alpha_inh * (e_rev_I - v) + i_offset

    * g_exc : excitatory conductance (init = 0.0)

        tau_syn_E * dg_exc/dt = - g_exc

    * alpha_exc : alpha function of excitatory conductance (init = 0.0)

        tau_syn_E * dalpha_exc/dt = exp((tau_syn_E - dt/2.0)/tau_syn_E) * g_exc - alpha_exc

    * g_inh : inhibitory conductance (init = 0.0)

        tau_syn_I * dg_inh/dt = - g_inh

    * alpha_inh : alpha function of inhibitory current (init = 0.0)

        tau_syn_I * dalpha_inh/dt = exp((tau_syn_I - dt/2.0)/tau_syn_I) * g_inh - alpha_inh


    Spike emission:

        v > v_thresh

    Reset:

        v = v_reset

    The ODEs are solved using the exponential Euler method.
"""
    def __init__(self):
        # Create the arguments
        parameters = """
    v_rest = -65.0
    cm  = 1.0
    tau_m  = 20.0
    tau_refrac = 0.0
    tau_syn_E = 5.0
    tau_syn_I = 5.0
    e_rev_E = 0.0 
    e_rev_I = -70.0
    v_thresh = -50.0
    v_reset = -65.0
    i_offset = 0.0
"""
        # Equations for the variables
        equations="""    
    gmax_exc = exp((tau_syn_E - dt/2.0)/tau_syn_E)
    gmax_inh = exp((tau_syn_I - dt/2.0)/tau_syn_I)
    cm * dv/dt = cm/tau_m*(v_rest -v)   + alpha_exc * (e_rev_E - v) + alpha_inh * (e_rev_I - v) + i_offset : exponential, init=-65.0
    tau_syn_E * dg_exc/dt = - g_exc : exponential
    tau_syn_I * dg_inh/dt = - g_inh : exponential
    tau_syn_E * dalpha_exc/dt = gmax_exc * g_exc - alpha_exc  : exponential
    tau_syn_I * dalpha_inh/dt = gmax_inh * g_inh - alpha_inh  : exponential
"""

        spike = """
    v >= v_thresh
"""
        reset = """
    v = v_reset
"""
        Neuron.__init__(self, parameters=parameters, equations=equations, spike=spike, reset=reset, refractory='tau_refrac')

    def __repr__(self):
        return self.__doc__


##################
### Neuron instances
##################
Izhikevich = IzhikevichClass()
IF_curr_exp = IF_curr_expClass()
IF_cond_exp = IF_cond_expClass()
IF_curr_alpha = IF_curr_alphaClass()
IF_cond_alpha = IF_cond_alphaClass()