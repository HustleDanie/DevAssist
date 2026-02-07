#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database Utility - Python 2 Legacy Code
A database management utility with Python 2 idioms.
"""

import anydbm
import cPickle as pickle
import UserDict
import thread
import Queue


class DatabaseManager(UserDict.UserDict):
    """A simple key-value database manager."""
    
    def __init__(self, db_path):
        UserDict.UserDict.__init__(self)
        self.db_path = db_path
        self.lock = thread.allocate_lock()
        self.operation_queue = Queue.Queue()
    
    def connect(self):
        """Connect to the database."""
        print "Connecting to database: %s" % self.db_path
        try:
            self.db = anydbm.open(self.db_path, 'c')
            print "Connected successfully!"
            return True
        except anydbm.error, e:
            print "Database error: %s" % e
            return False
    
    def disconnect(self):
        """Close the database connection."""
        print "Disconnecting from database..."
        if hasattr(self, 'db'):
            self.db.close()
        print "Disconnected."
    
    def set_value(self, key, value):
        """Set a value in the database."""
        self.lock.acquire()
        try:
            serialized = pickle.dumps(value)
            self.db[str(key)] = serialized
            print "Set key '%s' = %s" % (key, repr(value))
        finally:
            self.lock.release()
    
    def get_value(self, key, default=None):
        """Get a value from the database."""
        self.lock.acquire()
        try:
            if self.db.has_key(str(key)):
                serialized = self.db[str(key)]
                value = pickle.loads(serialized)
                print "Get key '%s' = %s" % (key, repr(value))
                return value
            else:
                print "Key '%s' not found, returning default" % key
                return default
        finally:
            self.lock.release()
    
    def delete_key(self, key):
        """Delete a key from the database."""
        self.lock.acquire()
        try:
            if self.db.has_key(str(key)):
                del self.db[str(key)]
                print "Deleted key '%s'" % key
                return True
            else:
                print "Key '%s' not found" % key
                return False
        finally:
            self.lock.release()
    
    def list_keys(self):
        """List all keys in the database."""
        keys = self.db.keys()
        print "Database contains %d keys:" % len(keys)
        for key in keys:
            print "  - %s" % key
        return keys
    
    def bulk_insert(self, data_dict):
        """Insert multiple key-value pairs."""
        print "Bulk inserting %d items..." % len(data_dict)
        count = 0
        for key, value in data_dict.iteritems():
            self.set_value(key, value)
            count += 1
        print "Inserted %d items." % count
    
    def export_to_file(self, filepath):
        """Export database to a pickle file."""
        print "Exporting database to %s..." % filepath
        data = {}
        for key in self.db.keys():
            data[key] = pickle.loads(self.db[key])
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print "Exported %d items." % len(data)
    
    def import_from_file(self, filepath):
        """Import data from a pickle file."""
        print "Importing from %s..." % filepath
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.bulk_insert(data)
        print "Import complete."


def interactive_mode():
    """Run interactive database shell."""
    db_path = raw_input("Enter database path: ")
    db = DatabaseManager(db_path)
    
    if not db.connect():
        print "Failed to connect!"
        return
    
    print "\nCommands: set, get, delete, list, export, import, quit"
    
    while True:
        cmd = raw_input("\ndb> ").strip().lower()
        
        if cmd == 'quit':
            break
        elif cmd == 'set':
            key = raw_input("Key: ")
            value = raw_input("Value: ")
            db.set_value(key, value)
        elif cmd == 'get':
            key = raw_input("Key: ")
            value = db.get_value(key)
            print "Value: %s" % repr(value)
        elif cmd == 'delete':
            key = raw_input("Key: ")
            db.delete_key(key)
        elif cmd == 'list':
            db.list_keys()
        elif cmd == 'export':
            filepath = raw_input("Export filepath: ")
            db.export_to_file(filepath)
        elif cmd == 'import':
            filepath = raw_input("Import filepath: ")
            db.import_from_file(filepath)
        else:
            print "Unknown command: %s" % cmd
    
    db.disconnect()
    print "Goodbye!"


if __name__ == '__main__':
    interactive_mode()
