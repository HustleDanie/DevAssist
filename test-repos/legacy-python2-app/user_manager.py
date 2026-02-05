# -*- coding: utf-8 -*-
"""
User Management Module - Python 2 Style

Demonstrates Python 2 patterns in a user management context.
"""

class User:
    """Represents a user in the system."""
    
    def __init__(self, username, email, age):
        self.username = unicode(username)
        self.email = unicode(email)
        self.age = int(age)
        self.active = True
        print "Created user: " + self.username
    
    def __str__(self):
        return u"User(%s, %s)" % (self.username, self.email)
    
    def deactivate(self):
        """Deactivate the user account."""
        self.active = False
        print "User %s has been deactivated" % self.username
    
    def update_email(self, new_email):
        """Update user email."""
        old_email = self.email
        self.email = unicode(new_email)
        print "Updated email from %s to %s" % (old_email, self.email)


class UserManager:
    """Manages a collection of users."""
    
    def __init__(self):
        self.users = {}
        self.user_count = 0
        print "UserManager initialized"
    
    def add_user(self, username, email, age):
        """Add a new user to the system."""
        if username in self.users.keys():
            print "Error: User %s already exists!" % username
            return False
        
        try:
            user = User(username, email, age)
            self.users[username] = user
            self.user_count += 1
            print "User count: %d" % self.user_count
            return True
        except Exception, e:
            print "Error creating user: " + str(e)
            return False
    
    def remove_user(self, username):
        """Remove a user from the system."""
        if username not in self.users.keys():
            print "Error: User %s not found!" % username
            return False
        
        del self.users[username]
        self.user_count -= 1
        print "Removed user: %s" % username
        return True
    
    def get_user(self, username):
        """Get a user by username."""
        return self.users.get(username, None)
    
    def list_users(self):
        """List all users."""
        print "=== User List ==="
        for username, user in self.users.iteritems():
            status = "active" if user.active else "inactive"
            print "  %s (%s) - %s" % (username, user.email, status)
        print "Total: %d users" % self.user_count
    
    def get_active_users(self):
        """Get all active users using a generator."""
        for username, user in self.users.iteritems():
            if user.active:
                yield user
    
    def get_user_emails(self):
        """Get all user emails."""
        emails = []
        for email in self.users.itervalues():
            emails.append(email.email)
        return emails
    
    def get_usernames(self):
        """Get all usernames."""
        return list(self.users.iterkeys())
    
    def search_users(self, query):
        """Search users by username or email."""
        query = unicode(query).lower()
        results = []
        
        for username, user in self.users.iteritems():
            if query in username.lower() or query in user.email.lower():
                results.append(user)
        
        print "Found %d users matching '%s'" % (len(results), query)
        return results
    
    def bulk_import(self, user_data):
        """Import users from a dictionary."""
        imported = 0
        
        for username, data in user_data.iteritems():
            try:
                email = data.get('email', '')
                age = data.get('age', 0)
                if self.add_user(username, email, age):
                    imported += 1
            except Exception, e:
                print "Error importing %s: %s" % (username, str(e))
        
        print "Imported %d users" % imported
        return imported


def interactive_mode():
    """Interactive user management."""
    manager = UserManager()
    
    while True:
        print "\n=== User Management ==="
        print "1. Add user"
        print "2. Remove user"
        print "3. List users"
        print "4. Search users"
        print "5. Exit"
        
        choice = raw_input("Enter choice: ")
        
        if choice == '1':
            username = raw_input("Username: ")
            email = raw_input("Email: ")
            age = raw_input("Age: ")
            manager.add_user(username, email, age)
        elif choice == '2':
            username = raw_input("Username to remove: ")
            manager.remove_user(username)
        elif choice == '3':
            manager.list_users()
        elif choice == '4':
            query = raw_input("Search query: ")
            manager.search_users(query)
        elif choice == '5':
            print "Goodbye!"
            break
        else:
            print "Invalid choice!"


if __name__ == "__main__":
    interactive_mode()
