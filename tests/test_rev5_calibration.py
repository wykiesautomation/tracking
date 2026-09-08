from types import SimpleNamespace
from app.calibration import validate_points,interpolate

def test_calibration_validation_and_interpolation():
 pts=[SimpleNamespace(raw_value=0,percent=0,litres=0),SimpleNamespace(raw_value=5,percent=100,litres=600)]
 errors,_=validate_points(pts,600);assert errors==[]
 percent,litres,quality=interpolate(2.5,pts);assert percent==50 and litres==300 and quality=='GOOD'

def test_non_monotonic_rejected():
 pts=[SimpleNamespace(raw_value=0,percent=0,litres=100),SimpleNamespace(raw_value=5,percent=100,litres=50)]
 errors,_=validate_points(pts,600);assert errors
