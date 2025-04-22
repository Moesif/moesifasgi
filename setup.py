# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Function to read the version from a file
def read_version():
    version_file = path.join(here, "moesifasgi", "version.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Version not found.")

# Get the long description from the README file
long_description = ''
if path.exists('README.md'):
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='moesifasgi',
    version=read_version(),
    description='Moesif Middleware for Python ASGI based platforms (FastAPI & Others)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://www.moesif.com/docs/server-integration/python-asgi/',
    author='Moesif, Inc',
    author_email='keyur@moesif.com',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Internet :: Log Analysis',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='log analysis restful api development debug asgi fastapi http middleware',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['starlette>=0.16.0', 'moesifapi>=1.5.4', 'moesifpythonrequest>=0.3.4'],
    extras_require={
        'dev': [],
        'test': ['nose'],
    },
)
