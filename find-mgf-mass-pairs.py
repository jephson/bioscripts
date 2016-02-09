#!/usr/bin/env python

# TODO pass these on the command line?
MASS_DIFFERENCE = 12.084
EPSILON = 0.001
MAX_TIME_DIFFERENCE = 30

import sys

# Library-ish functions and classes first

# Magic function to erase the previous line we printed and overwrite
# it, for a nicer progress display
def print_to_start(string):
    sys.stdout.write('\r\033[K' + string)
    sys.stdout.flush()

class Ions:
    def __init__(self, metadata, intensities):
        self.metadata = metadata
        self.intensities = intensities
    def write(self, f):
        f.write('BEGIN IONS\n')
        for key in self.metadata:
            f.write('{0}={1}\n'.format(key, self.metadata[key]))
        for mass, intensity in self.intensities:
            f.write("{0} {1}\n".format(mass, intensity))
        f.write('END IONS\n')

# Generator that takes a file and generates Ions
def read_ions(in_f):
    intensities = []
    metadata = {}
    for line in in_f:
        line = line.strip()
        if line == '' or line == 'BEGIN IONS':
            pass
        elif line == 'END IONS':
            ions = Ions(metadata, intensities)
            metadata = {}
            intensities = []
            yield ions
        else:
            parts = line.split('=', 1)
            if len(parts) == 1:
                parts = line.split(' ')
                assert len(parts) == 2
                intensities.append(parts)
            elif len(parts) == 2:
                metadata[parts[0]] = parts[1]

# Then the function that solves our actual problem.
# Read all the records from input, sort by PEPMASS, then for each element
# look for one with an exactly different mass 
def find_similar_mass(in_filename, out_filename):
    print("Reading {0}... ".format(in_filename))
    records = []
    with open(in_filename) as in_f:
        for ions in read_ions(in_f):
            records.append(ions)
            print_to_start("{0} records read".format(len(records)))
    records.sort(key=pepmass)
    found = 0
    with open(out_filename, 'w') as out_f:
        for i in range(0, len(records) - 1):
            left = records[i]
            right = find_by_pepmass(pepmass(left) + MASS_DIFFERENCE, records[i + 1:])
            if right is not None:
                if abs(rtinseconds(left) - rtinseconds(right)) < MAX_TIME_DIFFERENCE:
                    found += 1
                    print_to_start("{0} pairs written".format(found))
                    left.write(out_f)
                    right.write(out_f)

def pepmass(ions):
    return float(ions.metadata['PEPMASS'])

def rtinseconds(ions):
    return float(ions.metadata['RTINSECONDS'])

# Binary search a sorted list of records to find one with a similar PEPMASS
def find_by_pepmass(target_mass, records):
    def recurse(first, last):
        mid = (first + last) / 2 
        if first > last:
            return None
        else:
            mid_mass = pepmass(records[mid])
            if abs(mid_mass - target_mass) < EPSILON:
                return records[mid]
            elif mid_mass < target_mass:
                return recurse(mid + 1, last)
            else: # mid_mass > target_mass
                return recurse(first, mid - 1)
    return recurse(0, len(records) - 1)
                
if __name__ == '__main__':
    if len(sys.argv) == 3:
        find_similar_mass(sys.argv[1], sys.argv[2])
    else:
        print("Usage: {0} input-file output-file".format(sys.argv[0]))
