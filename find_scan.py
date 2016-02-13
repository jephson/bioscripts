#!/usr/bin/env python

# To pull out a specific spectrum by number from an mgf file
# using the MS2spectrum module.

import sys
from operator import methodcaller
from mgf import MS2spectrum, read_spectra

scan = sys.argv[1]
input_file = 'mini.mgf'
output_file = 'out.mgf'


with open(input_file, 'r') as in_f, open(output_file, 'w') as out_f:
    for spectra in read_spectra(in_f):
#        print('mass is {0} charge is {1}'.format(spectra.pepmass(),\
#       spectra.charge()))
        title = spectra.title()
        if title.find(scan) > 0:
            print(spectra.write(out_f))



