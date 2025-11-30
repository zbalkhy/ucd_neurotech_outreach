import unittest
from userModel import UserModel
from dataStream import DataStream, StreamType
from unittest.mock import MagicMock
from eventClass import EventType

class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.user_model = UserModel()

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
        stream_name = "stream1"
        data_stream1 = DataStream(stream_name, StreamType.SOFTWARE, 100)
        self.user_model.add_stream(data_stream1)
        self.assertIs(data_stream1, self.user_model.data_streams[stream_name])

        self.user_model.notify.assert_any_call(None, EventType.STREAMUPDATE)
        self.user_model.notify.assert_any_call(None, EventType.DEVICELISTUPDATE)
        self.assertEqual(self.user_model.notify.call_count,2)

# # User model declares:
# # if a user overrides a stream with the same name, the program loses track of the old stream thread and cannot quit
# # test whether the implemented check works
#     def test_add_stream_with_same_name(self):
#         self.user_model.notify = MagicMock()
#         stream_name = "stream"
#         old_stream = DataStream(stream_name, StreamType.SOFTWARE, 100)
#         new_stream = DataStream(stream_name, StreamType.DEVICE, 100)
#         self.user_model.add_stream(old_stream)
#         self.user_model.add_stream(new_stream)

#         self.assertNotIn(self.user_model.data_streams[stream_name], data_stream2)
        
    def test_remove_stream_by_name(self):
        #remove_stream_by_name has a shutdown event, checks if stream is alive, and a join event
        # Check that these are accounted for
        stream_name = "stream"
        data_stream1 = MagicMock(spec=DataStream)
        data_stream1.shutdown_event = MagicMock()
        data_stream1.is_alive = MagicMock(return_value = True)
        data_stream1.join = MagicMock()
        self.user_model.data_streams[stream_name] = data_stream1

        self.user_model.remove_stream_by_name(stream_name)
        self.assertNotIn(stream_name, self.user_model.data_streams)
        data_stream1.shutdown_event.set.assert_called_once()
        data_stream1.is_alive.assert_called_once()
        data_stream1.join.assert_called_once()




        
if __name__ == '__main__':
    unittest.main()