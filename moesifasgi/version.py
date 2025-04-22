from os import path

def read_version(filepath="../VERSION"):
    if not hasattr(read_version, '_version'):
        here = path.abspath(path.dirname(__file__))

        try:
            with open(path.join(here, filepath), 'r') as f:
                read_version._version = f.readline().strip()
        except FileNotFoundError:
            read_version._version = None
    return read_version._version
