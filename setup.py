#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup configuration for Thyrse

This setup.py is compatible with modern setuptools and works alongside
pyproject.toml for maximum compatibility with different build systems.
"""

from setuptools import setup, find_packages

setup(
    name="thyrse",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        "thyrse": ["py.typed"],
    },
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0",
            "mypy>=0.900",
        ],
    },
    author="Thyrse Contributors",
    description="Fast and elegant functional programming toolkit for Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/kagami-meika/thyrse.git",
    project_urls={
        "Documentation": "https://github.com/kagami-meika/thyrse",
        "Source Code": "https://github.com/kagami-meika/thyrse",
        "Bug Tracker": "https://github.com/kagami-meika/thyrse/issues",
        "Changelog": "https://github.com/kagami-meika/thyrse/blob/main/CHANGELOG.md",
    },
    license="CC0-1.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    keywords=[
        "functional-programming",
        "lambda",
        "combinators",
        "functional",
        "python",
    ],
)
