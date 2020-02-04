import os
import datetime

from lisfloodutilities.compare import NetCDFComparator

from lisflood.global_modules.settings import MaskInfo
from lisflood.main import lisfloodexe

from tests import TestSettings

settings_file = os.path.join(os.path.dirname(__file__), 'data/settings/full.xml')
settings_file_6hourly = os.path.join(os.path.dirname(__file__), 'data/settings/full_6h.xml')


class TestStepsDates(TestSettings):

    def setup_method(self):
        settings = self.setoptions(settings_file)
        rm_files = [os.path.join(settings.output_dir, f) for f in os.listdir(settings.output_dir) if f.endswith('.nc') or f.endswith('.tss')]
        for f in rm_files:
            os.unlink(f)

    def teardown_method(self):
        settings = self.setoptions(settings_file)
        rm_files = [os.path.join(settings.output_dir, f) for f in os.listdir(settings.output_dir) if f.endswith('.nc') or f.endswith('.tss')]
        for f in rm_files:
            os.unlink(f)

    def test_dates_steps_day(self):
        settings_a = self.setoptions(settings_file,
                                     opts_to_set=['repStateMaps', 'repEndMaps', 'repDischargeMaps',
                                                  'repSnowMaps', 'repLZMaps', 'repUZMaps'],
                                     opts_to_unset=['simulateLakes'])
        lisfloodexe(settings_a)
        settings_b = self.setoptions(settings_file,
                                     opts_to_set=['repStateMaps', 'repEndMaps', 'repDischargeMaps',
                                                  'repSnowMaps', 'repLZMaps', 'repUZMaps'],
                                     opts_to_unset=['simulateLakes'],
                                     vars_to_set={'StepStart': 213, 'StepEnd': 215,
                                                  'PathOut': '$(PathRoot)/outputs/compare'})

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
        errors = comparator.compare_dirs(out_a, out_b)
        assert not errors

        rm_files = [os.path.join(out_a, f) for f in os.listdir(out_a) if f.endswith('.nc') or f.endswith('.tss')]
        rm_files += [os.path.join(out_b, f) for f in os.listdir(out_b) if f.endswith('.nc') or f.endswith('.tss')]
        for f in rm_files:
            os.unlink(f)
