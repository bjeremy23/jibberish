#!/usr/bin/env python3
from setuptools import setup, find_packages

# Read the README file for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the version from version.py
version = {}
with open("app/version.py", "r") as fv:
    exec(fv.read(), version)

setup(
    name="jibberish",
    version=version["__version__"],
    author="Jeremy Brown",
    author_email="bjeremy32@yahoo.com",  # Update with your actual email
    description="An AI-powered Linux Shell",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bjeremy23/jibberish",
    packages=find_packages(),
    include_package_data=True,
    scripts=["scripts/jbrsh"],  # Include the wrapper script
    install_requires=[
        "click>=8.0.0",
        "openai>=1.0.0",
        "psutil>=7.0.0",
    ],
    extras_require={
        "azure": [
            "azure-identity>=1.12.0",
            "azureopenai>=0.0.1", 
        ],
    },
    entry_points={
        "console_scripts": [
            "jibberish=app.jibberish:main",
            "jbrsh=app.jibberish:main",
            "jbrsh-version=app.version_standalone:main",
            "jbrsh-question=app.question_standalone:main",
            "jbrsh-command=app.command_standalone:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
)
