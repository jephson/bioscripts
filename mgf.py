class MS2spectrum:
    def __init__(self, metadata, fragments):
        self.metadata = metadata
        self.fragments = fragments

    def write(self, f):
        f.write('BEGIN IONS\n')
        for key in self.metadata:
            f.write('{0}={1}\n'.format(key, self.metadata[key]))
        for fragment in self.fragments:
            f.write(fragment.format())
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

    def title(self):
        return self.metadata['TITLE']

class MS2fragment:
    def __init__(self, mass, intensity):
        self.mass = mass
        self.intensity = intensity

    def format(self):
        return "{0} {1}\n".format(self.mass, self.intensity)

# Generator that takes a file and generates instances of MS2spectrum
def read_spectra(in_f):
    fragments = []
    metadata = {}
    for line in in_f:
        line = line.strip()
        if line == '' or line == 'BEGIN IONS':
            pass
        elif line == 'END IONS':
            spectrum = MS2spectrum(metadata, fragments)
            metadata = {}
            fragments = []
            yield spectrum
        else:
            parts = line.split('=', 1)
            if len(parts) == 1:
                parts = line.split(' ')
                assert len(parts) == 2
                fragments.append(MS2fragment(float(parts[0]), float(parts[1])))
            elif len(parts) == 2:
                metadata[parts[0]] = parts[1]

