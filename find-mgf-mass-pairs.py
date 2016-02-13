#!/usr/bin/env python

# TODO pass these on the command line?
MASS_DIFFERENCE = 12.07573
EPSILON = 0.001
MAX_TIME_DIFFERENCE = 30

import sys
from operator import methodcaller

# Library-ish functions and classes first

# Magic function to erase the previous line we printed and overwrite
# it, for a nicer progress display
def print_to_start(string):
    sys.stdout.write('\r\033[K' + string)
    sys.stdout.flush()

class MS2spectrum:
    def __init__(self, metadata, masses):
        self.metadata = metadata
        self.masses = masses

    def write(self, f):
        f.write('BEGIN IONS\n')
        for key in self.metadata:
            f.write('{0}={1}\n'.format(key, self.metadata[key]))
        for mass, intensity in self.masses:
            f.write("{0} {1}\n".format(mass, intensity))
        f.write('END IONS\n')

    def pepmass(self):
        # Some programs write 2 numbers to the PEPMASS line, the second being
        # intensity. Let's ignore that for now.
        return float(self.metadata['PEPMASS'].split(' ')[0])

    def rtinseconds(self):
        return float(self.metadata['RTINSECONDS'])

    def charge(self):
        chg = self.metadata['CHARGE']
        sign = chg[-1:]
        assert sign == '+' or sign == '-'
        chg = chg[:-1]
        return int(sign + chg) 


# Generator that takes a file and generates instances of MS2spectrum
def read_spectra(in_f):
    masses = []
    metadata = {}
    for line in in_f:
        line = line.strip()
        if line == '' or line == 'BEGIN IONS':
            pass
        elif line == 'END IONS':
            spectrum = MS2spectrum(metadata, masses)
            metadata = {}
            masses = []
            yield spectrum
        else:
            parts = line.split('=', 1)
            if len(parts) == 1:
                parts = line.split(' ')
                assert len(parts) == 2
                masses.append(parts)
            elif len(parts) == 2:
                metadata[parts[0]] = parts[1]

# Then the function that solves our actual problem.
# Read all the records from input, sort by PEPMASS, then for each element
# look for one with an exactly different mass 
def find_similar_mass(in_filename, out_filename):
    print("Reading {0}... ".format(in_filename))
    records = []
    with open(in_filename) as in_f:
        for spectrum in read_spectra(in_f):
            records.append(spectrum)
            print_to_start("{0} records read".format(len(records)))
    print('')
    records.sort(key=methodcaller('pepmass'))
    found = 0
    with open(out_filename, 'w') as out_f:
        for i in range(0, len(records) - 1):
            left = records[i]
            right_target_mass = left.pepmass() + MASS_DIFFERENCE / left.charge()
            right_candidates = find_range_by_pepmass(right_target_mass, records[i + 1:])
            filtered = [right for right in right_candidates if charge_time_match(left, right)]
            for right in filtered:
                found += 1
                left.write(out_f)
                right.write(out_f)
            print_to_start("{0} spectra compared, {1} pairs written".format(i + 1, found))
        print('')

def charge_time_match(left, right):
    return abs(left.rtinseconds() - right.rtinseconds()) < MAX_TIME_DIFFERENCE \
        and left.charge() == right.charge()

# Binary search a sorted list of records to find ones with a similar PEPMASS
def find_range_by_pepmass(target_mass_centre, records):
    def mass(i):
        return records[i].pepmass()

    def recurse(left, right, target_mass):
        assert left <= right
        if left == right:
            return left
        if left + 1 == right and mass(left) < target_mass:
            return right
        mid = (left + right) // 2
        if mass(mid) < target_mass:
            return recurse(mid, right, target_mass)
        else: # mass(mid) > target_mass
            return recurse(left, mid, target_mass)

    left  = recurse(0, len(records) - 1, target_mass_centre - EPSILON)
    right = recurse(0, len(records) - 1, target_mass_centre + EPSILON)
    return records[left:right]

if __name__ == '__main__':
    if len(sys.argv) == 3:
        find_similar_mass(sys.argv[1], sys.argv[2])
    else:
        print("Usage: {0} input-file output-file".format(sys.argv[0]))
