import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="officeworld",
    version="0.1.0",
    author="Joshua Evans",
    author_email="jbe25@bath.ac.uk",
    description="A highly-customisable, procedurally-generated 'office building' environment for reinforcement learning. Essentally, gridworlds on steroids.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ueva/OffcieWorld",
    packages=setuptools.find_packages(exclude=("example", "test")),
    install_requires=["numpy", "pygame", "networkx"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Natural Language :: English",
    ],
)
