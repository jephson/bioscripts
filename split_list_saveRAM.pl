#!/usr/bin/perl

use strict;
use warnings;

my $files = '1filenames.txt';

# Edit this to control file size.
my $max_file_length = 2000000000;
#my $max_file_length = 100000000;

my $max_memory_use = 1000000; # Probably doesn't need tweaking

## run from directory containing results folders
open FILE, "<$files"; ### file of folder names eg lf2_26_1 not full path
my @files = <FILE>;

close FILE;

foreach my $file (@files) {
    if ($file =~ m/\w+/){
        chomp $file;

        print "Splitting $file...\n";

        open(FH, $file);
        my $str = "";
        my $chunk_no = 0;
        my $file_size = 0;
        open(OUT, ">${file}_$chunk_no");
        while(my $line = <FH>) {
            chomp($line);
            $str .= "$line\n";
            # Only do anything at a record boundary
            if ($line =~ /END IONS/) {
                my $len = length $str;
                # If we've used enough memory, write it all out.
                if ($len >= $max_memory_use) {
                    print OUT "$str";
                    $str = "";
                    $file_size += $len;
                }
                # ...then if that took us over the chunk size, start
                # a new file
                if ($file_size >= $max_file_length) {
                    $file_size = 0;
                    close OUT;
                    print "  Chunk $chunk_no written.\n";
                    $chunk_no ++;
                    open(OUT, ">${file}_$chunk_no");
                }
            }
        }
        print OUT "$str";
        close OUT;
        close FH;
    }
}

#getc();
