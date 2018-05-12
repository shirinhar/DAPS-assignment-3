import io, pytest, asyncio, os, time, mock
import server
import aioconsole


# NOTE: the following tests are not compliant with the new functionalities that you will need to implement in this exercise. Feel free to remove them, and replace them with your own tests of the new functionalities.

#########
# Mocks #
#########

class FakeReader:
    def __init__(self,predefined_content_list,output_pace=0):
        self.delay = output_pace
        if predefined_content_list == None:
            self.messages = None
        else:
            self.messages = list(predefined_content_list)
    
    @asyncio.coroutine
    def read(self, length):
        yield from asyncio.sleep(self.delay)
        if self.messages == None:
            return None
        if len(self.messages) > 0:
            message = self.messages.pop(0)
            if message == None:
                return None
            return message.encode()
        return ''

class FakeWriter:
    def __init__(self,extra_info = 'fake_writer'):
        self.extra_info = extra_info
        self.writer = io.BytesIO()
        self.open()

    def write(self, data):
        return self.writer.write(data)

    def getvalue(self):
        return self.writer.getvalue()
    
    def get_extra_info(self,string):
        return self.extra_info

    @asyncio.coroutine
    def drain(self):
        self.writer.flush()

    def close(self):
        self.closed = True
    
    def open(self):
        self.closed = False

    def is_closed(self):
        return self.closed

class FakeConsole:
    def __init__(self,predefined_content=[],output_pace=0,final_message='close()'):
        self.delay = output_pace
        if predefined_content == None:
            self.messages = None
        else:
            self.messages = list(predefined_content)
        self.final_string = final_message
    
    @asyncio.coroutine
    def fake_console_read(self,prompt):
        yield from asyncio.sleep(self.delay)
        if self.messages == None:
            return None
        if len(self.messages) > 0:
            return self.messages.pop(0)
        else:
            return self.final_string
    
#########
# Tests #
#########




class TestServerClass:
    def setup_method(self,method):
        self.testserver = server.Server()
        self.loop = asyncio.get_event_loop()        
        self.fake_writer = FakeWriter('fake client 1')
        self.other_fake_writer = FakeWriter('fake client 2')
        self.testserver.all_clients = set([self.fake_writer,self.other_fake_writer])

    # get username from message
    def get_id(self,message):
        return (message[message.find("(")+1:message.find(")")])

    # Check that the server can handle setting names for users
    def test_username_setup(self,capsys):
        message = '@server set_my_id(user1)'
        fake_reader = FakeReader([message])
        self.loop.run_until_complete(self.testserver.handle_connection(
                                    fake_reader , self.fake_writer))
        assert len(self.other_fake_writer.getvalue()) == 0
        sent_message = ('@client username set to '+ self.get_id(message))
        assert sent_message.encode() in self.fake_writer.getvalue()
        assert self.fake_writer.get_extra_info('').encode() \
                                not in self.other_fake_writer.getvalue()
        expected_out_msg1 = 'Received {}'.format(message)
        expected_out_msg2 = 'Closing connection with client' 
        out, err = capsys.readouterr()
        assert expected_out_msg1 in out
        assert expected_out_msg2 in out
        assert len(err) == 0

    # If username not set error will be sent
    def test_unset_username(self,capsys):
        message = 'Hello World!'
        fake_reader = FakeReader([message])
        self.loop.run_until_complete(self.testserver.handle_connection(
                                     fake_reader, self.fake_writer))
        assert len(self.other_fake_writer.getvalue()) == 0
        sent_message = ('@client ERROR username must be set to send messages.')
        assert sent_message.encode() in self.fake_writer.getvalue()
        """assert self.fake_writer.get_extra_info('').encode() \
                                     in self.other_fake_writer.getvalue()"""
        expected_out_msg1 = 'Received {} from {}'.format(
                 message, self.fake_writer.get_extra_info(''))
        expected_out_msg2 = 'Closing connection with client' 
        out, err = capsys.readouterr()
        assert expected_out_msg1 in out
        assert expected_out_msg2 in out
        assert len(err) == 0

    def test_username_error(self,capsys):
        message1 = '@server set_my_ip(user1)'
        message2 = '@server set_my_id(user 1)'
        message3 = '@server set_my_id(client)'
        messages = [message1,message2,message3]
        fake_reader = FakeReader(messages)
        self.loop.run_until_complete(self.testserver.handle_connection(
                                    fake_reader , self.fake_writer))
        assert len(self.other_fake_writer.getvalue()) == 0
        sent_message_1 = ('@client ERROR Incorrect Input')
        sent_message_2 = ('[error] Username cannot have spaces')
        sent_message_3 = ('[error] Incorrect user name chosen. User names cannot be "server" or "client" ')
        assert sent_message_1.encode() in self.fake_writer.getvalue()
        assert sent_message_2.encode() in self.fake_writer.getvalue()
        assert sent_message_3.encode() in self.fake_writer.getvalue()
        """assert self.fake_writer.get_extra_info('').encode() \
                                                       in self.other_fake_writer.getvalue()"""
        assert self.fake_writer not in self.testserver.all_clients
        assert len(self.testserver.all_clients) == 1
        expected_out_msg1 = 'Received {} from {}'.format(
                 message1, self.fake_writer.get_extra_info(''))
        expected_out_msg2 = 'Received {} from {}'.format(
                 message2, self.fake_writer.get_extra_info(''))
        expected_out_msg3 = 'Received {} from {}'.format(
                 message3, self.fake_writer.get_extra_info(''))
        expected_out_msg4 = 'Closing connection with client' 
        out, err = capsys.readouterr()
        assert expected_out_msg1 in out
        assert expected_out_msg2 in out
        assert expected_out_msg3 in out
        assert expected_out_msg4 in out
        assert len(err) == 0

    def test_change_username(self,capsys):
        message1 = '@server set_my_id(user1)'
        message2 = '@server set_my_id(user2)'
        messages = [message1,message2]
        fake_reader = FakeReader(messages)
        self.loop.run_until_complete(self.testserver.handle_connection(
                                    fake_reader , self.fake_writer))
        sent_message_1 = ('@client username set to '+ self.get_id(message1))
        sent_message_2 = ('@client username set to '+ self.get_id(message2))
        print (self.fake_writer.getvalue())
        assert len(self.testserver.all_clients) == 1
        assert sent_message_1.encode() in self.fake_writer.getvalue()
        assert sent_message_2.encode() in self.fake_writer.getvalue()
        expected_out_msg1 = 'Received {} from {}'.format((message1),self.get_id(message1))
        expected_out_msg2 = 'Received {} from {}'.format((message2),self.get_id(message2))
        expected_out_msg3 = 'Closing connection with client' 
        out, err = capsys.readouterr()
        assert expected_out_msg1 in out
        assert expected_out_msg2 in out
        assert expected_out_msg3 in out
        assert len(err) == 0

    # other cleint name not defined
    def test_public_message(self,capsys):
        message1 = '@server set_my_id(user1)'
        message2 = 'hi there'
        messages = [message1,message2]
        fake_reader = FakeReader(messages)
        #self.other_fake_writer.write(message2)
        self.loop.run_until_complete(self.testserver.handle_connection(
                                    fake_reader, self.fake_writer))
        #assert len(self.other_fake_writer.getvalue()) == 0
        sent_message_1 = ('@client username set to '+ self.get_id(message1))
        sent_message_2 = ('{}: {}'.format(self.get_id(message1),message2))
        assert sent_message_1.encode() in self.fake_writer.getvalue()
        assert sent_message_2.encode() in self.other_fake_writer.getvalue()
        """assert self.fake_writer.get_extra_info('').encode() \
                                                        not in self.fake_writer.getvalue()"""
        expected_out_msg1 = 'Received {} from {}'.format((message1),self.get_id(message1))
        expected_out_msg2 = 'Received {} from'.format((message1))
        expected_out_msg3 = 'Closing connection with client' 
        out, err = capsys.readouterr()
        assert expected_out_msg1 in out
        assert expected_out_msg2 in out
        assert expected_out_msg3 in out
        assert len(err) == 0

    def test_permission_repeated_username(self,capsys):
        message1 = '@server set_my_id(user1)'
        messages = [message1,message1]
        fake_reader = FakeReader(messages)
        self.loop.run_until_complete(self.testserver.handle_connection(
                                    fake_reader, self.fake_writer))
        #assert len(self.other_fake_writer.getvalue()) == 0
        sent_message_1 = ('@client username set to '+ self.get_id(message1))
        sent_message_2 = ('@client ERROR Name is already in use')
        assert sent_message_1.encode() in self.fake_writer.getvalue()
        assert sent_message_2.encode() in self.fake_writer.getvalue()
        """assert self.fake_writer.get_extra_info('').encode() \
                                                        not in self.fake_writer.getvalue()"""
        expected_out_msg1 = 'Received {} from {}'.format((message1),self.get_id(message1))
        expected_out_msg2 = 'Closing connection with client' 
        out, err = capsys.readouterr()
        assert expected_out_msg1 in out
        assert expected_out_msg2 in out
        assert len(err) == 0


    def test_private_message_to_nonexistent_user(self,capsys):
        message1 = '@server set_my_id(user1)'
        message2 = '@user2 hey there'
        messages = [message1,message2]
        fake_reader = FakeReader(messages)
        self.loop.run_until_complete(self.testserver.handle_connection(
                                    fake_reader, self.fake_writer))
        #assert len(self.other_fake_writer.getvalue()) == 0
        sent_message_1 = ('@client username set to '+ self.get_id(message1))
        sent_message_2 = ('@client ERROR Inavlid input')
        assert sent_message_1.encode() in self.fake_writer.getvalue()
        assert sent_message_2.encode() in self.fake_writer.getvalue()
        """assert self.fake_writer.get_extra_info('').encode() \
                                                        not in self.fake_writer.getvalue()"""
        expected_out_msg1 = 'Received {} from {}'.format((message1),self.get_id(message1))
        expected_out_msg2 = 'Closing connection with client' 
        out, err = capsys.readouterr()
        assert expected_out_msg1 in out
        assert expected_out_msg2 in out
        assert len(err) == 0



    # If the input message is empty or None, the server
    # should simply ignore it and close the connection
    def test_none_or_empty_messages(self,capsys):
        for fake_reader in [FakeReader(['']), FakeReader(None)]:
            self.loop.run_until_complete(
                self.testserver.handle_connection(
                    fake_reader, self.fake_writer))
            assert len(self.fake_writer.getvalue()) == 0
            assert len(self.other_fake_writer.getvalue()) == 0
            assert self.fake_writer.is_closed()
            assert not self.other_fake_writer.is_closed()
            self.fake_writer.open()
            assert not self.fake_writer.is_closed()


