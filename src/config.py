
class Config(object):
    DEBUG = False
    PORT = 5000
    CACHE_FOLDER = 'cache'

class Production(Config):
    pass
    
class Development(Config):
    DEBUG = True

    # Note: The ICE server has been firewalled to only allow 
    # local connections. Development builds can only occur on
    # a copy of Sybot checked out on localhost
    ICE_PROXY = 'Meta:tcp -h 127.0.0.1 -p 6502'
    ICE_SECRET = 'watchmakers'
    ICE_CLIENT = 'tcp -h 127.0.0.1'
