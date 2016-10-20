import os
from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    long_description =  f.read()

setup(
    name='pytwitcher',
    version='0.0.1',
    author='Anthony Dong',
    author_email='sirakain132@gmail.com',
    descriptions='Framework to develop Twitch bots',
    license='MIT',
    url='https://github.com/adongy/pytwitcher',
    packages=['pytwitcher'],
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
    ]
)
