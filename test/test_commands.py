
import unittest
from unittest.mock import Mock

import app.commands as cmds
import Murmur

class MockServer(Murmur.Server):
    def sendMessageChannel(self, channel, tree, text):
        self.text = text

    def sendMessage(self, session, text):
        self.text = text

    def getUsers():
        return [create_mock_user()]


def create_mock_text(text):
    return Murmur.TextMessage([0], [0], [], text)

def create_mock_user():
    user = Murmur.User()
    user.name = 'Mock'

    return user

class CommandsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_hello(self):
        server = MockServer()
        user = create_mock_user()

        text = create_mock_text('hi')
        cmds.publish(server, user, text)

        self.assertTrue(len(server.text) > 0)



