import setuptools
from codecs import open  # To use a consistent encoding
from os import path
from platform import system, machine
import subprocess

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.md'), encoding='utf-8') as f:
    long_description = f.read()
    
install_deps = ['darkdetect', 'pyserial']

# Raspberry Pi needs python3-pyqt5 and python3-pyqt5.qtserialport
# which can only be installed with apt-get
if (system() == "Linux") and (machine() == "armv7l"):
    cmd = ['sudo','apt-get','install','python3-pyqt5','python3-pyqt5.qtserialport']
    subprocess.run(cmd)
else:
    install_deps.append('pyqt5')

setuptools.setup(
    name='RTK_Firmware_Uploader',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='1.4.10',

    description='Application to upload firmware to SparkFun RTK products',
    long_description=long_description,

    # The project's main homepage.
    url='https://docs.sparkfun.com/SparkFun_RTK_Firmware/intro/',

    # Author details
    author='SparkFun Electronics',
    author_email='sales@sparkfun.com',

    project_urls = {
        "Bug Tracker" : "https://github.com/sparkfun/SparkFun_RTK_Firmware_Uploader/issues",
        "Repository"   : "https://github.com/sparkfun/SparkFun_RTK_Firmware_Uploader"
    },
    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Production Stable :: 5',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Hardware Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',

    ],

    download_url="https://github.com/sparkfun/SparkFun_RTK_Firmware_Uploader/releases",

    # What does your project relate to?
    keywords='Firmware SparkFun RTK Uploader',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=["RTK_Firmware_Uploader", "RTK_Firmware_Uploader/resource"],

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    install_requires=install_deps,

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'RTK_Firmware_Uploader/resource': ['*.png', '*.jpg', '*.ico', '*.bin', '*.icns'],
    },



    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': ['RTK_Firmware_Upload=RTK_Firmware_Uploader:startUploaderGUI',
        ],
    },
)
