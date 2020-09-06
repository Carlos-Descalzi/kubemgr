import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

if os.path.isfile('requirements.txt'):
    with open("requirements.txt", "r") as f:
        requirements = f.readlines()
else:
    requirements = []

setuptools.setup(
    name="kubemgr",
    version="0.0.1",
    author="Carlos Descalzi",
    author_email="carlos.descalzi@gmail.com",
    description="A terminal-based Kubernetes cluster managing tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Carlos-Descalzi/kubemgr",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["kubemgr = kubemgr.main:main"]},
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
