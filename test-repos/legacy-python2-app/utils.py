# -*- coding: utf-8 -*-
"""
Utility Functions - Python 2 Style

Common utility functions with Python 2 patterns.
"""

import time
import hashlib


def log_message(message, level="INFO"):
    """Log a message with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print "[%s] %s: %s" % (timestamp, level, message)


def format_string(template, **kwargs):
    """Format a string with keyword arguments."""
    result = unicode(template)
    for key, value in kwargs.iteritems():
        placeholder = "{%s}" % key
        result = result.replace(placeholder, unicode(value))
    return result


def hash_string(text):
    """Hash a string using MD5."""
    text = unicode(text).encode('utf-8')
    return hashlib.md5(text).hexdigest()


def validate_email(email):
    """Simple email validation."""
    email = unicode(email)
    if '@' not in email:
        print "Invalid email: missing @"
        return False
    if '.' not in email.split('@')[1]:
        print "Invalid email: missing domain"
        return False
    return True


def parse_key_value(text, separator='='):
    """Parse key-value pairs from text."""
    result = {}
    lines = unicode(text).strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if separator in line:
            key, value = line.split(separator, 1)
            result[key.strip()] = value.strip()
    
    print "Parsed %d key-value pairs" % len(result)
    return result


def dict_to_query_string(params):
    """Convert dictionary to query string."""
    parts = []
    for key, value in params.iteritems():
        parts.append("%s=%s" % (unicode(key), unicode(value)))
    return '&'.join(parts)


def query_string_to_dict(query):
    """Parse query string to dictionary."""
    result = {}
    query = unicode(query)
    
    if query.startswith('?'):
        query = query[1:]
    
    pairs = query.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            result[key] = value
    
    return result


def chunk_list(items, chunk_size):
    """Split a list into chunks."""
    chunks = []
    total = len(items)
    num_chunks = (total + chunk_size - 1) / chunk_size  # Integer division
    
    for i in xrange(num_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, total)
        chunks.append(items[start:end])
    
    print "Created %d chunks from %d items" % (len(chunks), total)
    return chunks


def flatten_dict(d, parent_key='', sep='.'):
    """Flatten a nested dictionary."""
    items = []
    for key, value in d.iteritems():
        new_key = "%s%s%s" % (parent_key, sep, key) if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).iteritems())
        else:
            items.append((new_key, value))
    return dict(items)


def retry_function(func, max_retries=3, delay=1):
    """Retry a function on failure."""
    for attempt in xrange(max_retries):
        try:
            return func()
        except Exception, e:
            print "Attempt %d failed: %s" % (attempt + 1, str(e))
            if attempt < max_retries - 1:
                print "Retrying in %d seconds..." % delay
                time.sleep(delay)
    
    print "All %d attempts failed" % max_retries
    return None


def measure_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print "Function %s took %.3f seconds" % (func.__name__, end - start)
        return result
    return wrapper


def safe_divide(a, b, default=0):
    """Safely divide two numbers."""
    try:
        if b == 0:
            print "Warning: Division by zero, returning default"
            return default
        return a / b  # Integer division in Python 2
    except Exception, e:
        print "Error in division: %s" % str(e)
        return default


def range_inclusive(start, end):
    """Generate inclusive range."""
    for i in xrange(start, end + 1):
        yield i


def get_user_confirmation(prompt):
    """Get yes/no confirmation from user."""
    while True:
        response = raw_input(prompt + " (y/n): ")
        response = unicode(response).lower().strip()
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print "Please enter 'y' or 'n'"


if __name__ == "__main__":
    # Test utilities
    log_message("Testing utilities", "DEBUG")
    
    print format_string("Hello {name}!", name="World")
    print hash_string("test")
    print validate_email("test@example.com")
