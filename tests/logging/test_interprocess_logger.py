import sys
import threading

if sys.version_info >= (3, 0):
    from unittest import TestCase, mock
else:
    import mock
    from unittest import TestCase

from cloudshell.logging.interprocess_logger import MultiProcessingLog


class TestMultiProcessingLog(TestCase):
    def setUp(self):
        self.log_file_handler = mock.Mock()

    def create_instance(self):
        with mock.patch("cloudshell.logging.interprocess_logger.logging.Handler.__init__") as log_handler_init:
            with mock.patch("cloudshell.logging.interprocess_logger.RotatingFileHandler") as log_file_handler:
                log_file_handler.return_value = self.log_file_handler
                name = mock.Mock()
                mode = mock.Mock()
                instance = MultiProcessingLog(name, mode)
                log_handler_init.assert_called_once_with(instance)
                log_file_handler.assert_called_once_with(name, mode, 0, 0)
        return instance

    @mock.patch("cloudshell.logging.interprocess_logger.threading")
    @mock.patch("cloudshell.logging.interprocess_logger.MultiProcessingLog.receive")
    def test_init(self, receive, threading):
        thread = mock.Mock()
        threading.Thread.return_value = thread
        instance = self.create_instance()
        self.assertIs(instance._handler, self.log_file_handler)
        threading.Thread.assert_called_once_with(target=receive)
        self.assertIs(thread, instance._receive_thread)
        self.assertEqual(thread.daemon, True)
        thread.start.assert_called_once_with()


class TestMultiProcessingLogThreads(TestCase):
    THREADS = 100
    MESSAGES_PER_THREAD = 200

    def setUp(self):
        test = TestMultiProcessingLog()
        test.setUp()
        self.handler = test.log_file_handler
        self.instance = test.create_instance()
        self.messages = []

    @mock.patch("cloudshell.logging.interprocess_logger.logging.Handler")
    def test_multi_thread_call_count(self, handler):
        self.handler.emit = self._emmit_mess
        self._send_multi_cl_mess_and_close()
        self.assertEqual(len(self.messages), self.THREADS * self.MESSAGES_PER_THREAD)

    def _send_multi_cl_mess_and_close(self):
        thread_list = []
        for cl_id in range(self.THREADS):
            thread_list.append(
                threading.Thread(target=self._send_messages_for_cl, args=(cl_id, self.MESSAGES_PER_THREAD)))
        list(map(lambda th: th.start(), thread_list))
        list(map(lambda th: th.join(), thread_list))
        self.instance.close()

    def _send_messages_for_cl(self, cl_id, mess_count):
        for mes_id in range(mess_count):
            self.instance.send("{}:{}".format(cl_id, mess_count))

    def _emmit_mess(self, mess):
        self.messages.append(mess)
