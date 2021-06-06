# TODO: mark this as slow using pytest.mark, only run if specifically indicated
#
# from lhorizon import LHorizon
# from lhorizon.tests.data import test_cases
#
# class TestLHorizonOnline:
#
#     def test_ephemerides_query(self):
#         case = test_cases.CERES_2000
#         test_lhorizon = LHorizon(**case['init_kwargs'])
#         df = test_lhorizon.dataframe()
#         table = test_lhorizon.table()
#