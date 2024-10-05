from setuptools import setup

setup(
    name="tinyoscquery",
    version='0.1.3',
    description="Quick and dirty python implementation for OSCQuery",
    author="CyberKitsune",
    packages=['tinyoscquery', 'tinyoscquery.shared'],
    install_requires=['zeroconf==0.39.1', 'requests']
)