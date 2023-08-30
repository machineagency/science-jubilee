import os
import setuptools

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name="science_jubilee",
    version="0.0.1",
    author="Machine Agency",
    author_email="b1air@uw.edu",
    description="Science with Jubilee",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/machineagency/science_jubilee",
    license="MIT",
    keywords= ['jubilee'],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.6',
    install_requires=['pyserial==3.5', 'ipykernel==6.25.1'] # ToDo
)