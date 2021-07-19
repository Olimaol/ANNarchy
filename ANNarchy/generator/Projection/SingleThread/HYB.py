#===============================================================================
#
#     HYB.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2020  Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
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
attribute_decl = {
    'local':
"""
    // Local %(attr_type)s %(name)s
    hyb_local<%(type)s> %(name)s;
""",
    'semiglobal':
"""
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    %(type)s %(name)s;
"""
}

attribute_cpp_init = {
    'local': """
        // Local %(attr_type)s %(name)s
        %(name)s = init_matrix_variable<%(type)s>(static_cast<%(type)s>(%(init)s));
"""
}

attribute_cpp_size = {
    'local': """
        // Local %(attr_type)s %(name)s
        size_in_bytes += sizeof(hyb_local<%(ctype)s>);
        size_in_bytes += (%(name)s.ell.capacity()) * sizeof(%(ctype)s);
        size_in_bytes += (%(name)s.coo.capacity()) * sizeof(%(ctype)s);       
""",
    'semiglobal': """
        // Semiglobal %(attr_type)s %(name)s
        size_in_bytes += sizeof(std::vector<%(ctype)s>());
        size_in_bytes += sizeof(%(ctype)s) * %(name)s.capacity();
""",
    'global': """
        // Global
        size_in_bytes += sizeof(%(ctype)s);
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
        'init': """
    delay = delays[0][0];
""",
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
"""
    }
}

###############################################################
# Rate-coded continuous transmission
###############################################################
hyb_summation_operation = {
    'sum' : """
%(pre_copy)s

// ELLPACK partition
auto post_ranks = get_post_rank();
auto maxnzr_ = ell_matrix_->get_maxnzr();
auto rl_ = ell_matrix_->get_rl();
auto col_idx_ = ell_matrix_->get_column_indices();

for(std::vector<%(idx_type)s>::size_type i = 0; i < post_ranks.size(); i++) {
    std::vector<%(idx_type)s>::size_type rk_post = post_ranks[i]; // Get postsynaptic rank

    sum = 0.0;
    for(std::vector<%(idx_type)s>::size_type j = i*maxnzr_; j < i*maxnzr_+rl_[i]; j++) {
        %(idx_type)s rk_pre = col_idx_[j];
        sum += %(ell_psp)s ;
    }
    pop%(id_post)s._sum_%(target)s%(ell_post_index)s += sum;
}

// Coordinate partition
auto nnz = coo_matrix_->nb_synapses();
auto row_it = coo_matrix_->get_row_indices();
auto col_it = coo_matrix_->get_column_indices();

for(int j = 0; j < nnz; j++, row_it++, col_it++) {
    pop%(id_post)s._sum_%(target)s%(coo_post_index)s += %(coo_psp)s;
}
""",
    'max': "",
    'min': "",
    'mean': "",
}

conn_templates = {
    # accessors
    'attribute_decl': attribute_decl,
    'attribute_cpp_init': attribute_cpp_init,
    'attribute_cpp_size': attribute_cpp_size,
    'delay': delay,
    
    'rate_coded_sum': hyb_summation_operation,
    'update_variables': ""
}