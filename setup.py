# coding: utf-8
from setuptools import setup, find_packages
from os import path as os_path

## INFOS ##
package = "rpviz"
descr = "Visualize pathways from the RetroPath Suite"
url = "https://github.com/brsynth/rpViz"
authors = "Joan Hérisson, Melchior du Lac, Thomas Duigou"
corr_author = "joan.herisson@univ-evry.fr"

## LONG DESCRIPTION
with open(
    os_path.join(os_path.dirname(os_path.realpath(__file__)), "README.md"),
    "r",
    encoding="utf-8",
) as f:
    long_description = f.read()


def get_version():
    with open(
        os_path.join(
            os_path.dirname(os_path.realpath(__file__)), package, "_version.py"
        ),
        "r",
    ) as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith("__version__"):
            from re import search

            m = search(r'"(.+)"', line)
            if m:
                return m.group(1)


setup(
    name=package,
    version=get_version(),
    author=authors,
    author_email=corr_author,
    description=descr,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=url,
    packages=find_packages(),
    package_dir={package: package},
    package_data={
        package: [
            "data/*",
            "templates/*.html",
            "templates/css/*",
            "templates/js/*",
        ]
    },
    include_package_data=True,
    test_suite="pytest",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
