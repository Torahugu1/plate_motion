from plate_motion import belong_plate_name, plate_motion


def test_belong_plate_name():
    # KHABAROVSK
    lat = 48.330
    lon = 135.046
    assert "Amur" == belong_plate_name(lat, lon)


def test_plate_motion():
    # KHABAROVSK
    print(plate_motion("Amur", 48.330, 135.046, 0))
    # EFFELSBERG
    print(plate_motion("Eurasia", 50.336, 6.884, 0))
    # DARWIN
    print(plate_motion("Australia", [-12.761, -12.761], [131.133, 131.133], [0, 0]))  # type: ignore
