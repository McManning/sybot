import Ice
import Murmur

from sybot import app

class MetaCallbackI(Murmur.MetaCallback):
    """ Callback interface to be notified when a 
        server is started or stopped.
    """
    def __init__(self, adapter):
        self.adapter = adapter
        super(MetaCallbackI, self).__init__()

    def started(self, server, current=None):
        server_callback = Murmur.ServerCallbackPrx.uncheckedCast(
            self.adapter.addWithUUID(
                ServerCallbackI(server, current.adapter)
            )
        )
        server.addCallback(server_callback)

    def stopped(self, server, current=None):
        pass


class ServerCallbackI(Murmur.ServerCallback):
    """ Callbacks for client events in a server instance
        (connect, disconnect, speak, text, etc)
    """

    def __init__(self, server, adapter):
        self.server = server
        self.adapter = adapter

        # Bind a context menu listener to the server instance
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

    def userTextMessage(self, user, message, current=None):
        """ Client sends a text message to a channel.
            This includes the sending of images (base64)
            and links, as well as information about the 
            destination, if not the user's current channel.
        """

        # Access to: user.name, etc. 
        # message.text

        # TODO: Delegate to listeners

        pass

    def channelCreated(self, channel, current=None):
        """A new channel has been added to the server
        """
        pass

    def channelRemoved(self, channel, current=None):
        """A channel has been removed from the server
        """
        pass

    def channelStateChanged(self, channel, current=None):
        """A channel has been updated (comment, ACLs, etc)
        """
        pass


        

class ServerContextCallbackI(Murmur.ServerContextCallback):
    """ Context action callback. This is for
        when a user clicks a custom context menu
        item from within their Mumble client.
    """
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
                '<a href="http://sybolt.com/live">http://dev.sybolt.com/live</a> you lazy fuck.'
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
    
        self.text_rules = []

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
                MetaCallbackI(adapter)
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

    def text(self, rule, **options):
        """ Decorator around add_text_rule 
            Example Usage:

            @mumble.text('^hello (?P<name>\w+)'):
            def hello(server, user, text, args):
                print(args['name'])
        """
        def decorator(f):
            # crap from Flask
            # endpoint = options.pop('endpoint', None)
            # self.add_url_rule(rule, endpoint, f, **options)
            self.add_text_rule(rule, f, **options)
            return f
        return decorator

    def add_text_rule(self, rule, f, **options):
        """Add a callback to be ran upon matching a text message
        """
        help = options.pop('help', '')

        self.text_rules.append({
            'regex': rule,
            'f': f,
            'help': help
        })

    def run_text_rules(self, server, user, msg):
        """Run a text_rule callback that matches the msg text
        """
        for rule in self.text_rules:
            match = re.search(rule['regex'], msg.text, re.IGNORECASE)
            
            # TODO: we push the full match into args, but groups
            # are accessed via match.group('foo'). I'd prefer this
            # to be a dictionary of keys to values. Check Flask's 
            # implementation.
            # TODO: Don't use re matching for args. Do something
            # that's familiar with Flask. I don't care for (?P<foo>)
            # nonsense.

            if match and rule['f'](server, user, msg.text, match):
                return
    