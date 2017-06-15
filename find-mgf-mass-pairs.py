#!/usr/bin/env python

# TODO pass these on the command line?
MASS_DIFFERENCE = 12.07573
EPSILON = 0.001
MAX_TIME_DIFFERENCE = 30
FILTERING_MASS_RANGE_START = 50
FILTERING_MASS_RANGE_INCREMENT = 100
FILTERING_FRAGMENTS_PER_RANGE = 4

import sys
import copy
import math
from operator import methodcaller, attrgetter
from mgf import MS2spectrum, read_spectra

# Magic function to erase the previous line we printed and overwrite
# it, for a nicer progress display
def print_to_start(string):
    sys.stdout.write('\r\033[K' + string)
    sys.stdout.flush()

# The function that solves our actual problem.
# Read all the records from input, sort by PEPMASS, then for each element
# look for one with an exactly different mass 
def find_similar_mass(in_filename, out_filename_base):
    print("Reading {0}... ".format(in_filename))
    records = []
    with open(in_filename) as in_f:
        for spectrum in read_spectra(in_f):
            records.append(filter_weak_fragments(spectrum))
            print_to_start("{0} records read".format(len(records)))
    print('')
    records.sort(key=methodcaller('pepmass'))
    found = 0
    with open(out_filename_base + '_light.mgf', 'w') as out_light_f, \
         open(out_filename_base + '_heavy.mgf', 'w') as out_heavy_f, \
         open(out_filename_base + '_summary.txt', 'w') as out_summary_f:
        for i in range(0, len(records) - 1):
            left = records[i]
            right_target_mass = left.pepmass() + MASS_DIFFERENCE / left.charge()
            right_candidates = find_range_by_pepmass(right_target_mass, records[i + 1:])
            filtered = [right for right in right_candidates if good_match(left, right)]
            for right in filtered:
                found += 1
                left.write(out_light_f)
                right.write(out_heavy_f)
                out_summary_f.write("{0}\t{1}\t{2}\t{3}\n".format(
                    left.title(),
                    right.title(),
                    left.pepmass(),
                    right.pepmass()
                ))
            print_to_start("{0} spectra compared, {1} pairs written".format(i + 1, found))
        print('')

def filter_weak_fragments(spectrum):
    filtered = []
    i = 0
    fragments = spectrum.fragments
    for ceil in range(FILTERING_MASS_RANGE_START,
                      int(math.ceil(fragments[-1].mass)),
                      FILTERING_MASS_RANGE_INCREMENT):
        segment = []
        while fragments[i].mass < ceil and i < len(fragments):
            segment.append(fragments[i])
            i += 1
        segment.sort(key=attrgetter('intensity'), reverse=True)
        segment = segment[:FILTERING_FRAGMENTS_PER_RANGE]
        segment.sort(key=attrgetter('mass'))
        filtered.extend(segment)
    result = copy.copy(spectrum)
    result.fragments = filtered
    return result

def good_match(left, right):
    return charge_time_match(left, right)

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
        print("Usage: {0} input-file output-file-base".format(sys.argv[0]))
