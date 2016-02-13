#!/usr/bin/env python

# To identify which program made an mgf file
# and count spectra of each type within file

import sys
from operator import methodcaller
from mgf import MS2spectrum, read_spectra

input_file = sys.argv[1]
types = {}
count = 0


with open(input_file, 'r') as in_f:
    for spectra in read_spectra(in_f):
        count += 1
        types[spectra.madeby()] = count

for a in types:
    print(a, types[a])

