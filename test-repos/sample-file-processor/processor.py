#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File Processor - Python 2 Legacy Code
A file processing utility with old-style string formatting and file operations.
"""

import os
import sys
import ConfigParser
import cStringIO
import codecs


class FileProcessor:
    """Process various file types."""
    
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_count = 0
        self.error_count = 0
    
    def process_text_file(self, filepath):
        """Process a text file and return statistics."""
        print "Processing: %s" % filepath
        
        try:
            with codecs.open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count statistics
            lines = content.split('\n')
            words = content.split()
            chars = len(content)
            
            stats = {
                'lines': len(lines),
                'words': len(words),
                'chars': chars,
                'avg_line_length': chars / len(lines) if lines else 0,
            }
            
            print "  Lines: %d, Words: %d, Chars: %d" % (stats['lines'], stats['words'], stats['chars'])
            return stats
            
        except IOError, e:
            print "Error reading file: %s" % e
            self.error_count += 1
            return None
    
    def process_config_file(self, filepath):
        """Parse a configuration file."""
        print "Parsing config: %s" % filepath
        
        config = ConfigParser.ConfigParser()
        try:
            config.read(filepath)
            
            sections = config.sections()
            print "  Found %d sections: %s" % (len(sections), ', '.join(sections))
            
            result = {}
            for section in sections:
                result[section] = dict(config.items(section))
            
            return result
            
        except ConfigParser.Error, e:
            print "Config parsing error: %s" % e
            return None
    
    def batch_process(self, file_extension='.txt'):
        """Process all files with given extension in input directory."""
        print "Starting batch process..."
        print "Input directory: %s" % self.input_dir
        print "Looking for files with extension: %s" % file_extension
        
        if not os.path.exists(self.input_dir):
            print "Error: Input directory does not exist!"
            return
        
        files = os.listdir(self.input_dir)
        target_files = filter(lambda f: f.endswith(file_extension), files)
        
        print "Found %d files to process" % len(target_files)
        
        results = {}
        for filename in target_files:
            filepath = os.path.join(self.input_dir, filename)
            stats = self.process_text_file(filepath)
            if stats:
                results[filename] = stats
                self.processed_count += 1
        
        print "\nBatch processing complete!"
        print "Processed: %d, Errors: %d" % (self.processed_count, self.error_count)
        
        return results
    
    def generate_report(self, results):
        """Generate a summary report."""
        output = cStringIO.StringIO()
        
        output.write("=" * 50 + "\n")
        output.write("FILE PROCESSING REPORT\n")
        output.write("=" * 50 + "\n\n")
        
        total_lines = 0
        total_words = 0
        total_chars = 0
        
        for filename, stats in results.iteritems():
            output.write("File: %s\n" % filename)
            output.write("  Lines: %d\n" % stats['lines'])
            output.write("  Words: %d\n" % stats['words'])
            output.write("  Chars: %d\n" % stats['chars'])
            output.write("\n")
            
            total_lines += stats['lines']
            total_words += stats['words']
            total_chars += stats['chars']
        
        output.write("-" * 50 + "\n")
        output.write("TOTALS:\n")
        output.write("  Total Lines: %d\n" % total_lines)
        output.write("  Total Words: %d\n" % total_words)
        output.write("  Total Chars: %d\n" % total_chars)
        
        report = output.getvalue()
        output.close()
        
        return report


def main():
    print "File Processor v1.0"
    print "-" * 30
    
    input_dir = raw_input("Enter input directory: ")
    output_dir = raw_input("Enter output directory: ")
    extension = raw_input("Enter file extension (default .txt): ")
    
    if not extension:
        extension = '.txt'
    
    processor = FileProcessor(input_dir, output_dir)
    results = processor.batch_process(extension)
    
    if results:
        report = processor.generate_report(results)
        print "\n" + report
        
        save = raw_input("Save report to file? (y/n): ")
        if save.lower() == 'y':
            report_file = raw_input("Enter report filename: ")
            with open(report_file, 'w') as f:
                f.write(report)
            print "Report saved to %s" % report_file


if __name__ == '__main__':
    main()
