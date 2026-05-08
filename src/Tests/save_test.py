
import os
import pytest
import numpy as np
import shutil
from Models.userModel import UserModel
from Models.saveModel import SaveModel, USER_SAVE_PATH
from Stream.dataStream import DataStream, StreamType
from Classes.filterClass import FilterClass
from Classes.featureClass import FeatureClass, FeatureType
from Classes.classifierClass import Classifier, MODEL_SAVE_DIR

# super basic unit tests just to make sure stuff ends up dumped to json,
# no tkinter


@pytest.fixture
def setup_teardown():
    if os.path.exists(USER_SAVE_PATH):
        os.remove(USER_SAVE_PATH)
    if os.path.exists(MODEL_SAVE_DIR):
        shutil.rmtree(MODEL_SAVE_DIR)

    yield

    if os.path.exists(USER_SAVE_PATH):
        os.remove(USER_SAVE_PATH)
    if os.path.exists(MODEL_SAVE_DIR):
        shutil.rmtree(MODEL_SAVE_DIR)


def test_save_empty(setup_teardown):
    user = UserModel()
    save_model = SaveModel()
    save_model.dump(user)
    loaded_user = save_model.load()
    assert isinstance(loaded_user, UserModel)
    assert len(loaded_user.data_streams) == 0
    assert len(loaded_user.filters) == 0
    assert len(loaded_user.data_sets) == 0
    assert len(loaded_user.features) == 0
    assert len(loaded_user.classifiers) == 0


def test_save_stream(setup_teardown):
    user = UserModel()
    stream = DataStream("TestStream", StreamType.SOFTWARE)
    user.add_stream(stream)
    save_model = SaveModel()
    save_model.dump(user)
    loaded_user = save_model.load()
    assert "TestStream" in loaded_user.data_streams
    loaded_stream = loaded_user.data_streams["TestStream"]
    assert loaded_stream.stream_name == "TestStream"
    assert loaded_stream.stream_type == StreamType.SOFTWARE


def test_save_filter(setup_teardown):
    user = UserModel()
    user.add_filter("TestFilter", "lowpass", 4, 30)
    save_model = SaveModel()
    save_model.dump(user)
    loaded_user = save_model.load()
    assert "TestFilter" in loaded_user.filters
    loaded_filter = loaded_user.filters["TestFilter"]
    assert loaded_filter.filter_name == "TestFilter"
    assert "lowpass" in loaded_filter.filters['filter']
    assert 4 in loaded_filter.filters['order']
    assert 30 in loaded_filter.filters['frequency']


def test_save_dataset(setup_teardown):
    user = UserModel()
    data = np.array([[1, 2, 3], [4, 5, 6]])
    user.add_dataset("TestDataset", data)
    save_model = SaveModel()
    save_model.dump(user)
    loaded_user = save_model.load()
    assert "TestDataset" in loaded_user.data_sets
    np.testing.assert_array_equal(loaded_user.data_sets["TestDataset"], data)


def test_save_feature(setup_teardown):
    user = UserModel()
    feature = FeatureClass(FeatureType.ALPHA)
    user.add_feature(feature)
    save_model = SaveModel()
    save_model.dump(user)
    loaded_user = save_model.load()
    feature_name = str(feature)
    assert feature_name in loaded_user.features
    loaded_feature = loaded_user.features[feature_name]
    assert loaded_feature.type == FeatureType.ALPHA


def test_save_classifier(setup_teardown):
    user = UserModel()
    classifier = Classifier()
    dataset0 = np.random.rand(10, 5)
    dataset1 = np.random.rand(10, 5)
    classifier.add_dataset(0, "set0", dataset0)
    classifier.add_dataset(1, "set1", dataset1)
    feature = FeatureClass(FeatureType.BETA)
    classifier.add_feature(feature)
    flt = FilterClass("CommonFilter")
    classifier.add_filter(flt)
    user.add_classifier("TestClassifier", classifier)
    save_model = SaveModel()
    save_model.dump(user)
    loaded_user = save_model.load()
    assert "TestClassifier" in loaded_user.classifiers
    loaded_classifier = loaded_user.classifiers["TestClassifier"]
    assert "set0" in loaded_classifier.label0_datasets
    np.testing.assert_array_equal(
        loaded_classifier.label0_datasets["set0"], dataset0)
    assert len(loaded_classifier.features) == 1
    assert loaded_classifier.features[0].type == FeatureType.BETA


def test_save_functions(setup_teardown):
    user = UserModel()
    user.functions["func1"] = "def func1(x): return x + 1"
    user.functions["func2"] = "def func2(y): return y * 2"

    save_model = SaveModel()
    save_model.dump(user)
    loaded_user = save_model.load()

    assert "func1" in loaded_user.functions
    assert "func2" in loaded_user.functions
    assert loaded_user.functions["func1"] == "def func1(x): return x + 1"
    assert loaded_user.functions["func2"] == "def func2(y): return y * 2"
