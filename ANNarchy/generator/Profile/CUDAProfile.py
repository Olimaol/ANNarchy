#===============================================================================
#
#     CUDAProfile.py
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
from ANNarchy.core import Global

from .ProfileGenerator import ProfileGenerator
from .ProfileTemplate import profile_base_template, cuda_profile_template, cuda_profile_header

class CUDAProfile(ProfileGenerator):

    def __init__(self, annarchy_dir, net_id):
        ProfileGenerator.__init__(self, annarchy_dir, net_id)

    def generate(self):
        """
        Generate Profiling class code, called from Generator instance.
        """
        # Generate header for profiling
        with open(self.annarchy_dir+'/generate/net'+str(self._net_id)+'/Profiling.h', 'w') as ofile:
            ofile.write(self._generate_header())

    def generate_body_dict(self):
        """
        Creates a dictionary, contain profile code snippets.
        """
        body_dict = {
            'prof_include': cuda_profile_template['include'],
            'prof_step_pre': cuda_profile_template['step_pre'],
            'prof_step_post': cuda_profile_template['step_post'],
            'prof_run_pre': cuda_profile_template['run_pre'],
            'prof_run_post': cuda_profile_template['run_post'],
            'prof_proj_psp_pre': cuda_profile_template['proj_psp_pre'],
            'prof_proj_psp_post': cuda_profile_template['proj_psp_post'],
            'prof_proj_step_pre': cuda_profile_template['proj_step_pre'],
            'prof_proj_step_post': cuda_profile_template['proj_step_post'],
            'prof_neur_step_pre': cuda_profile_template['neur_step_pre'],
            'prof_neur_step_post': cuda_profile_template['neur_step_post']
        }
        return body_dict

    def generate_init_network(self):
        return cuda_profile_template['init']

    def generate_init_population(self, pop):
        declare = """
    Measurement* measure_step;
    Measurement* measure_gather;
"""
        init = """        // Profiling
        measure_step = Profiling::get_instance()->register_function("pop", "%(name)s", %(id)s, "step", "%(label)s");
        measure_gather = Profiling::get_instance()->register_function("pop", "%(name)s",  %(id)s, "gather", "%(label)s");
""" % {'name': pop.name, 'id': pop.id, 'label': pop.name}

        return declare, init

    def generate_init_projection(self, proj):
        """
        Generate initialization code for projection
        """
        declare = """
    Measurement* measure_psp;
    Measurement* measure_step;
"""
        if isinstance(proj.target, str):
            target = proj.target
        else:
            target = proj.target[0]
            for tar in proj.target[1:]:
                target += "_"+tar

        init = """        // Profiling
        measure_psp = Profiling::get_instance()->register_function("proj", "%(name)s", %(id_proj)s, "psp", "%(label)s");
        measure_step = Profiling::get_instance()->register_function("proj", "%(name)s", %(id_proj)s, "step", "%(label)s");
""" % {'id_proj': proj.id, 'name': proj.name, 'label': proj.pre.name+'_'+proj.post.name+'_'+target}

        return declare, init

    def annotate_computesum_rate(self, proj, code):
        """
        annotate the computesum compuation code
        """
        prof_begin = cuda_profile_template['compute_psp']['before'] % {'id':proj.id, 'name': 'proj'+str(proj.id)}
        prof_end = cuda_profile_template['compute_psp']['after'] % {'id':proj.id, 'name': 'proj'+str(proj.id)}

        prof_code = """
        // first run, measuring average time
        %(prof_begin)s
%(code)s
        %(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }
        return prof_code

    def annotate_computesum_spiking(self, proj, code):
        """
        annotate the computesum compuation code
        """
        prof_begin = cuda_profile_template['compute_psp']['before'] % {'id':proj.id, 'name': 'proj'+str(proj.id)}
        prof_end = cuda_profile_template['compute_psp']['after'] % {'id':proj.id, 'name': 'proj'+str(proj.id)}

        prof_code = """
        // first run, measuring average time
        %(prof_begin)s
%(code)s
        %(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }
        return prof_code

    def annotate_update_synapse(self, proj, code):
        """
        annotate the update synapse code, generated by ProjectionGenerator.update_synapse()
        """
        prof_begin = cuda_profile_template['update_synapse']['before'] % {'id':proj.id, 'name': 'proj'+str(proj.id)}
        prof_end = cuda_profile_template['update_synapse']['after'] % {'id':proj.id, 'name': 'proj'+str(proj.id)}

        prof_code = """
// first run, measuring average time
%(prof_begin)s
%(code)s
%(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }

        return prof_code

    def annotate_update_neuron(self, pop, code):
        """
        annotate the update neuron code
        """
        prof_begin = cuda_profile_template['update_neuron']['before'] % {'id': pop.id, 'name': pop.name}
        prof_end = cuda_profile_template['update_neuron']['after'] % {'id': pop.id, 'name': pop.name}

        prof_code = """
        // first run, measuring average time
    %(prof_begin)s
%(code)s
    %(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }
        return prof_code

    def annotate_spike_gather(self, pop, code):
        """
        annotate the update neuron code
        """
        prof_begin = cuda_profile_template['spike_gather']['before'] % {'id': pop.id, 'name': pop.name}
        prof_end = cuda_profile_template['spike_gather']['after'] % {'id': pop.id, 'name': pop.name}

        prof_code = """
        // first run, measuring average time
    %(prof_begin)s
%(code)s
    %(prof_end)s
""" % {'code': code,
       'prof_begin': prof_begin,
       'prof_end': prof_end
       }
        return prof_code

    def _generate_header(self):
        """
        generate Profiling.h
        """
        config_xml = """
        _out_file << "  <config>" << std::endl;
        _out_file << "    <paradigm>%(paradigm)s</paradigm>" << std::endl;
        _out_file << "  </config>" << std::endl;
        """ % {'paradigm': Global.config["paradigm"]}

        timer_import = "#include <cuda_runtime_api.h>"
        timer_start = "cudaEvent_t _profiler_start;"
        timer_init = """
        cudaEventCreate(&_profiler_start);
        cudaEventRecord(_profiler_start);
"""

        config = Global.config["paradigm"]
        return profile_base_template % {
            'timer_import': timer_import,
            'timer_start_decl': timer_start,
            'timer_init': timer_init,
            'config': config,
            'config_xml': config_xml,
            'measurement_class': cuda_profile_header
        }
