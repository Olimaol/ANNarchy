#===============================================================================
#
#     CUDATemplates.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2016-2018  Julien Vitay <julien.vitay@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchy is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#===============================================================================
projection_header = """#pragma once

#include "sparse_matrix.cuh"

#include "pop%(id_pre)s.hpp"
#include "pop%(id_post)s.hpp"
%(include_additional)s
%(include_profile)s

extern std::vector<std::mt19937> rng;
extern unsigned long long global_seed;

extern PopStruct%(id_pre)s pop%(id_pre)s;
extern PopStruct%(id_post)s pop%(id_post)s;
%(struct_additional)s

/////////////////////////////////////////////////////////////////////////////
// proj%(id_proj)s: %(name_pre)s -> %(name_post)s with target %(target)s
/////////////////////////////////////////////////////////////////////////////
struct ProjStruct%(id_proj)s : %(sparse_format)s <int>{
    ProjStruct%(id_proj)s() : %(sparse_format)s <int>(%(sparse_format_args)s) {
    }

%(connector_call)s

    // Number of dendrites
    int size;

    // Transmission and plasticity flags
    bool _transmission, _plasticity, _update;
    int _update_period;
    long int _update_offset;

%(declare_delay)s
%(declare_event_driven)s
%(declare_rng)s
%(declare_parameters_variables)s
%(declare_cuda_stream)s
%(declare_additional)s
%(declare_profile)s

    // Method called to initialize the projection
    void init_projection() {
        _transmission = true;
        _update = true;
        _plasticity = true;
        _update_period = 1;
        _update_offset = 0L;

%(init_event_driven)s
%(init_parameters_variables)s
%(init_rng)s
%(init_additional)s
%(init_profile)s
    }

    // Accessors for default attributes
    int get_size() { return size; }
    void set_size(int new_size) { size = new_size; }

    // Additional access methods
%(access_parameters_variables)s
%(access_additional)s

    // Memory management
    long int size_in_bytes() {
        long int size_in_bytes = 0;
%(determine_size)s
        return size_in_bytes;
    }

    void clear() {
%(clear_container)s
    }

    // Memory transfers
    void host_to_device() {
%(host_to_device)s
    }

    void device_to_host() {
%(device_to_host)s
    }
};
"""

# Definition for the usage of CUDA device random
# number generators
#
# Parameters:
#
#    rd_name:
#    rd_update:
curand = {
    'local': {
        'decl': """
    curandState* gpu_%(rd_name)s;
""",
        'init': """
        cudaMalloc((void**)&gpu_%(rd_name)s, this->nb_synapses() * sizeof(curandState));
        init_curand_states( this->nb_synapses(), gpu_%(rd_name)s, global_seed );
    #ifdef _DEBUG
        cudaError_t err = cudaGetLastError();
        if ( err != cudaSuccess )
            std::cout << "proj%(id)s - init_projection: " << cudaGetErrorString(err) << std::endl;
    #endif

"""
    },
    'global': {
        'decl': """
    curandState* gpu_%(rd_name)s;
""",
        'init': """
        cudaMalloc((void**)&gpu_%(rd_name)s, size * sizeof(curandState));
        init_curand_states( size, gpu_%(rd_name)s, global_seed );
    #ifdef _DEBUG
        cudaError_t err = cudaGetLastError();
        if ( err != cudaSuccess )
            std::cout << "proj%(id)s - init_projection: " << cudaGetErrorString(err) << std::endl;
    #endif
"""
    }
}

cuda_stream = """
    // stream
    cudaStream_t stream;
"""

# some base stuff
cuda_templates = {
    'projection_header': projection_header,
    'rng': curand
}