from __future__ import absolute_import
import os
import datetime
import shutil

from lisfloodutilities.compare import NetCDFComparator

from lisflood.global_modules.settings import MaskInfo
from lisflood.main import lisfloodexe

from tests import TestSettings, mk_path_out


class TestStepsDates(TestSettings):
    settings_files = {
        'full': os.path.join(os.path.dirname(__file__), 'data/settings/full.xml')
    }

    def test_dates_steps_day(self):
        settings_a = self.setoptions(self.settings_files['full'],
                                     opts_to_set=['repStateMaps', 'repEndMaps', 'repDischargeMaps',
                                                  'repSnowMaps', 'repLZMaps', 'repUZMaps'],
                                     opts_to_unset=['simulateLakes'],
                                     vars_to_set={'PathOut': '$(PathRoot)/outputs/1'}
                                     )
        path_out_a = mk_path_out('data/TestCatchment/outputs/1')
        lisfloodexe(settings_a)
        settings_b = self.setoptions(self.settings_files['full'],
                                     opts_to_set=['repStateMaps', 'repEndMaps', 'repDischargeMaps',
                                                  'repSnowMaps', 'repLZMaps', 'repUZMaps'],
                                     opts_to_unset=['simulateLakes'],
                                     vars_to_set={'StepStart': 213, 'StepEnd': 215,
                                                  'PathOut': '$(PathRoot)/outputs/2'})
        path_out_b = mk_path_out('data/TestCatchment/outputs/2')

        lisfloodexe(settings_b)

        assert settings_a.step_start_int == 213
        assert settings_a.step_end_int == 215
        assert settings_a.step_start == settings_a.step_start_dt.strftime('%d/%m/%Y %H:%M')
        assert settings_a.step_end == settings_a.step_end_dt.strftime('%d/%m/%Y %H:%M')
        assert settings_b.step_start_dt == datetime.datetime(2000, 7, 30, 6, 0)
        assert settings_b.step_end_dt == datetime.datetime(2000, 8, 1, 6, 0)

        maskinfo = MaskInfo.instance()
        comparator = NetCDFComparator(maskinfo.info.mask)
        out_a = settings_a.output_dir
        out_b = settings_b.output_dir
        comparator.compare_dirs(out_a, out_b)

        shutil.rmtree(path_out_a)
        shutil.rmtree(path_out_b)
