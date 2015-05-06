#!/usr/bin/env python3

import sys
import operator

# Split masses in chunks of this
mass_range_size = 100
# And for each chunk take this many with the highest intensities
top_intensity_count = 4

# Magic function to erase the previous line we printed and overwrite
# it, for a nicer progress display
def print_to_start(string):
    sys.stdout.write('\r\033[K' + string)
    sys.stdout.flush()

def filter_file(in_filename, out_filename):
    print("Filtering {0}... ".format(in_filename))
    with open(in_filename) as in_f, open(out_filename, 'w') as out_f:
        record = ''
        intensities = []
        max_mass = mass_range_size
        records_done = 0
        for line in in_f:
            line = line.strip()
            if line == 'BEGIN IONS' or line.find('=') != -1:
                record += line + '\n'
            elif line == 'END IONS':
                record += format_intensities(top_intensities(intensities))
                record += line + '\n'
                out_f.write(record)
                record = ''
                intensities = []
                max_mass = mass_range_size                
                records_done += 1
                print_to_start("{0} records filtered".format(records_done))
            else:
                parts = line.split(' ')
                assert len(parts) == 2
                mass = float(parts[0])
                intensity = float(parts[1])
                if mass > max_mass:
                    record += format_intensities(top_intensities(intensities))
                    intensities = []
                    max_mass = round_up_to_multiple(mass, mass_range_size)
                intensities.append((mass, intensity))

def round_up_to_multiple(num, multiple):
    return (int(num / multiple) + 1) * multiple

def top_intensities(intensities):
    # i.e. sort by second element of tuple (intensity), descending
    intensities.sort(key=operator.itemgetter(1), reverse=True)
    # Then take the first top_intensity_count
    intensities = intensities[0:top_intensity_count]
    # Then sort back into mass order
    intensities.sort(key=operator.itemgetter(0))
    return intensities

def format_intensities(intensities):
    result = ''
    for mass, intensity in intensities:
        result += "{0} {1}\n".format(mass, intensity)
    return result

if __name__ == '__main__':
    if len(sys.argv) == 3:
        filter_file(sys.argv[1], sys.argv[2])
    else:
        print("Usage: {0} input-file output-file".format(sys.argv[0]))

