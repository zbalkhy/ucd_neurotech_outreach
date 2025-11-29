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

# User model declares:
# if a user overrides a stream with the same name, the program loses...
# track of the old stream thread and cannot quit
    def test_add_stream_with_same_name(self):
        self.user_model.notify = MagicMock()
        stream_name = "stream"
        data_stream1 = DataStream(stream_name, StreamType.SOFTWARE, 100)
        #want to magicmock stream1 to mimic it, then test to see if stop() is called
        data_stream2 = DataStream(stream_name, StreamType.DEVICE, 100)
        self.user_model.add_stream(data_stream1)
        self.user_model.add_stream(data_stream2)

        self.assertIs(self.user_model.data_streams[stream_name], data_stream2)
        


    #def test_add_stream(self):
        
if __name__ == '__main__':
    unittest.main()