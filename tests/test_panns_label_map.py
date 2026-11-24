import numpy as np

from acousticbench.models.panns_cnn14 import CLASSES, load_label_names, noise_label, room_label


def test_audioset_names_match_the_checkpoint_order():
    names = load_label_names()
    assert len(names) == CLASSES
    assert names[0] == "Speech"
    assert names[412] == "Mechanical fan"
    assert names[506] == "Inside, small room"


def test_noise_map_uses_the_audio_set_names():
    names = load_label_names()
    clip = np.zeros(CLASSES, dtype=np.float32)
    clip[names.index("Hubbub, speech noise, speech babble")] = 0.8
    clip[names.index("Mechanical fan")] = 0.2
    label, scores = noise_label(clip, names)
    assert label == "babble"
    assert abs(scores["babble"] - 0.8) < 1e-6


def test_room_map_uses_a_fixed_two_to_one_lead():
    names = load_label_names()
    clip = np.zeros(CLASSES, dtype=np.float32)
    clip[names.index("Inside, large room or hall")] = 0.4
    clip[names.index("Inside, small room")] = 0.1
    assert room_label(clip, names)[0] == "large"
    clip[names.index("Inside, small room")] = 0.3
    assert room_label(clip, names)[0] == "medium"
