import pytest

from vta_collection.calibration import Calibration, ZeroCalibration
from vta_collection.calibration_utils import calculate_coefficients
from vta_collection.standard import Standard


def test_linear_coefficients_success():
    standards = [
        Standard(name="Pt1", t_theor=100.0, t_exp=99.0),  # delta = +1.0
        Standard(name="Pt2", t_theor=200.0, t_exp=197.0),  # delta = +3.0
    ]
    coeffs = calculate_coefficients(standards, "linear")
    assert len(coeffs) == 3
    assert coeffs[2] == 0.0
    # a * 99 + b = 1; a * 197 + b = 3 -> a = 2/98, b = 1 - 99*(2/98)
    a, b = coeffs[0], coeffs[1]
    assert pytest.approx(a * 99.0 + b, 1e-6) == 1.0
    assert pytest.approx(a * 197.0 + b, 1e-6) == 3.0


def test_linear_requires_min_2_points():
    standards = [Standard(name="Pt1", t_theor=100.0, t_exp=99.0)]
    with pytest.raises(ValueError, match="минимум 2"):
        calculate_coefficients(standards, "linear")


def test_linear_duplicate_t_exp():
    standards = [
        Standard(name="Pt1", t_theor=100.0, t_exp=100.0),
        Standard(name="Pt2", t_theor=105.0, t_exp=100.0),
    ]
    with pytest.raises(ValueError, match="различными экспериментальными"):
        calculate_coefficients(standards, "linear")


def test_quadratic_requires_min_3_points():
    standards = [
        Standard(name="Pt1", t_theor=100.0, t_exp=99.0),
        Standard(name="Pt2", t_theor=200.0, t_exp=198.0),
    ]
    with pytest.raises(ValueError, match="минимум 3"):
        calculate_coefficients(standards, "quadratic")


def test_quadratic_duplicate_t_exp():
    standards = [
        Standard(name="Pt1", t_theor=100.0, t_exp=100.0),
        Standard(name="Pt2", t_theor=200.0, t_exp=100.0),
        Standard(name="Pt3", t_theor=300.0, t_exp=200.0),
    ]
    with pytest.raises(ValueError, match="различными экспериментальными"):
        calculate_coefficients(standards, "quadratic")


def test_quadratic_coefficients_success():
    standards = [
        Standard(name="Pt1", t_theor=100.0, t_exp=100.0),  # delta = 0
        Standard(name="Pt2", t_theor=201.0, t_exp=200.0),  # delta = 1
        Standard(name="Pt3", t_theor=304.0, t_exp=300.0),  # delta = 4
    ]
    coeffs = calculate_coefficients(standards, "quadratic")
    assert len(coeffs) == 3
    a, b, c = coeffs[0], coeffs[1], coeffs[2]
    # delta = a*x^2 + b*x + c
    assert pytest.approx(a * (100**2) + b * 100 + c, 1e-4) == 0.0
    assert pytest.approx(a * (200**2) + b * 200 + c, 1e-4) == 1.0
    assert pytest.approx(a * (300**2) + b * 300 + c, 1e-4) == 4.0


def test_invalid_calibration_type():
    standards = [
        Standard(name="Pt1", t_theor=100.0, t_exp=99.0),
        Standard(name="Pt2", t_theor=200.0, t_exp=198.0),
    ]
    with pytest.raises(ValueError, match="linear.*quadratic"):
        calculate_coefficients(standards, "cubic")


def test_statistics_degrees_of_freedom():
    # 2 точки для linear: n=2, p=2 -> n <= p -> SEC должно быть None
    cal_2 = Calibration(
        calibration_type="linear",
        standards=[
            Standard(name="Pt1", t_theor=100.0, t_exp=98.0),
            Standard(name="Pt2", t_theor=200.0, t_exp=196.0),
        ],
    )
    cal_2.update_from_standards()
    stats_2 = cal_2.calculate_statistics()
    assert stats_2["SEC"] is None
    assert stats_2["expanded_uncertainty"] is None
    assert stats_2["n_points"] == 2
    assert stats_2["n_params"] == 2

    # 3 точки для linear: n=3, p=2 -> n > p -> SEC должно быть числом
    cal_3 = Calibration(
        calibration_type="linear",
        standards=[
            Standard(name="Pt1", t_theor=100.0, t_exp=98.0),
            Standard(name="Pt2", t_theor=200.0, t_exp=196.0),
            Standard(name="Pt3", t_theor=300.0, t_exp=297.0),
        ],
    )
    cal_3.update_from_standards()
    stats_3 = cal_3.calculate_statistics()
    assert stats_3["SEC"] is not None
    assert stats_3["SEC"] >= 0.0
    assert stats_3["expanded_uncertainty"] == pytest.approx(2.0 * stats_3["SEC"])


def test_statistics_quadratic_degrees_of_freedom():
    # 3 точки для quadratic: n=3, p=3 -> n <= p -> SEC должно быть None
    cal_quad_3 = Calibration(
        calibration_type="quadratic",
        standards=[
            Standard(name="Pt1", t_theor=100.0, t_exp=100.0),
            Standard(name="Pt2", t_theor=201.0, t_exp=200.0),
            Standard(name="Pt3", t_theor=304.0, t_exp=300.0),
        ],
    )
    cal_quad_3.update_from_standards()
    stats_3 = cal_quad_3.calculate_statistics()
    assert stats_3["SEC"] is None
    assert stats_3["expanded_uncertainty"] is None

    # 4 точки для quadratic: n=4, p=3 -> n > p -> SEC должно быть числом
    cal_quad_4 = Calibration(
        calibration_type="quadratic",
        standards=[
            Standard(name="Pt1", t_theor=100.0, t_exp=100.0),
            Standard(name="Pt2", t_theor=201.0, t_exp=200.0),
            Standard(name="Pt3", t_theor=304.0, t_exp=300.0),
            Standard(name="Pt4", t_theor=409.5, t_exp=400.0),
        ],
    )
    cal_quad_4.update_from_standards()
    stats_4 = cal_quad_4.calculate_statistics()
    assert stats_4["SEC"] is not None
    assert stats_4["SEC"] >= 0.0


def test_zero_calibration():
    zero_cal = ZeroCalibration()
    assert zero_cal.get_value(123.45) == 123.45
    assert zero_cal.to_formule_str() == "Tскор = Tэксп (без калибровки)"
