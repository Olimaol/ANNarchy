# Header for a rate dendrite.
# 
# Depends on:
# 
#     * name : the class name (e.g. Projection1)
#    
#     * access : public access methods for all parameters and variables
#    
#     * global_ops_access : access to the global operations (min, max, mean, etc)
#    
#     * global_ops_method : methods for the global operations (min, max, mean, etc)
#    
#     * member : private definition of parameters and variables    
#    
#     * random : private definition of RandomDistribution arrays   
#    
#     * functions : inline definition of custom functions     
rate_projection_header = \
"""#ifndef __%(class)s_H__
#define __%(class)s_H__

#include "Global.h"
#include "Includes.h"
#include "RateDendrite.h"

class %(class)s : public RateDendrite 
{
public:
    %(class)s(Population* pre, Population* post, int postRank, int target);
    
    %(class)s(int preID, int postID, int postRank, int target);
    
    ~%(class)s();
    
    class Population* getPrePopulation() { return static_cast<Population*>(pre_population_); }
    
    int getSynapseCount() { return nbSynapses_; }
    
    int addSynapse(int rank, DATA_TYPE value, int delay);

    int removeSynapse(int rank);
    
    int removeAllSynapses();
    
    void initValues();
    
    void computeSum();
    
    void globalLearn();
    
    void localLearn();

    void record();

%(access)s

%(functions)s

private:
%(member)s

    %(pre_name)s* pre_population_;
    %(post_name)s* post_population_;
};
#endif
""" 

# Header for a spike dendrite.
# 
# Depends on:
# 
#     * name : the class name (e.g. Projection1)
#    
#     * access : public access methods for all parameters and variables
#    
#     * global_ops_access : access to the global operations (min, max, mean, etc)
#    
#     * global_ops_method : methods for the global operations (min, max, mean, etc)
#    
#     * member : private definition of parameters and variables    
#    
#     * random : private definition of RandomDistribution arrays  
#    
#     * functions : inline definition of custom functions      
spike_projection_header = \
"""#ifndef __%(class)s_H__
#define __%(class)s_H__

#include "Global.h"
#include "Includes.h"
#include "SpikeDendrite.h"

class %(class)s : public SpikeDendrite 
{
public:
    %(class)s(Population* pre, Population* post, int postRank, int target);
    
    %(class)s(int preID, int postID, int postRank, int target);
    
    ~%(class)s();
    
    class Population* getPrePopulation() { return static_cast<Population*>(pre_population_); }

    int getSynapseCount() { return nbSynapses_; }

    int addSynapse(int rank, DATA_TYPE value, int delay);

    int removeSynapse(int rank);
    
    int removeAllSynapses();
    
    void initValues();
    
    void computeSum();
    
    void globalLearn();
    
    void localLearn();

    void preEvent(int rank);
    
    void postEvent();
    
    bool isPreSynaptic(Population* pop) { return pop == static_cast<Population*>(pre_population_); }
        
    void record();
    
%(access)s

%(functions)s

private:
%(member)s

    %(pre_name)s* pre_population_;
    %(post_name)s* post_population_;
};
#endif
"""

# Body for a rate projection
#
# Depends on:
#
#    * class : the class name
#
#    * destructor : code for the destructor where all variables are freed
# 
#    * pre_type : name of class of the presynaptic population
# 
#    * post_type : name of class of the presynaptic population
# 
#    * init : initial values for parameters and variables
# 
#    * local : code for local_learn 
#
#    * global : code for global_learn
#
rate_projection_body = \
"""#include "%(class)s.h"        
#include "Global.h"

%(add_include)s

using namespace ANNarchy_Global;

%(class)s::%(class)s(Population* pre, Population* post, int postRank, int target) : RateDendrite() 
{
    pre_population_ = static_cast<%(pre_type)s*>(pre);
    post_population_ = static_cast<%(post_type)s*>(post);
    
    pre_rates_ = pre_population_->getRates();
    post_rates_ = post_population_->getRates();

    target_ = target;
    post_neuron_rank_ = postRank;
}

%(class)s::%(class)s(int preID, int postID, int postRank, int target) : RateDendrite() 
{
    pre_population_ = static_cast<%(pre_type)s*>(Network::instance()->getPopulation(preID));
    post_population_ = static_cast<%(post_type)s*>(Network::instance()->getPopulation(postID));

    pre_rates_ = pre_population_->getRates();
    post_rates_ = post_population_->getRates();

    target_ = target;
    post_neuron_rank_ = postRank;
}

%(class)s::~%(class)s() 
{
#ifdef _DEBUG
    std::cout <<"%(class)s::Destructor"<< std::endl;
#endif

%(destructor)s
}

int %(class)s::addSynapse(int rank, DATA_TYPE value, int delay)
{
%(add_synapse_body)s
}

int %(class)s::removeSynapse(int rank)
{
%(rem_synapse_body)s
}

int %(class)s::removeAllSynapses()
{
%(rem_all_synapse_body)s
}

void %(class)s::initValues() 
{
%(init)s
}

void %(class)s::computeSum() 
{   
%(sum)s
}

void %(class)s::localLearn() 
{
%(local)s
}

void %(class)s::globalLearn() 
{
%(global)s
}

void %(class)s::record() 
{
%(record)s
}
"""

# Body for a Spike projection
#
# Depends on:
#
#    * class : the class name
#
#    * destructor : code for the destructor where all variables are freed
# 
#    * pre_type : name of class of the presynaptic population
# 
#    * post_type : name of class of the presynaptic population
# 
#    * init : initial values for parameters and variables
# 
#    * local : code for local_learn 
#
#    * global : code for global_learn
#
spike_projection_body = \
"""#include "%(class)s.h"        
#include "Global.h"

%(add_include)s

using namespace ANNarchy_Global;
        
%(class)s::%(class)s(Population* pre, Population* post, int postRank, int target) : SpikeDendrite() 
{
    pre_population_ = static_cast<%(pre_type)s*>(pre);
    post_population_ = static_cast<%(post_type)s*>(post);

    target_ = target;
    post_neuron_rank_ = postRank;
    
    post_population_->getProjection(pre, target)->addDendrite(postRank, this);
    pre_population_->addSpikeTarget(this);
}

%(class)s::%(class)s(int preID, int postID, int postRank, int target) : SpikeDendrite() 
{
    pre_population_ = static_cast<%(pre_type)s*>(Network::instance()->getPopulation(preID));
    post_population_ = static_cast<%(post_type)s*>(Network::instance()->getPopulation(postID));

    target_ = target;
    post_neuron_rank_ = postRank;
    
    post_population_->getProjection(pre_population_, target)->addDendrite(postRank, this);
    pre_population_->addSpikeTarget(this);
}

%(class)s::~%(class)s() 
{
#ifdef _DEBUG
    std::cout<<"%(class)s::Destructor"<<std::endl;
#endif

%(destructor)s
}

int %(class)s::addSynapse(int rank, DATA_TYPE value, int delay)
{
%(add_synapse_body)s
}

int %(class)s::removeSynapse(int rank)
{
%(rem_synapse_body)s
}

int %(class)s::removeAllSynapses()
{
%(rem_all_synapse_body)s
}

void %(class)s::initValues() 
{
%(init)s
}

void %(class)s::computeSum() {   
%(sum)s
}

void %(class)s::localLearn() {
%(local)s
}

void %(class)s::globalLearn() {
%(global)s
}

void %(class)s::record() 
{
%(record)s
}

void %(class)s::preEvent(int rank) 
{
%(pre_event)s
}

void %(class)s::postEvent() 
{
%(post_event)s
}
"""

# Template for a local variable
# 
# Depends on:
# 
#     * name : name of the variable
#    
#     * Name : Capitalized name of variable
#
#     * type : type of the variable
#
local_variable_access = \
"""
    // Access methods for the local variable %(name)s
    std::vector<%(type)s> get%(Name)s() { return this->%(name)s_; }
    void set%(Name)s(std::vector<%(type)s> %(name)s) { this->%(name)s_ = %(name)s; }
    
    %(type)s getSingle%(Name)s(int rank) { return this->%(name)s_[rank]; }
    void setSingle%(Name)s(int rank, %(type)s %(name)s) { this->%(name)s_[rank] = %(name)s; }

    std::vector< std::vector< %(type)s > >getRecorded%(Name)s() { return this->recorded_%(name)s_; }                    
    void startRecord%(Name)s() { this->record_%(name)s_ = true; }
    void stopRecord%(Name)s() { this->record_%(name)s_ = false; }
    void clearRecorded%(Name)s() { this->recorded_%(name)s_.clear(); }
    
"""

# Template for a global variable
# 
# Depends on:
# 
#     * name : name of the variable
#    
#     * Name : Capitalized name of variable
#
#     * type : type of the variable
#
global_variable_access = \
"""
    // Access methods for the global variable %(name)s
    %(type)s get%(Name)s() { return this->%(name)s_; }
    void set%(Name)s(%(type)s %(name)s) { this->%(name)s_ = %(name)s; }
"""

# Cython file for a rate population
#
# Depends on:
#
#    * name : the class name
#
#    * cFunction : c++ methods to access attributes
# 
#    * pyFunction ' python functions to access attributes
# 
rate_projection_pyx = \
"""from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp cimport bool

import numpy as np

cdef extern from "../build/%(name)s.h":
    cdef cppclass %(name)s:
        %(name)s(int preLayer, int postLayer, int postNeuronRank, int target)

        void initValues()

%(cFunction)s

cdef class Local%(name)s(pyxDendrite):

    cdef %(name)s* cInhInstance

    def __cinit__(self, proj_type, preID, postID, rank, target, rateCoded):
        self.cInhInstance = <%(name)s*>(createProjInstance().getInstanceOf(proj_type, preID, postID, rank, target, rateCoded))

    def init_values(self):
        self.cInhInstance.initValues()
        
%(pyFunction)s

""" 

# Cython file for a Spike projection
#
# Depends on:
#
#    * name : the class name
#
#    * cFunction : c++ methods to access attributes
# 
#    * pyFunction ' python functions to access attributes
# 
spike_projection_pyx = \
"""from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp cimport bool

import numpy as np

cdef extern from "../build/%(name)s.h":
    cdef cppclass %(name)s:
        %(name)s(int preLayer, int postLayer, int postNeuronRank, int target)

        void initValues()
        
%(cFunction)s

cdef class Local%(name)s(pyxDendrite):

    cdef %(name)s* cInhInstance

    def __cinit__(self, proj_type, preID, postID, rank, target, rateCoded):
        self.cInhInstance = <%(name)s*>(createProjInstance().getInstanceOf(proj_type, preID, postID, rank, target, rateCoded))

    def init_values(self):
        self.cInhInstance.initValues()

%(pyFunction)s

""" 

# Local Cython property
# 
# Depends on:
# 
#     * name : name of the variable
#    
#     * Name : Capitalized name of variable
local_property_pyx = """
    property %(name)s:
        def __get__(self):
            return np.array(self.cInhInstance.get%(Name)s())

        def __set__(self, value):
            if isinstance(value, np.ndarray)==True:
                if value.ndim==1:
                    self.cInhInstance.set%(Name)s(value)
                else:
                    self.cInhInstance.set%(Name)s(value.reshape(self.size))
            else:
                self.cInhInstance.set%(Name)s(np.ones(self.size)*value)

    def _get_single_%(name)s(self, rank):
        return self.cInhInstance.getSingle%(Name)s(rank)

    def _set_single_%(name)s(self, rank, value):
        self.cInhInstance.setSingle%(Name)s(rank, value)

    def _start_record_%(name)s(self):
        self.cInhInstance.startRecord%(Name)s()

    def _stop_record_%(name)s(self):
        self.cInhInstance.stopRecord%(Name)s()

    def _get_recorded_%(name)s(self):
        tmp = np.array(self.cInhInstance.getRecorded%(Name)s())
        self.cInhInstance.clearRecorded%(Name)s()
        return tmp
        
"""

# Global Cython property
# 
# Depends on:
# 
#     * name : name of the variable
#    
#     * Name : Capitalized name of variable
global_property_pyx = """
    property %(name)s:
        def __get__(self):
            return self.cInhInstance.get%(Name)s()

        def __set__(self, value):
            self.cInhInstance.set%(Name)s(value)
        
"""

# Local Cython wrapper
# 
# Depends on:
# 
#     * name : name of the variable
#    
#     * Name : Capitalized name of variable
#    
#     * type : C type of variable
local_wrapper_pyx = """
        # Local %(name)s
        vector[%(type)s] get%(Name)s()
        void set%(Name)s(vector[%(type)s] values)
        %(type)s getSingle%(Name)s(int rank)
        void setSingle%(Name)s(int rank, %(type)s values)
        void startRecord%(Name)s()
        void stopRecord%(Name)s()
        void clearRecorded%(Name)s()
        vector[vector[%(type)s]] getRecorded%(Name)s()
"""

# Global Cython wrapper
# 
# Depends on:
# 
#     * name : name of the variable
#    
#     * Name : Capitalized name of variable
#    
#     * type : C type of variable
global_wrapper_pyx = """
        # Global %(name)s
        %(type)s get%(Name)s()
        void set%(Name)s(%(type)s value)                
"""

# an implementation code of adding dynamically synapses.
# 
# Depends on:
# 
#     * add_synapse : push_back of local variables, except value, delay, rank
add_synapse_body = """
    for(unsigned int i=0; i < rank_.size(); i++) 
    {
        if(rank_[i] == rank ) 
        {
        #ifdef _DEBUG
            std::cout << "synapse already exists ... " << std::endl;
        #endif
            return -1;
        }
    }

    rank_.push_back(rank);
    value_.push_back(value);
    
    if( delay > 0 )
    {
        delay_.push_back(delay);
        if(delay > maxDelay_)
        {
            maxDelay_ = delay;
            pre_population_->setMaxDelay(maxDelay_);
        }
    }

    if ( !isRateCoded_ )
    {
        auto tmp = std::pair<int,int>(rank, rank_.size()-1);
        inv_rank_.insert( tmp );
    }
    
    %(add_synapse)s

    nbSynapses_++;
    return 0;
"""

# an implementation code of removing dynamically synapses.
# 
# Depends on:
# 
#     * rem_synapse : erase of local variables, except value, delay, rank
rem_synapse_body = """
#ifdef _DEBUG
    std::cout << "suppress synapse - pre = " << rank << std::endl;
    std::cout << "check "<< rank_.size() <<" synapses."<< std::endl;
#endif
    for(unsigned int i=0; i < rank_.size(); i++) 
    {
        if(rank_[i] == rank ) 
        {
        #ifdef _DEBUG
           std::cout << "found the synapse at: "<< i <<std::endl;
        #endif
        
           rank_.erase(rank_.begin()+i);
           value_.erase(value_.begin()+i);

           if (delay_.size() > 1)
               delay_.erase(delay_.begin()+i);

            %(rem_synapse)s

           nbSynapses_--;
           return 0;
        }
    }

    return -1;
"""

rem_all_synapse_body = """
    rank_.clear();
    value_.clear();
    delay_.clear();
    
    nbSynapses_ = 0;
    
    %(rem_all_synapse)s
    
    if( !isRateCoded_ )
        inv_rank_.clear();
"""