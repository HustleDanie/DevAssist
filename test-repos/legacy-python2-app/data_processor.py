# -*- coding: utf-8 -*-
"""
Data Processing Module - Python 2 Style

Demonstrates Python 2 patterns for data processing.
"""

import json


def process_list(items):
    """Process a list of items using xrange."""
    print "Processing %d items..." % len(items)
    
    results = []
    for i in xrange(len(items)):
        item = items[i]
        processed = unicode(item).upper()
        results.append(processed)
        print "  [%d] %s -> %s" % (i, item, processed)
    
    return results


def process_dict(data):
    """Process dictionary data."""
    print "Processing dictionary with %d keys..." % len(data)
    
    processed = {}
    for key, value in data.iteritems():
        new_key = unicode(key).lower()
        new_value = unicode(value).strip()
        processed[new_key] = new_value
        print "  %s: %s" % (new_key, new_value)
    
    return processed


def filter_data(data, predicate):
    """Filter data based on a predicate function."""
    results = []
    
    for key, value in data.iteritems():
        if predicate(key, value):
            results.append((key, value))
    
    print "Filtered %d items from %d" % (len(results), len(data))
    return results


def merge_dicts(dict1, dict2):
    """Merge two dictionaries (Python 2 style)."""
    result = {}
    
    for key, value in dict1.iteritems():
        result[key] = value
    
    for key, value in dict2.iteritems():
        if key in result.keys():
            print "Warning: Overwriting key '%s'" % key
        result[key] = value
    
    return result


def calculate_statistics(numbers):
    """Calculate basic statistics."""
    if not numbers:
        print "Error: Empty list!"
        return None
    
    n = len(numbers)
    total = sum(numbers)
    mean = total / n  # Integer division in Python 2
    
    # Calculate variance
    variance_sum = 0
    for i in xrange(n):
        variance_sum += (numbers[i] - mean) ** 2
    variance = variance_sum / n
    
    # Find min and max
    min_val = numbers[0]
    max_val = numbers[0]
    for i in xrange(1, n):
        if numbers[i] < min_val:
            min_val = numbers[i]
        if numbers[i] > max_val:
            max_val = numbers[i]
    
    print "Statistics:"
    print "  Count: %d" % n
    print "  Sum: %d" % total
    print "  Mean: %d" % mean
    print "  Variance: %d" % variance
    print "  Min: %d" % min_val
    print "  Max: %d" % max_val
    
    return {
        'count': n,
        'sum': total,
        'mean': mean,
        'variance': variance,
        'min': min_val,
        'max': max_val
    }


def read_json_file(filepath):
    """Read and parse a JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            print "Loaded JSON from %s" % filepath
            return data
    except IOError, e:
        print "Error reading file: " + str(e)
        return None
    except ValueError, e:
        print "Error parsing JSON: " + str(e)
        return None


def write_json_file(filepath, data):
    """Write data to a JSON file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            print "Wrote JSON to %s" % filepath
            return True
    except IOError, e:
        print "Error writing file: " + str(e)
        return False


def generate_range(start, end, step=1):
    """Generate a range of numbers (Python 2 xrange wrapper)."""
    print "Generating range from %d to %d with step %d" % (start, end, step)
    for i in xrange(start, end, step):
        yield i


def batch_process(items, batch_size):
    """Process items in batches."""
    total = len(items)
    batches = (total + batch_size - 1) / batch_size  # Integer division
    
    print "Processing %d items in %d batches" % (total, batches)
    
    for batch_num in xrange(batches):
        start = batch_num * batch_size
        end = min(start + batch_size, total)
        batch = items[start:end]
        
        print "  Batch %d: items %d-%d" % (batch_num + 1, start, end - 1)
        yield batch


if __name__ == "__main__":
    print "=== Data Processor Test ==="
    
    # Test list processing
    test_list = ['apple', 'banana', 'cherry']
    process_list(test_list)
    
    # Test dict processing
    test_dict = {'Name': '  John  ', 'City': '  New York  '}
    process_dict(test_dict)
    
    # Test statistics
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    calculate_statistics(numbers)
