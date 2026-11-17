from acousticbench.ace_prepare import match_rir_filename
from acousticbench.sim.sabine import sabine_t60


def test_sabine_matches_the_standard_formula():
    # 4 m by 5 m by 3 m, absorption 0.2.
    # Volume 60. Surface 94. T60 = 0.161 * 60 / 18.8.
    assert abs(sabine_t60((4.0, 5.0, 3.0), 0.2) - (0.161 * 60 / 18.8)) < 1e-12


def test_ace_filename_matches_one_room_config():
    labels = [
        {"room_code": "502", "room_name": "Office_1", "config": "1", "t60": 0.364},
        {"room_code": "502", "room_name": "Office_1", "config": "2", "t60": 0.310},
        {"room_code": "503", "room_name": "Meeting_Room_1", "config": "1", "t60": 0.450},
    ]
    office = match_rir_filename("502_1_RIR_Single.wav", labels)
    assert office["room_name"] == "Office_1"
    assert office["config"] == "1"
    assert match_rir_filename("502_1_Ambient.wav", labels) is None
    assert match_rir_filename("503_1_RIR.wav", labels)["t60"] == 0.450
