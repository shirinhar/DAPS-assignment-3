import sys, asyncio

################
# Server class #
################

class Server:
    default_server_address = '127.0.0.1'
    default_server_port = 8888

    # NOTE: you can modify __init__
    def __init__(self,server_address=default_server_address,server_port=default_server_port):
        self.address = server_address
        self.port = server_port
        self.all_clients = set([])
        self.users = {}

    # NOTE: the following method must be implemented for some of our grading tests to work. If you don't implement this method correctly, you will lose some marks!
    # method for registering usernames 
    def set_username(self,new_username,writer,old_username=None):
        pass
    
    # NOTE: this method must be implemented for some of our grading tests to work. If you don't implement this method correctly, you will lose some marks!
    # method that returns all the registered usernames as a list
    def get_registered_usernames_list(self):
        pass

    # NOTE: you can modify the implementation of handle_connection (but not its signature)
    @asyncio.coroutine
    def handle_connection(self, reader, writer):
        self.all_clients.add(writer)
        client_addr  = writer.get_extra_info('peername')
        client_addr_copy = client_addr
        print('New client {}'.format(client_addr))
        while True:
            data = yield from reader.read(100)
            if data == None or len(data) == 0:
                break
            message = data.decode()
            splitted = message.split()
            if '@server' in message:
                new_message = ('@client ERROR - Incorrect Input')
                if 'set_my_id(' in message and ')' in message:
                    chosen_name = message[message.find("(")+1:message.find(")")]
                    if (' ' in chosen_name):
                        new_message = ('[error] Username cannot have spaces')
                    elif chosen_name == 'server' or chosen_name == 'client':
                        new_message = ('[error] Incorrect user name chosen. \nuser names cannot be "server" or "client" or the same as another')
                    elif (chosen_name in self.users.values()):
                        new_message = ('@client ERROR - Name is already in use')
                    else:
                        #self.users.append(chosen_name)
                        self.users[writer] = chosen_name
                        client_addr = chosen_name
                        new_message = ('@client username set to ' + chosen_name)
                        #HOW THE FUCK DO I DO THAT?!
                
                writer.write(new_message.encode())
                yield from writer.drain()
                print("Received {} from {}".format(message, client_addr))   
                continue

            # no need to traverse you can use the key and value
            elif client_addr not in self.users.values():
                for other_writer in self.all_clients:
                    if other_writer == writer:
                        text = '[error] username must be set to send messages.'
                        other_writer.write(text.encode())
                        yield from other_writer.drain()
                        print("Received {} from {}".format(message, client_addr))   
                continue

            elif ('@') in splitted[0]:
                check = False
                for other_writer in self.all_clients:  
                    if splitted[0] == ('@' + self.users[other_writer]): 
                        if other_writer == writer:
                            check = True
                            other_writer.write(('[error] cannot send private message to yourself').encode())
                            yield from other_writer.drain()
                            print("Received {} from {}".format(new_message, client_addr))   
                            continue 
                        check = True           
                        other_message = ('@' + self.users[other_writer] + ' ' + client_addr  + ': ' + message[message.index(' ') + 1:])
                        other_writer.write(other_message.encode())
                        yield from other_writer.drain()
                        print("Received {} from {}".format(message, client_addr))
                if check == False:
                    new_message = ('[error] Inavlid input')
                    for other_writer in self.all_clients:
                        if other_writer == writer:
                            other_writer.write(new_message.encode())
                            yield from other_writer.drain()
                            print("Received {} from {}".format(new_message, client_addr))   
                continue
            
            """if client_addr == client_addr_copy:
                for other_writer in self.all_clients:
                    if other_writer == writer:
                        text = 'Username must be set to send messages.\nSet username by writting @server set_my_id(<username>)'
                        other_writer.write(text.encode())
                        yield from other_writer.drain()
                        print("Received {} from {}".format(message, client_addr))   
                continue"""

            print("Received {} from {}".format(message, client_addr))
            for other_writer in self.all_clients:
                if other_writer != writer:
                    new_message = '{}: {}'.format(client_addr,message)
                    #new_message = '{}: {}'.format(client_addr,message)
                    other_writer.write(new_message.encode())
                    yield from other_writer.drain()      
        print("Closing connection with client {}".format(client_addr))
        writer.close()
        self.all_clients.remove(writer)
        self.users.pop(writer,None)

    # NOTE: do not modify run
    def run(self):
        loop = asyncio.get_event_loop()
        coro = asyncio.start_server(self.handle_connection,self.address,
                                                    self.port,loop=loop)
        server = loop.run_until_complete(coro)

        print('Serving on {}'.format(server.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print('\nGot keyboard interrupt, shutting down',file=sys.stderr)
        
        for task in asyncio.Task.all_tasks():
            task.cancel()
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()    


# NOTE: do not modify the following two lines
if __name__ == '__main__':
    Server().run()
