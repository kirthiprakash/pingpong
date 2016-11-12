"""
author: kp
date: 12/11/16
"""

from pymongo import MongoClient


class MongoConnection(object):
    def __init__(self, host='localhost', port=27017, dbname='test'):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.connection = MongoClient(self.host, self.port)
        self.db = self.connection[self.dbname]

    def get_connection(self):
        return self.connection

    def close_connection(self):
        self.connection.close()

    def save(self, collection, params):
        return self.db[collection].save(params)

    def find(self, collection, params={}, sort={}, limit=None, distinct=None):
        cursor = self.db[collection].find(params)
        if sort:
            sort_arr = []
            for key, direction in sort.iteritems():
                sort_arr.append((key, direction))
            cursor = cursor.sort(sort_arr)
        if limit is not None and limit > 0:
            cursor = cursor.limit(limit)
        if distinct is not None:
            cursor.distinct(distinct)
        return cursor

    def findOne(self, collection, params={}):
        return self.db[collection].find_one(params)

    def aggregate(self, collection, pipeline=[]):
        return self.db[collection].aggregate(pipeline=pipeline)

    def distinct(self, collection, key):
        return self.db[collection].distinct(key)

    def update(self, collection, params={}, set_params={}, upsert=False):
        return self.db[collection].update(params, {"$set": set_params}, upsert=upsert)

    def generic_update(self, collection, query={}, params={}, upsert=False):
        return self.db[collection].update(query, params, upsert=upsert)

    def find_and_modify(self, collection, query={}, params={}, upsert=False):
        return self.db[collection].find_and_modify(query, params, upsert=upsert)

    def insertOne(self, collection, params):
        return self.db[collection].insert(params)

    def delete(self, collection, params=None):
        return self.db[collection].remove(params)

    def distinct(self, collection, key):
        return self.db[collection].distinct(key)


host = "localhost"
port = 27017
dbname = "pingpong"

dao = MongoConnection(host=host, port=port, dbname=dbname)


class Collection:
    account = "account"
    connection = "connection"
    message = "message"

    class Account:
        name = "account"
        STATUS_ONLINE = "ONLINE"
        STATUS_OFFLINE = "OFFLINE"

    class Connection:
        name = "connection"

    class Message:
        name = "message"
