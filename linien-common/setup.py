import re

from setuptools import find_packages, setup

version_file = "linien_client/_version.py"
with open(version_file, "rt") as f:
    verstrline = f.read()
mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", verstrline, re.M)
verstr = mo.group(1)


setup(
    name="linien-common",
    version=verstr,
    author="Benjamin Wiegand",
    author_email="highwaychile@posteo.de",
    maintainer="Bastian Leykauf",
    maintainer_email="leykauf@physik.hu-berlin.de",
    description="Part of linien that is used by all components.",
    long_description="Have a look at the 'linien' package for installation instructions.",  # noqa: E501
    long_description_content_type="text/x-rst",
    url="https://github.com/linien-org/linien",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=["numpy>=1.11.0", "scipy>=0.17.0", "plumbum>=1.6.9"],
)
