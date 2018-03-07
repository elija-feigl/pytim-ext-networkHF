import codecs
import os
import sys

try:
    from setuptools import find_packages
except ImportError:
    sys.stderr.write("Error : setuptools is not installed\n"
                     "Use pip install setuptools\n")
    exit(100)

from setuptools import setup
from setuptools.command.test import test as TestCommand
from distutils.extension import Extension


try:
    import numpy
except ImportError:
    sys.stderr.write("Error : numpy is not installed\n"
                     "Use pip install numpy\n")
    exit(100)

try:
    import networkx
except ImportError:
    sys.stderr.write("Error : networkx is not installed\n"
                     "Use pip install numpy\n")
    exit(100)

try:
    import scipy
except ImportError:
    sys.stderr.write("Error : scipy is not installed\n"
                     "Use pip install numpy\n")
    exit(100)

try:
    import pytim
except ImportError:
    sys.stderr.write("Error : pytim is not installed\n"
                     "Use pip install numpy\n")
    exit(100)


here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

if sys.platform == 'darwin' and os.path.exists('/usr/bin/xcodebuild'):
    os.environ['ARCHFLAGS'] = ''

setup(
    name = "network-pytim",
    version = "0.1.4",
    author = "Elija Feigl",
    author_email = "elija.feigl@gmail.com",
    description = ("calucate network of Md trajectory"),
    license = "none",
    keywords = "MD, network",
    url = "",
    long_description="none",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: no License',
        'Programming Language :: Python :: 2.7',
    ],


    packages=find_packages(),
      
    install_requires=[
                        'MDAnalysis>=0.16', 'PyWavelets>=0.5.2', 'numpy>=1.12.0', 'scipy>=1.0',
                        'scikit-image>=0.13.0', 'cython>=0.24.1', 'sphinx>=1.4.3',
                        'matplotlib', 'pytest'
                        ],
      
)
