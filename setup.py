# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="pyRetroTerm",
    version="0.2.1",
    author="Scott Peterman",
    author_email="scottpeterman@gmail.com",
    description="pyRetroTerm - A PyQt6 Terminal Emulator with Real-time Telemetry and Retro Themes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scottpeterman/pyretroterm",
    project_urls={},
    keywords="terminal, ssh, network, automation, telemetry, monitoring, pyqt6",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'pyretroterm': [
            'static/**/*',
            'templates/**/*',
            'templates.db'
        ],
        'termtel': [
            'frontend/**/*',
            'frontend/assets/**/*',
            'backend/**/*',
            'backend/output_debug/**/*'
        ]
    },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Terminals :: Terminal Emulators/X Terminals",
    ],
    entry_points={
        'console_scripts': [
            'pyretroterm-con=pyretroterm.pyretroterm:main',
        ],
        'gui_scripts': [
            'pyretroterm=pyretroterm.pyretroterm:main',
            'termtel=termtel.backend.launcher:main',
        ],
    },
    python_requires=">=3.9",
)
