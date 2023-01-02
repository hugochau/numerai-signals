"""
conftest.py

Pytest metadata
"""

def pytest_addoption(parser):
    parser.addoption('--start', action='store_const', const=True, default='220101')
    parser.addoption('--end', action='store_const', const=True, default='220101')
    parser.addoption('--ticker', action='store_const', const=True, default='000060.KS')


def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    option_value = metafunc.config.option.start
    if 'start' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("start", [option_value])