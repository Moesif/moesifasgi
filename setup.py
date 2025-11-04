# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from codecs import open
from os import path
import os

here = os.path.abspath(os.path.dirname(__file__))

def read_version(filepath="VERSION"):
    """Reads the version from the specified file."""
    if not hasattr(read_version, '_version'):
        try:
            with open(os.path.join(here, filepath), 'r') as f:
                version = f.readline().strip()
                if version:  # Ensure the file is not empty
                    read_version._version = version
                else:
                    raise ValueError("VERSION file is empty.")
        except FileNotFoundError:
            read_version._version = None
        except ValueError as e:
            print(f"Error: {e}")
            read_version._version = None

    return read_version._version

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
        'Development Status :: 5 - Production/Stable',
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
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords='log analysis restful api development debug asgi fastapi http middleware',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['starlette>=0.16.0', 'moesifapi>=1.5.5', 'moesifpythonrequest>=0.3.4', 'packaging'],
    extras_require={
        'dev': [],
        'test': ['nose'],
    },
)
