"""

Copyright 2019-2020 European Union

Licensed under the EUPL, Version 1.2 or as soon they will be approved by the European Commission  subsequent versions of the EUPL (the "Licence");

You may not use this work except in compliance with the Licence.
You may obtain a copy of the Licence at:

https://joinup.ec.europa.eu/sites/default/files/inline-files/EUPL%20v1_2%20EN(1).txt

Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the Licence for the specific language governing permissions and limitations under the Licence.

"""

from __future__ import absolute_import
import os
import shutil
from datetime import timedelta

import pytest

from lisfloodutilities.compare import NetCDFComparator

from lisflood.global_modules.settings import MaskInfo
from lisflood.main import lisfloodexe

from . import TestSettings, mk_path_out


@pytest.mark.slow
class TestWarmStartDays(TestSettings):
    settings_files = {
        'prerun': os.path.join(os.path.dirname(__file__), 'data/settings/prerun.xml'),
        'cold': os.path.join(os.path.dirname(__file__), 'data/settings/cold.xml'),
        'warm': os.path.join(os.path.dirname(__file__), 'data/settings/warm.xml')
    }

    def test_warmstart(self):
        step_start = '02/01/2000 06:00'
        step_end = '30/12/2000 06:00'
        dt_sec = 86400
        modules_to_unset = [
            # 'SplitRouting',
            'simulateReservoirs',
            'simulateLakes',
            # 'wateruse',
            # 'groundwaterSmooth',
            # 'wateruseRegion',
            # 'TransientWaterDemandChange',
            # 'drainedIrrigation',
            # 'openwaterevapo'
            # 'useWaterDemandAveYear',
            # 'riceIrrigation',
        ]

        # init
        path_out_init = mk_path_out('data/TestCatchment/outputs/init')
        settings_prerun = self.setoptions(self.settings_files['prerun'], opts_to_unset=modules_to_unset,
                                          vars_to_set={'DtSec': dt_sec,
                                                       'PathOut': path_out_init,
                                                       'StepStart': step_start,
                                                       'StepEnd': step_end})
        step_end_dt = settings_prerun.step_end_dt
        lisfloodexe(settings_prerun)

        # long run
        lzavin_path = settings_prerun.binding['LZAvInflowMap']
        avgdis_path = settings_prerun.binding['AvgDis']
        path_out_reference = mk_path_out('data/TestCatchment/outputs/longrun_reference')
        settings_longrun = self.setoptions(self.settings_files['cold'], opts_to_unset=modules_to_unset,
                                           vars_to_set={'StepStart': step_start,
                                                        'StepEnd': step_end,
                                                        'LZAvInflowMap': lzavin_path,
                                                        'PathOut': path_out_reference,
                                                        'AvgDis': avgdis_path,
                                                        'DtSec': dt_sec})
        lisfloodexe(settings_longrun)

        # warm run (1. Cold start)
        run_number = 1
        cold_start_step_end = step_start
        path_out = mk_path_out('data/TestCatchment/outputs/run_{}'.format(run_number))
        settings_coldstart = self.setoptions(self.settings_files['cold'], opts_to_unset=modules_to_unset,
                                             vars_to_set={'StepStart': step_start,
                                                          'StepEnd': cold_start_step_end,
                                                          'LZAvInflowMap': lzavin_path,
                                                          'PathOut': path_out,
                                                          'AvgDis': avgdis_path,
                                                          'DtSec': dt_sec})
        lisfloodexe(settings_coldstart)

        # warm run (2. single step warm start/stop with initial conditions from previous run)
        prev_settings = settings_coldstart
        warm_step_start = prev_settings.step_end_dt + timedelta(seconds=dt_sec)
        warm_step_end = warm_step_start
        timestep_init = prev_settings.step_end_dt.strftime('%d/%m/%Y %H:%M')
        maskinfo = MaskInfo.instance()
        comparator = NetCDFComparator(maskinfo.info.mask, for_testing=True)
        while warm_step_start <= step_end_dt:
            run_number += 1
            path_init = prev_settings.output_dir
            path_out = mk_path_out('data/TestCatchment/outputs/run_{}'.format(run_number))

            settings_warmstart = self.setoptions(self.settings_files['warm'], opts_to_unset=modules_to_unset,
                                                 vars_to_set={'StepStart': warm_step_start.strftime('%d/%m/%Y %H:%M'),
                                                              'StepEnd': warm_step_end.strftime('%d/%m/%Y %H:%M'),
                                                              'LZAvInflowMap': lzavin_path,
                                                              'PathOut': path_out,
                                                              'PathInit': path_init,
                                                              'timestepInit': timestep_init,
                                                              'AvgDis': avgdis_path,
                                                              'DtSec': dt_sec})
            lisfloodexe(settings_warmstart)

            # checking values at current timestep (using datetime)
            timestep = settings_warmstart.step_end_dt
            if not (run_number % 13):
                # compare every 13 timesteps to speed up test
                comparator.compare_dirs(path_out, path_out_reference, skip_missing=True, timestep=timestep)
            # remove previous output dir (we don't need it anymore after this point)
            shutil.rmtree(path_init)

            # setup for next warm start/stop
            prev_settings = settings_warmstart
            warm_step_start = prev_settings.step_end_dt + timedelta(seconds=dt_sec)
            warm_step_end = warm_step_start
            timestep_init = prev_settings.step_end_dt.strftime('%d/%m/%Y %H:%M')

        # cleaning after (move to tear_down method)
        shutil.rmtree(path_out)

    def teardown_method(self):
        super().teardown_method()
        if os.path.exists('data/TestCatchment/outputs/longrun_reference'):
            shutil.rmtree('data/TestCatchment/outputs/longrun_reference')
        if os.path.exists('data/TestCatchment/outputs/init'):
            shutil.rmtree('data/TestCatchment/outputs/init')
