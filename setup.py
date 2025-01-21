from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="pyRetroTerm",
    version="0.1.4",
    author="Scott Peterman",
    author_email="scottpeterman@gmail.com",
    description="pyRetroTerm - A PyQt6 Tabbed Terminal Emulator with Retro themes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scottpeterman/pyretroterm",
    project_urls={

    },
    keywords="terminal, ssh, network, automation, pyqt6",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'pyretroterm': [
            'static/**/*',
            'templates/**/*',
            'templates.db'
        ]
    },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
entry_points={
        'console_scripts': [
            'pyretroterm-con=pyretroterm.pyretroterm:main',
        ],
        'gui_scripts': [
            'pyretroterm=pyretroterm.pyretroterm:main',
        ],
    },
    python_requires=">=3.8",
)