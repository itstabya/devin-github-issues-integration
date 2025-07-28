#!/usr/bin/env python3
"""
Setup script for GitHub Issues CLI tool.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="github-issues-cli",
    version="1.0.0",
    author="Devin AI",
    author_email="devin-ai-integration[bot]@users.noreply.github.com",
    description="A CLI tool to list and filter GitHub issues from repositories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itstabya/devin-github-issues-integration",
    packages=find_packages(),
    py_modules=["github_issues_cli"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Bug Tracking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "github-issues-cli=github_issues_cli:list_issues",
        ],
    },
    keywords="github issues cli automation devin",
    project_urls={
        "Bug Reports": "https://github.com/itstabya/devin-github-issues-integration/issues",
        "Source": "https://github.com/itstabya/devin-github-issues-integration",
    },
)
