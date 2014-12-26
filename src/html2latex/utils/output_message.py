# Standard Library
import os
import re
import sys


# Functions for outputting message to stderr


def warning_message(message, newLine=True):
    '''Output a warning message to stderr.'''
    sys.stderr.write('WARNING: ' + message)
    if newLine:
        sys.stderr.write('\n')


def information_message(message, newLine=True):
    '''Output an information message to stderr.'''
    sys.stderr.write('INFO: ' + message)
    if newLine:
        sys.stderr.write('\n')


def error_message(message, newLine=True, terminate=True):
    '''Output an error message to stderr.'''
    global commandlineArguments
    sys.stderr.write('ERROR: ' + message)
    if newLine:
        sys.stderr.write('\n')
    if terminate:
        sys.exit()
