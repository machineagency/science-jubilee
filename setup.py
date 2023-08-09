import os
import setuptools

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name="duckbot",
    version="0.0.1",
    author="Blair Subbaraman",
    author_email="b1air@uw.edu",
    description="Duckweed (and other) science with Jubilee ",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/machineagency/duckbot",
    license="MIT",
    keywords= ['jubilee'],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.6'
    #install_requires=[''] # ToDo
)