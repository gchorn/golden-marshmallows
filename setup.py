from time import time
from setuptools import setup, find_packages

setup(
    name='golden_marshmallows',
    version='0.1',
    author='Guillaume Chorn',
    author_email='guillaume.chorn@gmail.com',
    packages=find_packages(),
    url='https://github.com/gchorn/golden-marshmallows',
    download_url='https://github.com/gchorn/golden-marshmallows/archive/v0.1.0.tar.gz',
    description='Marshmallow Schema subclass that auto-defines fields based on'
                ' SQLAlchemy classes',
    install_requires=['marshmallow>=2.9.0', 'SQLAlchemy>=0.9.8']
)
