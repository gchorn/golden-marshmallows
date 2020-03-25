from setuptools import setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='golden_marshmallows',
    version='0.3.0',
    author='Guillaume Chorn',
    author_email='guillaume.chorn@gmail.com',
    packages=['golden_marshmallows'],
    url='https://github.com/gchorn/golden-marshmallows',
    download_url='https://github.com/gchorn/golden-marshmallows/archive/v0.2.1.tar.gz',
    description='Marshmallow Schema subclass that auto-defines fields based on'
                ' SQLAlchemy classes',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['marshmallow<3', 'SQLAlchemy']
)
