#!/usr/bin/env python

# TODO pass these on the command line?

# Difference in mass we are looking for
MASS_DIFFERENCE = 12.07573

# Masses are considered equivalent if within this
EPSILON = 0.001

# Records match if RTINSECONDS differ by no more than this
MAX_TIME_DIFFERENCE = 30

# Next 3 mean "find 4 highest intensity fragments in mass range 50-150, then 4 in 150-250, etc"
FILTERING_MASS_RANGE_START = 50
FILTERING_MASS_RANGE_INCREMENT = 100
FILTERING_FRAGMENTS_PER_RANGE = 4

# Need at least this many fragments with MASS_DIFFERENCE / charge matching for a record to match
SHIFTED_FRAGMENTS_NEEDED = 4

# Total number of fragments needed, with at least the number of shifted fragments above.
SHIFTED_OR_UNSHIFTED_FRAGMENTS_NEEDED = 10

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
         open(out_filename_base + '_matched_fragments.txt', 'w') as out_matched_f, \
         open(out_filename_base + '_summary.txt', 'w') as out_summary_f:
        for i in range(0, len(records) - 1):
            left = records[i]
            right_target_mass = left.pepmass() + MASS_DIFFERENCE / left.charge()
            right_candidates = find_range_by_pepmass(right_target_mass, records[i + 1:])
            filtered = [right for right in right_candidates
                        if good_match(left, right, out_matched_f)]
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

def good_match(left, right, out_f):
    return charge_time_match(left, right) and fragment_diff_match(left, right, out_f)

def charge_time_match(left, right):
    return abs(left.rtinseconds() - right.rtinseconds()) < MAX_TIME_DIFFERENCE \
        and left.charge() == right.charge()

def fragment_diff_match(left, right, out_f):
    out_f.write("\nCompared: {} with {}\n".format(left.title(), right.title()))
    right_masses = right.fragment_masses()
    shifted_fragments = 0
    unshifted_fragments = 0
    for l in left.fragment_masses():
        matches = binary_search_range(
            right_masses, lambda r: r < l - EPSILON, lambda r: r < l + EPSILON)
        if len(matches) > 0:
            out_f.write("Unshifted match: {}\n".format(matches[0]))
            unshifted_fragments += 1
        for c in range(1, left.charge()):
            target = l + MASS_DIFFERENCE / c
            matches = binary_search_range(
                right_masses, lambda r: r < target - EPSILON, lambda r: r < target + EPSILON)
            if len(matches) > 0:
                out_f.write("Shifted match: {} {} {}\n".format(matches[0], l, MASS_DIFFERENCE / c))
                shifted_fragments += 1
    return shifted_fragments + unshifted_fragments > SHIFTED_OR_UNSHIFTED_FRAGMENTS_NEEDED and \
        shifted_fragments > SHIFTED_FRAGMENTS_NEEDED

# Binary search a sorted list of records to find ones with a similar PEPMASS
def find_range_by_pepmass(target_mass_centre, records):
    def lower_pepmass(diff):
        return lambda record: record.pepmass() < target_mass_centre + diff
    return binary_search_range(records, lower_pepmass(-EPSILON), lower_pepmass(EPSILON))

def binary_search_range(records, left_pred, right_pred):
    left  = binary_search(records, left_pred)
    right = binary_search(records, right_pred)
    return records[left:right]

def binary_search(records, predicate):
    def recurse(left, right):
        assert left <= right
        if left == right:
            return left
        if left + 1 == right and predicate(records[left]):
            return right
        mid = (left + right) // 2
        if predicate(records[mid]):
            return recurse(mid, right)
        else:
            return recurse(left, mid)
    return recurse(0, len(records) - 1)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        find_similar_mass(sys.argv[1], sys.argv[2])
    else:
        print("Usage: {0} input-file output-file-base".format(sys.argv[0]))
