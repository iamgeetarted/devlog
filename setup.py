from setuptools import setup, find_packages

setup(
    name="devlog",
    version="2.3.0",
    packages=find_packages(),
    install_requires=[
        "rich>=12.0",
        "anthropic>=0.20.0",
    ],
    entry_points={
        "console_scripts": [
            "devlog=devlog.cli:main",
        ],
    },
    python_requires=">=3.10",
)
