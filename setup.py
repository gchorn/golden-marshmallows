from time import time
from setuptools import setup, find_packages

setup(
    name='golden_marshmallows',
    version='0.1.%s' % int(time()),
    author='Guillaume Chorn',
    author_email='guillaume.chorn@gmail.com',
    packages=find_packages(),
    description='Marshmallow Schema subclass that auto-defines fields based on'
                ' SQLAlchemy classes',
    install_requires=['marshmallow>=2.9.0', 'SQLAlchemy>=0.9.8']
)
