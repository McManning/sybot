from flask import Blueprint, jsonify

from app.murmur import get_murmur_meta, address_to_ipv6
from app.util import texture_to_data_uri

api = Blueprint('api', __name__)

@api.route('/')
def hello():
    return jsonify({
        'data': 'hello world'
    })

@api.route('/servers')
def servers():
    meta = get_murmur_meta()
    servers = []
    for server in meta.getAllServers():
        servers.append({
            'name': server.getConf('registername'),
            'host': server.getConf('host'),
            'port': server.getConf('port'),
            'isRunning': server.isRunning(),
            'uptime': server.getUptime(),
            'users': len(server.getUsers())
        })

    return jsonify({
        'data': servers
    })

@api.route('/users')
def users():
    meta = get_murmur_meta()
    users = []

    for server in meta.getAllServers():
        for id, user in server.getUsers().items():
            # Textures are stored as zlib compress()ed 600x60 32-bit BGRA data.
            # sequence<byte> data
            texture = ''
            if user.userid >= 0:
                texture = server.getTexture(user.userid)

            users.append({
                'session': user.session,
                'registered': user.userid >= 0,
                'mute': user.mute or user.selfMute,
                'deaf': user.deaf or user.selfDeaf,
                'channel': user.channel, # ID number
                'name': user.name,
                'texture': texture_to_data_uri(texture),
                'addr': str(address_to_ipv6(user.address))
            })

            # Not included: onlinesecs, bytespersec,
            # version, os, osversion, comment, tcponly, idlesecs

    return jsonify({
        'data': users
    })

@api.route('/live', methods=['GET', 'POST'])
def on_live():
    """Live stream has started. Notify Mumble users"""
    with open('templates/live_notice.html', 'r') as f:
        html = f.read()

    meta = get_murmur_meta()
    for server in meta.getAllServers():
        server.sendMessageChannel(0, 1, html)

    return ''



