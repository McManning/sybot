import Ice
import Murmur

from sybot import app

class MetaCallbackI(Murmur.MetaCallback):

    def started(self, server, current=None):
        # TODO: Scope of `adapter` is incorrect here.
        server_callback = Murmur.ServerCallbackPrx.uncheckedCast(
            adapter.addWithUUID(
                ServerCallbackI(server, current.adapter)
            )
        )
        server.addCallback(server_callback)

    def stopped(self, server, current=None):
        pass


class ServerCallbackI(Murmur.ServerCallback):
    def __init__(self, server, adapter):
        self.server = server
        self.context_callback = Murmur.ServerContextCallbackPrx.uncheckedCast(
            adapter.addWithUUID(
                ServerContextCallbackI(server)
            )
        )
        
    def userConnected(self, user, current=None):
        print(user)
        
        # Access to: user.session, user.name

        # If they're an admin...
        #if (self.server.hasPermission(user.session, 0, Murmur.PermissionWrite)):
        #    print "Is a global admin"

        # Add a "Sybolt Live" button to the user's Server menu
        self.server.addContextCallback(
            user.session, 
            "showlive", 
            "Sybolt Live", 
            self.context_callback, 
            Murmur.ContextServer
        )

        # Add a button to provide a link/details of Sybot
        self.server.addContextCallback(
            user.session,
            "showsybot",
            "Sybot Info",
            self.context_callback,
            Murmur.ContextServer
        )
        
    def userDisconnected(self, user, current=None):
        pass
        
    def userStateChanged(self, user, current=None):

        # If they turned on frontend recording, give them a friendly message :)
        if user.recording:
            self.server.sendMessageChannel(
                user.channel, 
                0, 
                "Hey, {} stop that shit.".format(user.name)
            )
        

class ServerContextCallbackI(Murmur.ServerContextCallback):

    def __init__(self, server):
        self.server = server

    def get_user_from_session(self, session):
        users = self.server.getUsers()
        for i in users:
            if users[i].session == session:
                return users[i]
                
        return None
        
    def contextAction(self, action, user, session, chanid, current=None):
        if action == 'showlive':
            self.server.sendMessage(
                user.session, 
                '<a href="http://dev.sybolt.com/live">http://dev.sybolt.com/live</a> you lazy fuck.'
            )
        elif action == 'showsybot':
            self.server.sendMessage(
                user.session,
                'TODO: :)'
            )
        

class MumbleInterface(object):
    """Primary interface component to interact with Ice """

    ice = None

    def __init__(self):
        print('Starting MumbleInterface')

        prop = Ice.createProperties([])
        prop.setProperty("Ice.ImplicitContext", "Shared")
        prop.setProperty("Ice.MessageSizeMax", "65535")
        prop.setProperty("Ice.Default.EncodingVersion", "1.0")

        idd = Ice.InitializationData()
        idd.properties = prop

        self.ice = Ice.initialize(idd)
        self.ice.getImplicitContext().put("secret", app.config['ICE_SECRET'])
    

    def connect(self):
        print('Connecting to Mumble Ice')

        self.meta = Murmur.MetaPrx.checkedCast(
            self.ice.stringToProxy(app.config['ICE_PROXY'])
        )

        adapter = self.ice.createObjectAdapterWithEndpoints(
            "Callback.Client", 
            app.config['ICE_CLIENT']
        )

        self.meta_callback = Murmur.MetaCallbackPrx.uncheckedCast(
            adapter.addWithUUID(
                MetaCallbackI()
            )
        )

        adapter.activate()
        self.meta.addCallback(self.meta_callback)
        
        # Bind to known servers
        for server in self.meta.getBootedServers():
            print(server)

            server_callback = Murmur.ServerCallbackPrx.uncheckedCast(
                adapter.addWithUUID(
                    ServerCallbackI(server, adapter)
                )
            )
            server.addCallback(server_callback)


    def shutdown(self):
        self.meta.removeCallback(self.meta_callback)
        self.ice.shutdown()

