from setuptools import setup, find_packages

setup(
    name='rpviz',
    version='0.1.0',
    description='Visualize pathways from the RetroPath Suite.',
    license='MIT',
    author='Thomas Duigou, Melchior du Lac',
    author_email='thomas.duigou@inrae.fr',
    packages=find_packages(),
    keywords=['rpviz'],
    url='https://github.com/brsynth/rpviz',
    classifiers=[
        'Topic :: Scientific/Engineering',
    ]
)