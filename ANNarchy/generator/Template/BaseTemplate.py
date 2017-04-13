omp_header_template = """#pragma once

#include <string>
#include <vector>
#include <algorithm>
#include <map>
#include <deque>
#include <queue>
#include <iostream>
#include <sstream>
#include <fstream>
#include <cstdlib>
#include <stdlib.h>
#include <string.h>
#include <random>
%(include_omp)s

/*
 * Built-in functions
 *
 */
%(built_in)s

/*
 * Custom constants
 *
 */
%(custom_constant)s

/*
 * Custom functions
 *
 */
%(custom_func)s

/*
 * Structures for the populations
 *
 */
%(pop_struct)s
/*
 * Structures for the projections
 *
 */
%(proj_struct)s


/*
 * Internal data
 *
*/
extern %(float_prec)s dt;
extern long int t;
extern std::mt19937  rng;


/*
 * Declaration of the populations
 *
 */
%(pop_ptr)s

/*
 * Declaration of the projections
 *
 */
%(proj_ptr)s

/*
 * Recorders
 *
 */
#include "Recorder.h"

extern std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder);
void removeRecorder(Monitor* recorder);

/*
 * Simulation methods
 *
*/

void initialize(%(float_prec)s _dt, long int seed) ;

void run(int nbSteps);

int run_until(int steps, std::vector<int> populations, bool or_and);

void step();


/*
 * Time export
 *
*/
long int getTime() ;
void setTime(long int t_) ;

%(float_prec)s getDt() ;
void setDt(%(float_prec)s dt_);

/*
 * Number of threads
 *
*/
void setNumberThreads(int threads);

/*
 * Seed for the RNG
 *
*/
void setSeed(long int seed);

"""

omp_body_template = """
#include "ANNarchy.h"
%(prof_include)s

/*
 * Internal data
 *
 */
%(float_prec)s dt;
long int t;
std::mt19937  rng;

// Custom constants
%(custom_constant)s

// Populations
%(pop_ptr)s

// Projections
%(proj_ptr)s

// Global operations
%(glops_def)s

// Recorders
std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder){
    recorders.push_back(recorder);
}
void removeRecorder(Monitor* recorder){
    for(int i=0; i<recorders.size(); i++){
        if(recorders[i] == recorder){
            recorders.erase(recorders.begin()+i);
            break;
        }
    }
}

void singleStep(); // Function prototype

// Simulate the network for the given number of steps,
// called from python
void run(int nbSteps) {
%(prof_run_pre)s
    for(int i=0; i<nbSteps; i++) {
        singleStep();
    }
%(prof_run_post)s
}

// Simulate the network for a single steps,
// called from python
void step() {
%(prof_run_pre)s
    singleStep();
%(prof_run_post)s
}

int run_until(int steps, std::vector<int> populations, bool or_and)
{

%(run_until)s

}

// Initialize the internal data and random numbers generators
void initialize(%(float_prec)s _dt, long int seed) {
%(initialize)s
}

// Change the seed of the RNG
void setSeed(long int seed){
    if(seed==-1){
        rng = std::mt19937(time(NULL));
    }
    else{
        rng = std::mt19937(seed);
    }
}

// Step method. Generated by ANNarchy.
void singleStep()
{
%(prof_step_pre)s

    ////////////////////////////////
    // Presynaptic events
    ////////////////////////////////
%(prof_proj_psp_pre)s
%(reset_sums)s
%(compute_sums)s
%(prof_proj_psp_post)s

    ////////////////////////////////
    // Recording target variables
    ////////////////////////////////
    for(int i=0; i < recorders.size(); i++){
        recorders[i]->record_targets();
    }

    ////////////////////////////////
    // Update random distributions
    ////////////////////////////////
%(random_dist_update)s

    ////////////////////////////////
    // Update neural variables
    ////////////////////////////////
%(prof_neur_step_pre)s
%(update_neuron)s
%(prof_neur_step_post)s

    ////////////////////////////////
    // Delay outputs
    ////////////////////////////////
%(delay_code)s

    ////////////////////////////////
    // Global operations (min/max/mean)
    ////////////////////////////////
%(update_globalops)s

    ////////////////////////////////
    // Update synaptic variables
    ////////////////////////////////
%(prof_proj_step_pre)s
%(update_synapse)s
%(prof_proj_step_post)s

    ////////////////////////////////
    // Postsynaptic events
    ////////////////////////////////
%(post_event)s

    ////////////////////////////////
    // Structural plasticity
    ////////////////////////////////
%(structural_plasticity)s

    ////////////////////////////////
    // Recording neural / synaptic variables
    ////////////////////////////////
    for(int i=0; i < recorders.size(); i++){
        recorders[i]->record();
    }

    ////////////////////////////////
    // Increase internal time
    ////////////////////////////////
    t++;

%(prof_step_post)s
}


/*
 * Access to time and dt
 *
*/
long int getTime() {return t;}
void setTime(long int t_) { t=t_;}
%(float_prec)s getDt() { return dt;}
void setDt(%(float_prec)s dt_) { dt=dt_;}

/*
 * Number of threads
 *
*/
void setNumberThreads(int threads)
{
    %(set_number_threads)s
}
"""

omp_run_until_template = {
    'default':
"""
    run(steps);
    return steps;
""",
    'body':
"""
    bool stop = false;
    int nb = 0;
    for(int n = 0; n < steps; n++)
    {
        step();
        nb++;
        stop = or_and;

%(run_until)s

        if(stop)
            break;
    }
    return nb;

""",
    'single_pop': """
        if(or_and)
            stop = stop && pop%(id)s.stop_condition();
        else
            stop = stop || pop%(id)s.stop_condition();
    """
}

omp_initialize_template = """
%(prof_init)s
    // Internal variables
    dt = _dt;
    t = (long int)(0);

    // Random number generators
    setSeed(seed);

    // Populations
%(pop_init)s

    // Projections
%(proj_init)s

    // Custom constants
%(custom_constant)s
"""

cuda_header_template = """#ifndef __ANNARCHY_H__
#define __ANNARCHY_H__

#include <string>
#include <vector>
#include <algorithm>
#include <map>
#include <deque>
#include <queue>
#include <iostream>
#include <sstream>
#include <fstream>
#include <cstdlib>
#include <stdlib.h>
#include <string.h>

#include <cuda_runtime_api.h>
#include <curand_kernel.h>

/*
 * Built-in functions
 */
%(built_in)s

/*
 * Structures for the populations
 *
 */
%(pop_struct)s
/*
 * Structures for the projections
 *
 */
%(proj_struct)s

/*
 * Internal data
 *
*/
extern %(float_prec)s dt;
extern long int t;

/*
 * Declaration of the populations
 *
 */
%(pop_ptr)s

/*
 * Declaration of the projections
 *
 */
%(proj_ptr)s

/*
 * (De-)Flattening of LIL structures
 */
template<typename T>
std::vector<int> flattenIdx(std::vector<std::vector<T> > in)
{
    std::vector<T> flatIdx = std::vector<T>();
    typename std::vector<std::vector<T> >::iterator it;

    for ( it = in.begin(); it != in.end(); it++)
    {
        flatIdx.push_back(it->size());
    }

    return flatIdx;
}

template<typename T>
std::vector<int> flattenOff(std::vector<std::vector<T> > in)
{
    std::vector<T> flatOff = std::vector<T>();
    typename std::vector<std::vector<T> >::iterator it;

    int currOffset = 0;
    for ( it = in.begin(); it != in.end(); it++)
    {
        flatOff.push_back(currOffset);
        currOffset += it->size();
    }

    return flatOff;
}

template<typename T>
std::vector<T> flattenArray(std::vector<std::vector<T> > in)
{
    std::vector<T> flatVec = std::vector<T>();
    typename std::vector<std::vector<T> >::iterator it;

    for ( it = in.begin(); it != in.end(); it++)
    {
        flatVec.insert(flatVec.end(), it->begin(), it->end());
    }

    return flatVec;
}

template<typename T>
std::vector<std::vector<T> > deFlattenArray(std::vector<T> in, std::vector<int> idx)
{
    std::vector<std::vector<T> > deFlatVec = std::vector<std::vector<T> >();
    std::vector<int>::iterator it;

    int t=0;
    for ( it = idx.begin(); it != idx.end(); it++)
    {
        std::vector<T> tmp = std::vector<T>(in.begin()+t, in.begin()+t+*it);
        t += *it;

        deFlatVec.push_back(tmp);
    }

    return deFlatVec;
}

/*
 * Recorders
 *
 */
#include "Recorder.h"

extern std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder);
void removeRecorder(Monitor* recorder);

/*
 * Simulation methods
 *
 */
void initialize(%(float_prec)s _dt, long seed) ;

void run(int nbSteps);

int run_until(int steps, std::vector<int> populations, bool or_and);

void step();

inline void setDevice(int device_id) {
#ifdef _DEBUG
    std::cout << "Setting device " << device_id << " as compute device ..." << std::endl;
#endif
    cudaError_t err = cudaSetDevice(device_id);
    if ( err != cudaSuccess )
        std::cerr << "Set device " << device_id << ": " << cudaGetErrorString(err) << std::endl;
}

/*
 * Time export
 *
*/
long int getTime() ;
void setTime(long int t_) ;

%(float_prec)s getDt() ;
void setDt(%(float_prec)s dt_);

/*
 * Seed for the RNG
 *
 */
inline void setSeed(long int seed){ printf("Setting seed not implemented on CUDA"); }

#endif
"""

cuda_device_kernel_template = """
/****************************************
 * Global Symbols (ANNarchyHost.cu)     *
 ****************************************/
#include <curand_kernel.h>
extern __device__ long int t;
extern __device__ double atomicAdd(double* address, double val);

/****************************************
 * inline functions                     *
 ****************************************/
%(built_in)s

/****************************************
 * custom functions                     *
 ****************************************/
%(custom_func)s

/****************************************
 * updating neural variables            *
 ****************************************/
%(pop_kernel)s

/****************************************
 * weighted sum kernels                 *
 ****************************************/
__global__ void clear_sum(int num_elem, double *sum) {
    int j = threadIdx.x + blockIdx.x * blockDim.x;
    
    while( j < num_elem ) {
        sum[j] = 0.0;
        j+= blockDim.x * gridDim.x;
    }
}

%(psp_kernel)s

/****************************************
 * update synapses kernel               *
 ****************************************/
%(syn_kernel)s

/****************************************
 * global operations kernel             *
 ****************************************/
%(glob_ops_kernel)s

/****************************************
 * postevent kernel                     *
 ****************************************/
%(postevent_kernel)s
"""

cuda_host_body_template =\
"""
#ifdef __CUDA_ARCH__
/***********************************************************************************/
/*                                                                                 */
/*                                                                                 */
/*          DEVICE - code                                                          */
/*                                                                                 */
/*                                                                                 */
/***********************************************************************************/
#include <cuda_runtime_api.h>
#include <curand_kernel.h>
#include <float.h>

/****************************************
 * atomicAdd for non-Pascal             *
 ****************************************/
#if !defined(__CUDA_ARCH__) || __CUDA_ARCH__ >= 600
#else
    __device__ double atomicAdd(double* address, double val)
    {
        unsigned long long int* address_as_ull = (unsigned long long int*)address;
        unsigned long long int old = *address_as_ull, assumed;
        do {
            assumed = old;
            old = atomicCAS(address_as_ull, assumed,
                            __double_as_longlong(val +
                            __longlong_as_double(assumed)));
        } while (assumed != old);
        return __longlong_as_double(old);
    }
#endif

/****************************************
 * init random states                   *
 ****************************************/
/*
 *  Each thread gets an unique sequence number (i) and all use the same seed. As highlightet
 *  in section 3.1.1. of the curand documentation this should be enough to get good random numbers
 */
__global__ void rng_setup_kernel( int N, curandState* states, unsigned long seed )
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    while( i < N )
    {
        curand_init( seed, i, 0, &states[ i ] );
        i += blockDim.x * gridDim.x;
    }
}

// global time step
__device__ long int t;
__global__ void update_t(int t_host) {
    t = t_host;
}

// Computation Kernel
#include "ANNarchyDevice.cu"

#else
/***********************************************************************************/
/*                                                                                 */
/*                                                                                 */
/*          HOST - code                                                            */
/*                                                                                 */
/*                                                                                 */
/***********************************************************************************/
#include "ANNarchy.h"
%(prof_include)s
#include <math.h>

// cuda specific header
#include <cuda_runtime_api.h>
#include <curand.h>
#include <float.h>

// kernel config
%(kernel_config)s

// Kernel definitions
__global__ void update_t(int t_host);
__global__ void clear_sum(int num_elem, double *sum);
%(kernel_def)s

// RNG
__global__ void rng_setup_kernel( int N, curandState* states, unsigned long seed );

void init_curand_states( int N, curandState* states, unsigned long seed ) {
    int numThreads = 64;
    int numBlocks = ceil (float(N) / float(numThreads));

    rng_setup_kernel<<< numBlocks, numThreads >>>( N, states, seed);

#ifdef _DEBUG
    cudaError_t err = cudaGetLastError();
    if ( err != cudaSuccess )
        std::cout << "init_curand_state: " << cudaGetErrorString(err) << std::endl;
#endif
}

/*
 * Internal data
 *
 */
%(float_prec)s dt;
long int t;
long seed;

// Recorders
std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder){
    recorders.push_back(recorder);
}
void removeRecorder(Monitor* recorder){
    for(int i=0; i<recorders.size(); i++){
        if(recorders[i] == recorder){
            recorders.erase(recorders.begin()+i);
            break;
        }
    }
}

// Populations
%(pop_ptr)s

// Projections
%(proj_ptr)s

// Stream configuration (available for CC > 3.x devices)
// NOTE: if the CC is lower then 3.x modification of stream
//       parameter (4th arg) is automatically ignored by CUDA
%(stream_setup)s

/**
 *  Implementation remark (27.02.2015, HD) to: run(int), step() and single_step()
 *
 *  we have two functions in ANNarchy to run simulation code: run(int) and step(). The latter one to
 *  run several steps at once, the other one just a single step. On CUDA I face the problem, that I
 *  propably need to update variables before step() and definitly changed variables after step().
 *  run(int) calls step() normally, if I add transfer codes in step(), run(N) would end up in N
 *  back transfers from GPUs, whereas we only need the last one.
 *  As solution I renamed step() to single_step(), the interface behaves as OMP side and I only
 *  transfer at begin and at end, as planned.
 */
void single_step(); // function prototype

// Simulate the network for the given number of steps
void run(int nbSteps) {
#ifdef _DEBUG
    std::cout << "simulate " << nbSteps << " steps." << std::endl;
#endif

%(host_device_transfer)s

    stream_assign();

%(prof_run_pre)s
    // simulation loop
    for(int i=0; i<nbSteps; i++) {
        single_step();
    }
%(prof_run_post)s

%(device_host_transfer)s
}

int run_until(int steps, std::vector<int> populations, bool or_and) {
%(run_until)s
}

void step() {
%(host_device_transfer)s
%(prof_run_pre)s
    single_step();
%(prof_run_post)s
%(device_host_transfer)s
}

// Initialize the internal data and random numbers generators
void initialize(%(float_prec)s _dt, long _seed) {
%(initialize)s
}

// Step method. Generated by ANNarchy. (analog to step() in OMP)
void single_step()
{
%(prof_step_pre)s

%(prof_proj_psp_pre)s
    ////////////////////////////////
    // Clear sums
    ////////////////////////////////
%(clear_sums)s

    cudaDeviceSynchronize();

    ////////////////////////////////
    // Presynaptic events
    ////////////////////////////////
%(compute_sums)s

    cudaDeviceSynchronize();
%(prof_proj_psp_post)s

    ////////////////////////////////
    // Recording targets
    ////////////////////////////////
    for(int i=0; i < recorders.size(); i++){
        recorders[i]->record_targets();
    }

    ////////////////////////////////
    // Update neural variables
    ////////////////////////////////
%(prof_neur_step_pre)s
%(update_neuron)s

    cudaDeviceSynchronize();
%(prof_neur_step_post)s

%(update_FR)s

    ////////////////////////////////
    // Delay outputs
    ////////////////////////////////
%(delay_code)s

    ////////////////////////////////
    // Global operations (min/max/mean)
    ////////////////////////////////
%(update_globalops)s

    cudaDeviceSynchronize();

    ////////////////////////////////
    // Update synaptic variables
    ////////////////////////////////
%(prof_proj_step_pre)s
%(update_synapse)s

    cudaDeviceSynchronize();
%(prof_proj_step_post)s

    ////////////////////////////////
    // Postsynaptic events
    ////////////////////////////////
%(post_event)s

    cudaDeviceSynchronize();

    ////////////////////////////////
    // Recording neural/synaptic variables
    ////////////////////////////////
    for(int i=0; i < recorders.size(); i++){
        recorders[i]->record();
    }

    ////////////////////////////////
    // Increase internal time
    ////////////////////////////////
    t++;    // host side
    // note: the first parameter is the name of the device variable
    //       for earlier releases before CUDA4.1 this was a const char*
    cudaMemcpyToSymbol(t, &t, sizeof(long int));    // device side
    //update_t<<<1,1>>>(t);

%(prof_step_post)s
}


/*
 * Access to time and dt
 *
*/
long int getTime() {return t;}
void setTime(long int t_) { t=t_; cudaMemcpyToSymbol(t, &t, sizeof(long int)); }
%(float_prec)s getDt() { return dt;}
void setDt(%(float_prec)s dt_) { dt=dt_;}
#endif
"""

cuda_stream_setup=\
"""
cudaStream_t streams[%(nbStreams)s];

void stream_setup()
{
    for ( int i = 0; i < %(nbStreams)s; i ++ )
    {
        cudaStreamCreate( &streams[i] );
    }
}

void stream_assign()
{
%(pop_assign)s

%(proj_assign)s
}

void stream_destroy()
{
    for ( int i = 0; i < %(nbStreams)s; i ++ )
    {
        // all work finished
        cudaStreamSynchronize( streams[i] );

        // destroy
        cudaStreamDestroy( streams[i] );
    }
}
"""

cuda_initialize_template = """
    dt = _dt;
    t = (long int)(0);
    cudaMemcpyToSymbol(t, &t, sizeof(long int));    // device side
    //update_t<<<1,1>>>(t);

    // seed
    seed = _seed;

%(prof_init)s

%(pop_init)s

%(proj_init)s

    // create streams
    stream_setup();
"""

built_in_functions = """
#define positive(x) (x>0.0? x : 0.0)
#define negative(x) (x<0.0? x : 0.0)
#define clip(x, a, b) (x<a? a : (x>b? b :x))
#define modulo(a, b) long(a) % long(b)
#define Equality(a, b) a == b
#define Eq(a, b) a == b
#define And(a, b) a && b
#define Or(a, b) a || b
#define Not(a) !a
#define Ne(a, b) a != b
#define ite(a, b, c) (a?b:c)
"""
