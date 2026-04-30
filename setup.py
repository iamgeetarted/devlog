from setuptools import setup, find_packages

setup(
    name="devlog",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "devlog=devlog.cli:main",
        ],
    },
    python_requires=">=3.10",
)
