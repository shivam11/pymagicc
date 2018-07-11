from os import remove
from os.path import exists, join
from subprocess import CalledProcessError

import numpy as np
import pytest
from unittest.mock import patch
import pandas as pd
import f90nml

from pymagicc.api import MAGICCBase, MAGICC6, MAGICC7, config, _clean_value

magicc_classes = [MAGICC6, MAGICC7]

@pytest.fixture(scope="function")
def magicc_base():
    yield MAGICCBase()

@pytest.fixture(scope="function", params=magicc_classes)
def magicc_class(request):
    check_available(request.param())
    yield request.param

def check_available(magicc_cls):
    if magicc_cls.executable is None or not exists(magicc_cls.original_dir):
        pytest.skip('MAGICC {} is not available'.format(magicc_cls.version))

@pytest.fixture(scope="module", params=magicc_classes)
def package(request):
    MAGICC_cls = request.param
    p = MAGICC_cls()
    check_available(p)

    p.create_copy()
    root_dir = p.root_dir
    yield p
    # Perform cleanup after tests are complete
    p.remove_temp_copy()
    assert not exists(root_dir)


def write_config(p):
    emis_key = "file_emissionscenario" if p.version == 6 \
        else "FILE_EMISSCEN"
    outpath = join(p.run_dir, "MAGTUNE_SIMPLE.CFG")
    f90nml.write({"nml_allcfgs": {
        emis_key: 'RCP26.SCEN'
    }}, outpath, force=True)

    # Write years config.
    outpath_years = join(p.run_dir, "MAGCFG_NMLYEARS.CFG")
    f90nml.write({"nml_years": {
        "startyear": 1765,
        "endyear": 2100,
        "stepsperyear": 12
    }}, outpath_years, force=True)


def test_not_initalise():
    p = MAGICC6()
    assert p.root_dir is None
    assert p.run_dir is None
    assert p.out_dir is None


def test_initalise_and_clean(package):
    # fixture package has already been initialised
    assert exists(package.run_dir)
    assert exists(join(package.run_dir, 'MAGCFG_USER.CFG'))
    assert exists(package.out_dir)


def test_run_failure(package):
    # Ensure that no MAGCFG_NMLYears.cfg is present
    if exists(join(package.run_dir, 'MAGCFG_NMLYEARS.CFG')):
        remove(join(package.run_dir, 'MAGCFG_NMLYEARS.CFG'))

    with pytest.raises(CalledProcessError):
        package.run()

    assert len(package.config.keys()) == 0


def test_run_success(package):
    write_config(package)
    results = package.run()

    assert len(results.keys()) > 1
    assert 'SURFACE_TEMP' in results

    assert len(package.config.keys()) != 0


def test_run_only(package):
    write_config(package)
    results = package.run(only=['SURFACE_TEMP'])

    assert len(results.keys()) == 1
    assert 'SURFACE_TEMP' in results


def test_override_config():
    config['EXECUTABLE_6'] = '/tmp/magicc'
    magicc = MAGICC6()

    # Stop this override impacting other tests
    del config.overrides['EXECUTABLE_6']
    assert magicc.executable == '/tmp/magicc'


def test_dont_create_dir():
    magicc = MAGICC6()
    # Dir isn't created yet
    assert magicc.root_dir is None
    magicc.create_copy()
    root_dir = magicc.root_dir
    assert exists(root_dir)
    magicc.remove_temp_copy()
    assert not exists(root_dir)
    assert magicc.root_dir is None


def test_clean_value_simple():
    assert "SF6" == _clean_value("SF6                 ")

    assert 1970 == _clean_value(1970)
    assert 2012.123 == _clean_value(2012.123)


def test_clean_value_nulls():
    in_str = [
        "SF6                 ", "SO2F2               ",
        "\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000",
        "\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000",
    ]
    expected = ["SF6", "SO2F2", "", ""]
    out_str = _clean_value(in_str)

    assert len(out_str) == len(expected)
    for o, e in zip(out_str, expected):
        assert o == e


def test_incorrect_subdir():
    config['EXECUTABLE_6'] = '/tmp/magicc'
    magicc = MAGICC6()
    try:
        with pytest.raises(AssertionError):
            magicc.create_copy()
    finally:
        del config.overrides['EXECUTABLE_6']
        magicc.remove_temp_copy()


def test_root_dir():
    with MAGICC6() as magicc:
        m2 = MAGICC6(root_dir=magicc.root_dir)

        assert m2.root_dir == magicc.root_dir

        # Does nothing
        m2.remove_temp_copy()
        # Can be called many times
        m2.remove_temp_copy()

        assert m2.root_dir is not None

def test_no_root_dir():
    assert not exists('/tmp/magicc/')
    magicc = MAGICC6(root_dir='/tmp/magicc/')

    with pytest.raises(FileNotFoundError):
        magicc.run()

@patch.object(MAGICCBase, '_diagnose_tcr_ecs_config_setup')
@patch.object(MAGICCBase, 'run')
@patch.object(MAGICCBase, '_get_tcr_ecs_from_diagnosis_results')
def test_diagnose_tcr_ecs(mock_get_tcr_ecs_from_results, mock_run, mock_diagnose_tcr_ecs_setup, magicc_base):
    mock_tcr_val = 1.8
    mock_ecs_val = 3.1
    mock_results = pd.DataFrame()

    mock_run.return_value = mock_results
    mock_get_tcr_ecs_from_results.return_value = [mock_tcr_val, mock_ecs_val]

    assert magicc_base.diagnose_tcr_ecs()['tcr'] == mock_tcr_val
    assert mock_diagnose_tcr_ecs_setup.call_count == 1
    mock_run.assert_called_with(
        only=['CO2_CONC', 'TOTAL_INCLVOLCANIC_RF', 'SURFACE_TEMP',]
    )
    assert mock_get_tcr_ecs_from_results.call_count == 1
    mock_get_tcr_ecs_from_results.assert_called_with(mock_run())

    assert magicc_base.diagnose_tcr_ecs()['ecs'] == mock_ecs_val
    assert mock_diagnose_tcr_ecs_setup.call_count == 2
    assert mock_get_tcr_ecs_from_results.call_count == 2

    results = magicc_base.diagnose_tcr_ecs()
    assert isinstance(results["timeseries"], pd.DataFrame)

@patch.object(MAGICCBase, 'set_config')
@patch.object(MAGICCBase, 'set_years')
def test_diagnose_tcr_ecs_config_setup(mock_set_years, mock_set_config, magicc_base):
    magicc_base._diagnose_tcr_ecs_config_setup()
    mock_set_years.assert_called_with(startyear=1750, endyear=4200)
    mock_set_config.assert_called_with(
        FILE_CO2_CONC="TCRECS_CO2_CONC.IN",
        RF_TOTAL_RUNMODUS="CO2",
        RF_TOTAL_CONSTANTAFTERYR=2000,
    )

@pytest.fixture
def valid_tcr_ecs_diagnosis_results():
    startyear = 1700
    endyear = 4000
    spin_up_time = 50
    rising_time = 70
    tcr_yr = startyear + spin_up_time + rising_time
    ecs_yr = endyear
    fake_PI_conc = 278.
    eqm_time = endyear - startyear - spin_up_time - rising_time

    fake_time = np.arange(startyear, endyear+1)
    fake_concs = np.concatenate((
        fake_PI_conc*np.ones(spin_up_time),
        fake_PI_conc*1.01**(np.arange(rising_time+1)),
        fake_PI_conc*1.01**(rising_time)*np.ones(eqm_time),
    ))
    fake_rf = 2.*np.log(fake_concs/fake_PI_conc)
    fake_temp = np.log(fake_rf+1.) + fake_time / fake_time[1400]

    mock_results = {}
    mock_results['CO2_CONC'] = pd.DataFrame(
        {'GLOBAL': fake_concs},
        index=fake_time,
    )
    mock_results['TOTAL_INCLVOLCANIC_RF'] = pd.DataFrame(
        {'GLOBAL': fake_rf},
        index=fake_time,
    )
    mock_results['SURFACE_TEMP'] = pd.DataFrame(
        {'GLOBAL': fake_temp},
        index=fake_time,
    )
    yield {
        'mock_results': mock_results,
        'tcr_yr': tcr_yr,
        'ecs_yr': ecs_yr,
    }

@patch.object(MAGICCBase, '_check_tcr_ecs_temp')
@patch.object(MAGICCBase, '_check_tcr_ecs_total_RF')
@patch.object(MAGICCBase, '_get_tcr_ecs_yr_from_CO2_concs')
def test_get_tcr_ecs_from_diagnosis_results(mock_get_tcr_ecs_yr_from_CO2_concs, mock_check_tcr_ecs_total_RF, mock_check_tcr_ecs_temp, valid_tcr_ecs_diagnosis_results, magicc_base):
    test_tcr_yr = valid_tcr_ecs_diagnosis_results['tcr_yr']
    test_ecs_yr = valid_tcr_ecs_diagnosis_results['ecs_yr']
    test_results_dict = valid_tcr_ecs_diagnosis_results['mock_results']

    mock_get_tcr_ecs_yr_from_CO2_concs.return_value = [
        test_tcr_yr,
        test_ecs_yr
    ]

    expected_tcr = test_results_dict['SURFACE_TEMP']['GLOBAL'].loc[test_tcr_yr]
    expected_ecs = test_results_dict['SURFACE_TEMP']['GLOBAL'].loc[test_ecs_yr]

    actual_tcr, actual_ecs = magicc_base._get_tcr_ecs_from_diagnosis_results(
        test_results_dict
    )
    assert actual_tcr  == expected_tcr
    assert actual_ecs == expected_ecs

    mock_get_tcr_ecs_yr_from_CO2_concs.assert_called_with(
        test_results_dict['CO2_CONC']['GLOBAL']
    )
    mock_check_tcr_ecs_total_RF.assert_called_with(
        test_results_dict['TOTAL_INCLVOLCANIC_RF']['GLOBAL'],
        tcr_yr=test_tcr_yr,
        ecs_yr=test_ecs_yr,
    )
    mock_check_tcr_ecs_temp.assert_called_with(
        test_results_dict['SURFACE_TEMP']['GLOBAL'],
    )

def test_get_tcr_ecs_yr_from_CO2_concs(valid_tcr_ecs_diagnosis_results, magicc_base):
    test_CO2_data = valid_tcr_ecs_diagnosis_results['mock_results']['CO2_CONC']['GLOBAL']
    actual_tcr_yr, actual_ecs_yr = magicc_base._get_tcr_ecs_yr_from_CO2_concs(
        test_CO2_data
    )
    assert actual_tcr_yr == valid_tcr_ecs_diagnosis_results['tcr_yr']
    assert actual_ecs_yr == valid_tcr_ecs_diagnosis_results['ecs_yr']

    test_time = test_CO2_data.index.values
    for year_to_break in [test_time[0], test_time[15], test_time[115], test_time[-1] - 100, test_time[-1]]:
        broken_CO2_data = test_CO2_data.copy()
        broken_CO2_data.loc[year_to_break] = test_CO2_data.loc[year_to_break] * 1.01
        with pytest.raises(ValueError, match=r'The TCR/ECS CO2 concs look wrong.*'):
            magicc_base._get_tcr_ecs_yr_from_CO2_concs(broken_CO2_data)

def test_check_tcr_ecs_total_RF(valid_tcr_ecs_diagnosis_results, magicc_base):
    test_RF_data = valid_tcr_ecs_diagnosis_results['mock_results']['TOTAL_INCLVOLCANIC_RF']['GLOBAL']
    magicc_base._check_tcr_ecs_total_RF(
        test_RF_data,
        valid_tcr_ecs_diagnosis_results['tcr_yr'],
        valid_tcr_ecs_diagnosis_results['ecs_yr'],
    )
    test_time = test_RF_data.index.values
    for year_to_break in [test_time[0], test_time[15], test_time[115], test_time[-1] - 100, test_time[-1]]:
        broken_CO2_data = test_RF_data.copy()
        broken_CO2_data.loc[year_to_break] = test_RF_data.loc[year_to_break] * 1.01 + 0.01
        with pytest.raises(ValueError, match=r'The TCR/ECS total radiative forcing looks wrong.*'):
            magicc_base._check_tcr_ecs_total_RF(
                broken_CO2_data,
                valid_tcr_ecs_diagnosis_results['tcr_yr'],
                valid_tcr_ecs_diagnosis_results['ecs_yr'],
            )

def test_check_tcr_ecs_temp(valid_tcr_ecs_diagnosis_results, magicc_base):
    test_temp_data = valid_tcr_ecs_diagnosis_results['mock_results']['SURFACE_TEMP']['GLOBAL']
    magicc_base._check_tcr_ecs_temp(test_temp_data)

    test_time = test_temp_data.index.values
    for year_to_break in [test_time[3], test_time[15], test_time[115], test_time[-1] - 100, test_time[-1]]:
        broken_temp_data = test_temp_data.copy()
        broken_temp_data.loc[year_to_break] = test_temp_data.loc[year_to_break-1] - 0.1
        with pytest.raises(ValueError, match=r'The TCR/ECS surface temperature looks wrong, it decreases'):
            magicc_base._check_tcr_ecs_temp(broken_temp_data)

# integration test (i.e. actually runs magicc) hence slow
@pytest.mark.slow
def test_integration_diagnose_tcr_ecs(package):
    actual_result = package.diagnose_tcr_ecs()
    assert isinstance(actual_result, dict)
    assert 'tcr' in actual_result
    assert 'ecs' in actual_result
    assert actual_result['tcr'] < actual_result['ecs']
    if isinstance(package, MAGICC6):
        assert actual_result['tcr'] == 1.9733976000000002 # MAGICC6 shipped with pymagicc should be stable
        assert actual_result['ecs'] == 2.9968448 # MAGICC6 shipped with pymagicc should be stable

def test_persistant_state(magicc_class):
    with magicc_class() as magicc:
        test_ecs = 1.75
        magicc.set_config(
            CORE_CLIMATESENSITIVITY=test_ecs,
        )
        actual_results = magicc.diagnose_tcr_ecs()
        assert actual_results['ecs'] == test_ecs # test will need to change to handle numerical precision when fixed
