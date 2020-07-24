#===============================================================================
#
#     CSR_OpenmMP.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2016-2020  Julien Vitay <julien.vitay@gmail.com>,
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
connectivity_matrix = {
    'declare': """
    // LIL connectivity
    std::vector<int> post_ranks; // its encoded implicitely in CSR

    // CSR connectivity
    std::vector<int> _row_ptr;
    std::vector<int> _col_idx;
    int _nb_synapses;
""",
    'accessor': """
    // Accessor to connectivity data
    std::vector<int> get_post_rank() { return post_ranks; }
    int nb_synapses(int lil_idx) {
        if ( _inv_computed ) {
            int rk_post = post_ranks[lil_idx];
            return _col_ptr[rk_post+1] - _col_ptr[rk_post];
        }else{
            return 0;
        }
    }

    // LIL specific, read-only
    std::vector<int> get_dendrite_pre_rank(int lil_idx) {
        if ( _inv_computed ) {
            int n = post_ranks[lil_idx];
            auto beg = _row_idx.begin()+_col_ptr[n];
            auto end = _row_idx.begin()+_col_ptr[n+1];
            return std::vector<int>(beg, end);
        } else {
            std::cout << "Inverse connectivity was not created ..." << std::endl;
            return std::vector<int>();
        }
    }
""",
    'init': """
""",
    'pyx_struct': """
        void init_from_lil(vector[int] post_ranks, vector[vector[int]] pre_ranks, vector[vector[double]] weights, vector[vector[int]] delays)

        # LIL Connectivity, read-only !!!
        vector[int] get_post_rank()
        vector[int] get_dendrite_pre_rank(int)
""",
    'pyx_wrapper_args': "synapses",
    'pyx_wrapper_init': """
        cdef post_ranks = synapses.post_rank

        proj%(id_proj)s.init_from_lil(synapses.post_rank, synapses.pre_rank, synapses.w, synapses.delay)
""",
    'pyx_wrapper_accessor': """
    # Connectivity
    def post_rank(self):
        return proj%(id_proj)s.get_post_rank()
    def pre_rank(self, int n):
        return proj%(id_proj)s.get_dendrite_pre_rank(n)
"""
}

weight_matrix = {
    'declare': """
    std::vector<%(float_prec)s> w;

    // Init the CSR from LIL
    void init_from_lil(std::vector<int> post_ranks, std::vector< std::vector<int> > pre_ranks, std::vector< std::vector<double> > weights, std::vector< std::vector<int> > delays) {
        // create the inverse view
        auto tmp_row_idx = std::vector< std::vector< int > >(%(pre_size)s, std::vector< int >());
        auto tmp_value = std::vector< std::vector< %(float_prec)s> >(%(pre_size)s, std::vector< %(float_prec)s >());

        for (unsigned int r = 0; r < post_ranks.size(); r++) {
            auto col_it = pre_ranks[r].begin();
            auto w_it = weights[r].begin();
            for (; col_it != pre_ranks[r].end(); col_it++, w_it++) {
                tmp_row_idx[*col_it].push_back(post_ranks[r]);
                tmp_value[*col_it].push_back(*w_it);
            }
        }

        // build up CSR based on inverse view
        _row_ptr = std::vector<int>(%(pre_size)s+1);
        _col_idx = std::vector<int>();
        w = std::vector<%(float_prec)s>();
        for (auto row_idx = 0; row_idx < %(pre_size)s; row_idx++ ) {
            _row_ptr[row_idx] = _col_idx.size();

            if ( tmp_row_idx[row_idx].size() > 0 ) {
                _col_idx.insert(_col_idx.end(), tmp_row_idx[row_idx].begin(), tmp_row_idx[row_idx].end());
                w.insert(w.end(), tmp_value[row_idx].begin(), tmp_value[row_idx].end());
            }
        }
        _row_ptr[%(pre_size)s] = _col_idx.size();
        _nb_synapses = _col_idx.size();
        this->post_ranks = post_ranks;

    #ifdef _DEBUG_CONN
         std::cout << "row_ptr = [ ";
         for (auto it = _row_ptr.begin(); it != _row_ptr.end(); it++)
             std::cout << *it << " ";
         std::cout << "]" << std::endl;

         std::cout << "col_idx = [ ";
         for (auto it = _col_idx.begin(); it != _col_idx.end(); it++)
             std::cout << *it << " ";
         std::cout << "]" << std::endl;

         std::cout << "values = [ ";
         for (auto it = w.begin(); it != w.end(); it++)
             std::cout << *it << " ";
         std::cout << "]" << std::endl;
    #endif
    }
""",
    'accessor': """
    std::vector< std::vector<%(float_prec)s> > get_w() {
        std::vector< std::vector< %(float_prec)s > > res;
        for(int i = 0; i < post_ranks.size(); i++ ) {
            res.push_back(std::move(get_dendrite_w(i)));
        }
        return res;
    }
    std::vector< %(float_prec)s > get_dendrite_w(int lil_idx) {
        int rk = post_ranks[lil_idx];
        std::vector< %(float_prec)s > tmp_w;
        for (auto col_idx = _col_ptr[rk]; col_idx < _col_ptr[rk+1]; col_idx++) {
            tmp_w.push_back(w[_inv_idx[col_idx]]);
        }
        return tmp_w;
    }
    void set_w(std::vector<std::vector< %(float_prec)s > >value) {
        for (int i = 0; i < post_ranks.size(); i++) {
            set_dendrite_w(i, value[i]);
        }
    }
    void set_dendrite_w(int lil_idx, std::vector<%(float_prec)s> value) {
        int rk = post_ranks[lil_idx];
        int i = 0;
        int j = _col_ptr[rk];
        for (; j < _col_ptr[rk+1]; i++, j++) {
            w[j] = value[i];
        }
    }
""",
    'init': """
""",
    'pyx_struct': """
        # Interface access
        vector[%(float_prec)s] get_dendrite_w(int)
        vector[vector[%(float_prec)s]] get_w()
""",
    'pyx_wrapper_args': "",
    'pyx_wrapper_init': """
""",
    'pyx_wrapper_accessor': """
    def get_w(self):
        return proj%(id_proj)s.get_w()
    def get_dendrite_w(self, int rank):
        return proj%(id_proj)s.get_dendrite_w(rank)
"""
}

single_weight_matrix = {
    'declare': """
    // Single weight in the projection
    %(float_prec)s w;

    // Init the CSR from LIL
    void init_from_lil(std::vector<int> post_ranks, std::vector< std::vector<int> > pre_ranks, std::vector< std::vector<double> > weights, std::vector< std::vector<int> > delays) {
        // just store
        this->post_ranks = post_ranks;
        w = weights[0][0];

        // create the inverse view
        auto tmp_row_idx = std::vector< std::vector< int > >(%(pre_size)s, std::vector< int >());

        for (unsigned int r = 0; r < post_ranks.size(); r++) {
            auto col_it = pre_ranks[r].begin();
            for (; col_it != pre_ranks[r].end(); col_it++) {
                tmp_row_idx[*col_it].push_back(post_ranks[r]);
            }
        }

        // build up CSR based on inverse view
        _row_ptr = std::vector<int>(%(pre_size)s+1);
        _col_idx = std::vector<int>();
        for (auto row_idx = 0; row_idx < %(pre_size)s; row_idx++ ) {
            _row_ptr[row_idx] = _col_idx.size();

            if ( tmp_row_idx[row_idx].size() > 0 ) {
                _col_idx.insert(_col_idx.end(), tmp_row_idx[row_idx].begin(), tmp_row_idx[row_idx].end());
            }
        }
        _row_ptr[%(pre_size)s] = _col_idx.size();
        _nb_synapses = _col_idx.size();

    #ifdef _DEBUG_CONN
         std::cout << "row_ptr = [ ";
         for (auto it = _row_ptr.begin(); it != _row_ptr.end(); it++)
             std::cout << *it << " ";
         std::cout << "]" << std::endl;

         std::cout << "col_idx = [ ";
         for (auto it = _col_idx.begin(); it != _col_idx.end(); it++)
             std::cout << *it << " ";
         std::cout << "]" << std::endl;

         std::cout << "values = " << w << std::endl;
    #endif
    }
""",
    'accessor': "",
    'init': "",
    'pyx_struct': """
        # Local variable w
        %(float_prec)s w
""",
    'pyx_wrapper_args': "",
    'pyx_wrapper_init': """
""",
    'pyx_wrapper_accessor': """
    # Local variable w
    def get_w(self):
        return proj%(id_proj)s.w
    def set_w(self, value):
        proj%(id_proj)s.w = value
    def get_dendrite_w(self, int rank):
        return proj%(id_proj)s.w
    def set_dendrite_w(self, int rank, %(float_prec)s value):
        proj%(id_proj)s.w = value
    def get_synapse_w(self, int rank_post, int rank_pre):
        return proj%(id_proj)s.w
    def set_synapse_w(self, int rank_post, int rank_pre, %(float_prec)s value):
        proj%(id_proj)s.w = value
"""
}

inverse_connectivity_matrix = {
    'declare': """
    // CSR inverse
    std::vector<int> _col_ptr;
    std::vector<int> _row_idx;
    std::vector<int> _inv_idx;
    bool _inv_computed = false;
""",
    'init': """
        if ( _inv_computed )
            return;

        if (_row_ptr.empty()) {
            std::cerr << "no row_ptr data ..." << std::endl;
            return;
        }

        //
        // 2-pass algorithm: 1st we compute the inverse connectivity as LIL, 2ndly transform it to CSR
        //
        std::map< int, std::vector< int > > inv_post_rank = std::map< int, std::vector< int > >();
        std::map< int, std::vector< int > > inv_idx = std::map< int, std::vector< int > >();

        // iterate over post neurons, post_rank_it encodes the current rank
        for( int i = 0; i < (_row_ptr.size()-1); i++ ) {
            int row_begin = _row_ptr[i];
            int row_end = _row_ptr[i+1];

            // iterate over synapses, update both result containers
            for( int syn_idx = row_begin; syn_idx < row_end; syn_idx++ ) {
                inv_post_rank[_col_idx[syn_idx]].push_back(i);
                inv_idx[_col_idx[syn_idx]].push_back(syn_idx);
            }
        }

        //
        // store as CSR
        //
        _col_ptr.clear();
        _row_idx.clear();
        _inv_idx.clear();
        int curr_off = 0;

        // iterate over pre-neurons
        for ( int i = 0; i < %(pre_size)s; i++) {
            _col_ptr.push_back( curr_off );
            if ( !inv_post_rank[i].empty() ) {
                _row_idx.insert(_row_idx.end(), inv_post_rank[i].begin(), inv_post_rank[i].end());
                _inv_idx.insert(_inv_idx.end(), inv_idx[i].begin(), inv_idx[i].end());

                curr_off += inv_post_rank[i].size();
            }
        }
        _col_ptr.push_back(curr_off);

        if ( _nb_synapses != curr_off )
            std::cerr << "Something went wrong: (nb_synapes = " << _nb_synapses << ") != (curr_off = " << curr_off << ")" << std::endl;
    #ifdef _DEBUG_CONN
        std::cout << "Pre to Post:" << std::endl;
        for ( int i = 0; i < pop%(id_pre)s.size; i++ ) {
            std::cout << i << ": " << col_ptr[i] << " -> " << col_ptr[i+1] << std::endl;
        }
    #endif

        _inv_computed = true;
"""
}

attribute_decl = {
    'local':
"""
    // Local %(attr_type)s %(name)s
    std::vector< %(type)s > %(name)s;
""",
    'semiglobal':
"""
    // Semiglobal %(attr_type)s %(name)s
    std::vector< %(type)s >  %(name)s ;
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    %(type)s  %(name)s ;
"""
}

attribute_acc = {
    'local':
"""
    // Local %(attr_type)s %(name)sf
    std::vector<std::vector< %(type)s > > get_%(name)s() {
        std::vector< std::vector< %(type)s > > res;
        if ( _inv_computed ) {
            for(int i = 0; i < post_ranks.size(); i++ ) {
                res.push_back(std::move(get_dendrite_%(name)s(i)));
            }
        } else {
             std::cout << "Inverse connectivity missing ... " << std::endl;
        }
        return res;
    }
    std::vector<%(type)s> get_dendrite_%(name)s(int idx) {
        auto res = std::vector< %(type)s >();
        if ( _inv_computed ) {
            int rk = post_ranks[idx];
            for (auto col_idx = _col_ptr[rk]; col_idx < _col_ptr[rk+1]; col_idx++) {
                res.push_back(%(name)s[_inv_idx[col_idx]]);
            }
        } else {
             std::cout << "Inverse connectivity missing ... " << std::endl;
        }
        return res;
    }
    %(type)s get_synapse_%(name)s(int post_idx, int rk_pre) {
        int rk_post = post_ranks[post_idx];
        for(int j = _col_ptr[rk_post]; j < _col_ptr[rk_post+1]; j++)
            if ( _row_idx[j] == rk_pre )
                return %(name)s[_inv_idx[j]];
    }
    void set_%(name)s(std::vector<std::vector< %(type)s > >value) {
        for (int i = 0; i < post_ranks.size(); i++) {
            set_dendrite_%(name)s(i, value[i]);
        }
    }
    void set_dendrite_%(name)s(int idx, std::vector<%(type)s> value) {
        int rk = post_ranks[idx];
        if ( (_col_ptr[rk+1] - _col_ptr[rk]) != value.size() )
            std::cout << "set_%(name)s: vector mismatch ... " << std::endl;

        int i = 0;
        int j = _col_ptr[rk];
        for (; j < _col_ptr[rk+1]; i++, j++) {
            %(name)s[_inv_idx[j]] = value[i];
        }
    }
    void set_synapse_%(name)s(int rk_post, int rk_pre, %(type)s value) {
        for (int j = _col_ptr[rk_post]; j < _col_ptr[rk_post+1]; j++) {
            if ( _row_idx[j] == rk_pre ) {
                %(name)s[j] = value;
                break;
            }
        }
    }
""",
    'semiglobal':
"""
    // Semiglobal %(attr_type)s %(name)s
    std::vector<%(type)s> get_%(name)s() { return %(name)s; }
    %(type)s get_dendrite_%(name)s(int rk) { return %(name)s[rk]; }
    void set_%(name)s(std::vector<%(type)s> value) { %(name)s = value; }
    void set_dendrite_%(name)s(int rk, %(type)s value) { %(name)s[rk] = value; }
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    %(type)s get_%(name)s() { return %(name)s; }
    void set_%(name)s(%(type)s value) { %(name)s = value; }
"""
}

attribute_cpp_init = {
    'local':
"""
        // Local %(attr_type)s %(name)s
        %(name)s = std::vector< %(type)s >( _nb_synapses, %(init)s);
""",
    'semiglobal':
"""
        // Semiglobal %(attr_type)s %(name)s
        %(name)s = std::vector<%(type)s>( post_ranks.size(), %(init)s);
""",
    'global':
"""
        // Global %(attr_type)s %(name)s
        %(name)s = %(init)s;
"""
}

delay = {
    'uniform': {
        'declare': """
    // Uniform delay
    int delay ;""",
        'pyx_struct':
"""
        # Uniform delay
        int delay""",
        'init': "",
        'pyx_wrapper_init':
"""
        proj%(id_proj)s.delay = syn.uniform_delay""",
        'pyx_wrapper_accessor':
"""
    # Access to non-uniform delay
    def get_delay(self):
        return proj%(id_proj)s.delay
    def get_dendrite_delay(self, idx):
        return proj%(id_proj)s.delay
    def set_delay(self, value):
        proj%(id_proj)s.delay = value
"""},
    'nonuniform': {
        'declare': """
    // Non-uniform delay
    std::vector< std::vector< int > > delay ;""",
        'pyx_struct':
"""
        # Non-uniform delay
        vector[vector[int]] delay""",
        'init': "",
        'pyx_wrapper_init':
"""
        proj%(id_proj)s.delay = syn.delay""",
        'pyx_wrapper_accessor':
"""
    # Access to non-uniform delay
    def get_delay(self):
        return proj%(id_proj)s.delay
    def get_dendrite_delay(self, idx):
        return proj%(id_proj)s.delay[idx]
    def set_delay(self, value):
        proj%(id_proj)s.delay = value
"""
    }
}

event_driven = {
    'declare': """
    std::vector< long > _last_event;
""",
    'cpp_init': """
    _last_event = std::vector<long>( _nb_synapses, -10000);
""",
    'pyx_struct': """
        vector[long] _last_event
""",
    'pyx_wrapper_init':"""
"""
}

csr_summation_operation = {
    'sum' : """
%(pre_copy)s

%(omp_code)s
for(int i = 0; i < _col_ptr.size()-1; i++) {
    sum = 0.0;
    for(int j = _col_ptr[i]; j < _col_ptr[i+1]; j++) {
        sum += %(psp)s ;
    }
    pop%(id_post)s._sum_%(target)s%(post_index)s += sum;
}
"""
}

spiking_summation_fixed_delay = """// Event-based summation
if (_transmission && pop%(id_post)s._active){

    %(omp_code)s
    // Iterate over all spiking neurons
    for( int _idx = 0; _idx < %(pre_array)s.size(); _idx++) {
        // Rank of the presynaptic neuron
        int _pre = %(pre_array)s[_idx];

        // Iterate over connected post neurons
        for(int syn = _row_ptr[_pre]; syn < _row_ptr[_pre + 1]; syn++) {

            // Event-driven integration
            %(event_driven)s
            // Update conductance
            %(g_target)s
            // Synaptic plasticity: pre-events
            %(pre_event)s
        }
    }
} // active
"""

conn_templates = {
    # connectivity
    'connectivity_matrix': connectivity_matrix,
    'inverse_connectivity_matrix': inverse_connectivity_matrix,
    'weight_matrix': weight_matrix,
    'single_weight_matrix': single_weight_matrix,

    # accessors
    'attribute_decl': attribute_decl,
    'attribute_acc': attribute_acc,
    'attribute_cpp_init': attribute_cpp_init,
    'delay': delay,
    'event_driven': event_driven,

    #operations
    'rate_coded_sum': csr_summation_operation,
    'spiking_sum_fixed_delay': spiking_summation_fixed_delay,
    'spiking_sum_variable_delay': None
}