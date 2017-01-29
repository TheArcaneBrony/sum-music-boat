import logging

from xmlrpc.server import SimpleXMLRPCServer

shard_cfg = {}

#logging.basicConfig(level=logging.DEBUG)

server = SimpleXMLRPCServer(("localhost", 8000), logRequests=False, allow_none=True)
print("Listening on port 8000...")


def add_to_cfg(opts, shard_id):
    #logging.debug("shard_id: %s, opts: %s", shard_id, opts)
    global shard_cfg
    shard_cfg[shard_id] = opts
    return


def get_cfg():
    temp_cfg = {
        "channels": 0,
        "servers": 0,
        "members": 0,
        "playing_on": 0
    }

    for i in shard_cfg.values():
        for val in list(i.items()):
            temp_cfg[val[0]] += val[1]

    #logging.debug("temp cfg: %s", temp_cfg)

    return temp_cfg

server.register_function(get_cfg, "get_cfg")
server.register_function(add_to_cfg, "add_to_cfg")

server.serve_forever()

