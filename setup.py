from setuptools import setup

setup(
    name="tinyoscquery",
    version='0.1.1',
    description="Quick and dirty python implementation for OSCQuery",
    author="CyberKitsune",
    packages=['tinyoscquery', 'tinyoscquery.shared'],
    install_requires=['zeroconf', 'requests']
)