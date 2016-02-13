# Based on a mascot generic file format tested with output
# from MSConvert, Proteome Discoverer and Progenesis
# these three programes define the metadata a bit differently

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
# This generator will have trouble with some input files have have more than
# one = in the TITLE line

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

