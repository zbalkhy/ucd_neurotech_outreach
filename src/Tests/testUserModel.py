import unittest
from unittest.mock import MagicMock
from Classes.eventClass import EventType
from Classes.filterClass import FilterClass
from Models.userModel import UserModel
from Stream.dataStream import DataStream, StreamType

class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.user_model = UserModel()
    def tearDown(self):
        self.user_model = None


    def test_get_stream(self):
        stream_name1 = "stream1"
        stream_name2 = 'stream2'
        #create some streams and add to data_streams_dictionary
        data_stream1 = DataStream(stream_name1, StreamType.DEVICE, 100)
        data_stream2 = DataStream(stream_name2, StreamType.SOFTWARE, 100)
        self.user_model.add_stream(data_stream1)
        self.user_model.add_stream(data_stream2)
        returned_stream = self.user_model.get_stream(stream_name2)
        self.assertEqual(returned_stream, data_stream2)
        self.assertNotEqual(returned_stream,data_stream1) 

        #Test get_streams
        returned_streams = self.user_model.get_streams()
        self.assertEqual(returned_streams, [data_stream1, data_stream2])


    def test_stream_not_found(self):
        returned_stream = self.user_model.get_stream("empty")
        self.assertIsNone(returned_stream)


    def test_add_stream(self):
        self.user_model.notify = MagicMock()
        stream_name = "stream"
        old_stream = DataStream(stream_name, StreamType.SOFTWARE, 100)
        new_stream = DataStream(stream_name, StreamType.DEVICE, 100)
        old_stream.stop = MagicMock()
        self.user_model.add_stream(old_stream)
        self.user_model.add_stream(new_stream)

        self.assertIn(stream_name, self.user_model.data_streams.keys())
        self.assertIs(new_stream, self.user_model.data_streams[stream_name])
        # Old stream with same name should be removed
        self.assertNotIn(old_stream, self.user_model.data_streams.values())
        old_stream.stop.assert_called_once()


    def test_rename_stream(self):
        old_name = "old stream"
        new_name = "new stream"
        self.user_model.notify = MagicMock()
        data_stream = DataStream(old_name, StreamType.SOFTWARE, 100)
        self.user_model.data_streams[old_name] = data_stream
        # Returns true if renamed
        result = self.user_model.rename_stream(old_name, new_name)

        self.assertTrue(result)
        self.assertNotIn(old_name, self.user_model.data_streams.keys())
        self.assertIn(new_name, self.user_model.data_streams.keys())
        # Same object with a new name
        self.assertIs(data_stream, self.user_model.data_streams[new_name])
        self.user_model.notify.assert_called_once_with(
            self.user_model, EventType.STREAMUPDATE
        )


    def test_rename_stream_returns_false(self):
        result = self.user_model.rename_stream("missing name", "new")
        self.assertFalse(result)

        old_name = "old stream"
        new_name = "new stream"
        data_stream1 = DataStream(old_name, StreamType.SOFTWARE, 100)
        data_stream2 = DataStream(new_name, StreamType.DEVICE, 100)
        self.user_model.data_streams[old_name] = data_stream1
        self.user_model.data_streams[new_name] = data_stream2

        result = self.user_model.rename_stream(old_name, new_name)
        self.assertFalse(result)


    def test_remove_stream_by_name(self):
        # Return False when stream not found
        result = self.user_model.remove_stream_by_name("no name")
        self.assertFalse(result)

        stream_name = "stream"
        self.user_model.notify = MagicMock()
        data_stream = DataStream(stream_name, StreamType.FILTER, 100)
        data_stream.stop = MagicMock()
        self.user_model.data_streams[stream_name] = data_stream

        # Returns True when stream successfully removed
        result = self.user_model.remove_stream_by_name(stream_name)
        self.assertTrue(result)
        self.assertNotIn(data_stream, self.user_model.data_streams)
        data_stream.stop.assert_called_once()
        self.user_model.notify.assert_called_once_with(
            self.user_model, EventType.STREAMUPDATE)

    # add_filters() not implemented yet inside add_filter function
    # def test_add_filter(self):
    #     pass

    def test_remove_filter(self):
        # remove_filter function currently deletes an entire category in the 'filters' dictionary
        # Is removing only one filter from the category intended?
        # Populate filters dictionary
        filter = FilterClass("filterA")
        filter.add_filters("filter", "low pass")
        filter.add_filters("order", 2)
        filter.add_filters("frequency", 20)

        self.user_model.filters["filterA"] = filter

        self.user_model.remove_filter("filterA")
        self.assertNotIn("filterA", self.user_model.filters.keys())

    # def test_get_filter(self):
    #     pass

    # def test_delete_dataset(self):
    #     pass

    # def test_add_dataset(self):
    #     pass

    # def test_get_dataset(self):
    #     pass

    # def test_rename_dataset(self):
    #     pass

    # def test_get_datasets(self):
    #     pass

    # def test_get_features(self):
    #     pass

    # def test_remove_classifier(self):
    #     pass

    # def test_add_classifier(self):
    #     pass

    # def test_get_classifier(self):
    #     pass

    # def test_get_classifiers(self):
    #     pass

    # def test_rename_classifier(self):
    #     pass
        
if __name__ == '__main__':
    unittest.main()