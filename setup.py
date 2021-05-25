from setuptools import setup, find_packages

setup(
    name='rpviz',
    version='0.1.1',
    description='Visualize pathways from the RetroPath Suite.',
    license='MIT',
    author='Thomas Duigou, Melchior du Lac',
    author_email='thomas.duigou@inrae.fr',
    packages=find_packages(),
    include_package_data=True,
    keywords=['rpviz'],
    url='https://github.com/brsynth/rpviz',
    classifiers=[
        'Topic :: Scientific/Engineering',
    ]
)