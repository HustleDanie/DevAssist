#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Analytics - Python 2 Legacy Code
A data analytics script with various Python 2 patterns.
"""

import __builtin__
import operator
import itertools
import functools
import collections
import cPickle as pickle
import cStringIO


class DataAnalyzer:
    """Analyze datasets with various statistical methods."""
    
    def __init__(self, data=None):
        self.data = data if data else []
        self.results = {}
    
    def load_csv(self, filepath, delimiter=','):
        """Load data from a CSV file."""
        print "Loading data from %s..." % filepath
        
        self.data = []
        with open(filepath, 'r') as f:
            headers = f.readline().strip().split(delimiter)
            print "Headers: %s" % ', '.join(headers)
            
            line_count = 0
            for line in f:
                values = line.strip().split(delimiter)
                row = dict(zip(headers, values))
                self.data.append(row)
                line_count += 1
        
        print "Loaded %d rows." % line_count
        return self.data
    
    def filter_data(self, column, condition_func):
        """Filter data based on a condition."""
        print "Filtering data on column '%s'..." % column
        
        filtered = filter(lambda row: condition_func(row.get(column, '')), self.data)
        print "Filtered: %d -> %d rows" % (len(self.data), len(filtered))
        return filtered
    
    def map_column(self, column, transform_func):
        """Apply a transformation to a column."""
        print "Transforming column '%s'..." % column
        
        result = map(lambda row: transform_func(row.get(column, '')), self.data)
        return result
    
    def reduce_column(self, column, reduce_func, initial=None):
        """Reduce a column to a single value."""
        print "Reducing column '%s'..." % column
        
        values = [row.get(column, 0) for row in self.data]
        
        if initial is not None:
            result = reduce(reduce_func, values, initial)
        else:
            result = reduce(reduce_func, values)
        
        print "Result: %s" % result
        return result
    
    def calculate_statistics(self, column):
        """Calculate basic statistics for a numeric column."""
        print "Calculating statistics for '%s'..." % column
        
        # Extract numeric values
        values = []
        for row in self.data:
            try:
                val = float(row.get(column, 0))
                values.append(val)
            except (ValueError, TypeError):
                pass
        
        if not values:
            print "No numeric values found!"
            return None
        
        n = len(values)
        total = sum(values)
        mean = total / n
        
        # Calculate variance and std dev
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = variance ** 0.5
        
        # Sort for median and percentiles
        sorted_values = sorted(values)
        median = sorted_values[n / 2] if n % 2 else (sorted_values[n/2 - 1] + sorted_values[n/2]) / 2
        
        stats = {
            'count': n,
            'sum': total,
            'mean': mean,
            'median': median,
            'min': min(values),
            'max': max(values),
            'std_dev': std_dev,
            'variance': variance,
        }
        
        print "Statistics:"
        for key, value in stats.iteritems():
            print "  %s: %.4f" % (key, value)
        
        self.results[column] = stats
        return stats
    
    def group_by(self, column):
        """Group data by a column."""
        print "Grouping by '%s'..." % column
        
        groups = collections.defaultdict(list)
        for row in self.data:
            key = row.get(column, 'Unknown')
            groups[key].append(row)
        
        print "Found %d groups:" % len(groups)
        for key, items in groups.iteritems():
            print "  %s: %d items" % (key, len(items))
        
        return dict(groups)
    
    def sort_data(self, column, reverse=False):
        """Sort data by a column."""
        print "Sorting by '%s' (reverse=%s)..." % (column, reverse)
        
        sorted_data = sorted(self.data, key=lambda row: row.get(column, ''), reverse=reverse)
        return sorted_data
    
    def export_results(self, filepath):
        """Export analysis results to a file."""
        print "Exporting results to %s..." % filepath
        
        output = cStringIO.StringIO()
        output.write("DATA ANALYSIS REPORT\n")
        output.write("=" * 50 + "\n\n")
        
        for column, stats in self.results.iteritems():
            output.write("Column: %s\n" % column)
            output.write("-" * 30 + "\n")
            for key, value in stats.iteritems():
                output.write("  %s: %s\n" % (key, value))
            output.write("\n")
        
        report = output.getvalue()
        output.close()
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        print "Export complete!"
        return report
    
    def save_state(self, filepath):
        """Save analyzer state to a pickle file."""
        print "Saving state to %s..." % filepath
        
        state = {
            'data': self.data,
            'results': self.results,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        print "State saved!"
    
    def load_state(self, filepath):
        """Load analyzer state from a pickle file."""
        print "Loading state from %s..." % filepath
        
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        self.data = state.get('data', [])
        self.results = state.get('results', {})
        
        print "State loaded! %d rows, %d result sets" % (len(self.data), len(self.results))


def main():
    print "Data Analytics Tool v1.0"
    print "=" * 40
    
    analyzer = DataAnalyzer()
    
    print "\nCommands: load, stats, group, sort, filter, export, save, restore, quit"
    
    while True:
        cmd = raw_input("\nanalytics> ").strip().lower()
        
        if cmd == 'quit':
            break
        elif cmd == 'load':
            filepath = raw_input("CSV file path: ")
            analyzer.load_csv(filepath)
        elif cmd == 'stats':
            column = raw_input("Column name: ")
            analyzer.calculate_statistics(column)
        elif cmd == 'group':
            column = raw_input("Group by column: ")
            analyzer.group_by(column)
        elif cmd == 'sort':
            column = raw_input("Sort by column: ")
            reverse = raw_input("Reverse? (y/n): ").lower() == 'y'
            result = analyzer.sort_data(column, reverse)
            print "Sorted %d rows" % len(result)
        elif cmd == 'filter':
            column = raw_input("Filter column: ")
            value = raw_input("Contains value: ")
            result = analyzer.filter_data(column, lambda x: value in str(x))
            print "Filtered to %d rows" % len(result)
        elif cmd == 'export':
            filepath = raw_input("Export to: ")
            analyzer.export_results(filepath)
        elif cmd == 'save':
            filepath = raw_input("Save state to: ")
            analyzer.save_state(filepath)
        elif cmd == 'restore':
            filepath = raw_input("Load state from: ")
            analyzer.load_state(filepath)
        else:
            print "Unknown command: %s" % cmd
    
    print "Goodbye!"


if __name__ == '__main__':
    main()
