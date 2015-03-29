#!/usr/bin/env python

import sys

files = '1filenames.txt'

# Edit this to control file size.
max_file_length = 2000000000
#max_file_length = 1000000

# Probably doesn't need tweaking
max_memory_use = 1000000
# But our algorithm only works if max_memory =< max_file
max_memory_use = min(max_file_length, max_memory_use)

# Magic function to erase the previous line we printed and overwrite
# it, for a nicer progress display
def print_to_start(string):
    sys.stdout.write('\r\033[K' + string)
    sys.stdout.flush()

def split_files():
    ## run from directory containing results folders
    with open(files) as f: ### file of folder names eg lf2_26_1 not full path
        filenames = f.readlines()
    for filename in filenames:
        split_file(filename.strip())

def split_file(filename):
    print("Splitting {0}... ".format(filename))
    with open(filename) as in_f:
        chunk = ""
        chunk_no = 0
        file_size = 0
        # NB: we can't use a with statement for out_f, we need to
        # directly control how we open / close it
        out_f = open('{0}_{1}'.format(filename, chunk_no), 'w')
        for line in in_f:
            line = line.strip()
            chunk += line + '\n'
            # Only do anything at a record boundary
            if line == 'END IONS':
                length = len(chunk)
                # If we've used enough memory, write it all out.
                if length >= max_memory_use:
                    out_f.write(chunk)
                    chunk = ''
                    file_size += length
                # ...then if that took us over the chunk size, start
                # a new file
                if file_size >= max_file_length:
                    file_size = 0
                    out_f.close()
                    print_to_start("  Chunk {0} written.".format(chunk_no))
                    chunk_no += 1
                    out_f = open('{0}_{1}'.format(filename, chunk_no), 'w')
        out_f.write(chunk)
        out_f.close()
        print_to_start('  Wrote {0} chunks.\n'.format(chunk_no + 1))

if __name__ == '__main__':
    split_files()
