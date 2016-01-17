
class Config(object):
    DEBUG = False

    # Specify the server name that accepts connections.
    # Connections not from this particular server name
    # will be 404'd in the router
    SERVER_NAME = 'sybolt.com:5006'
    CACHE_FOLDER = 'cache'

class Production(Config):
    pass
    
class Development(Config):
    DEBUG = True
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True
    SERVER_NAME = 'sybolt.com:5007'

    # Note: The ICE server has been firewalled to only allow 
    # local connections. Development builds can only occur on
    # a copy of Sybot checked out on localhost
    ICE_PROXY = 'Meta:tcp -h 127.0.0.1 -p 6502'
    ICE_SECRET = 'watchmakers'
    ICE_CLIENT = 'tcp -h 127.0.0.1'

class RemoteDevelopment(Development):
    # I lied, it's not behind a firewall. RIP security
    ICE_PROXY = 'Meta:tcp -h 107.170.144.158 -p 6502'
    ICE_CLIENT = 'tcp -h 107.170.144.158'
