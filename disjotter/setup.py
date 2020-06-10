import setuptools
import os
from shutil import copyfile


short_desc = "DisJotter allows the user to interactively create a Docker image from a Jupyter Notebook."

try:
    with open("../README.md", "r") as fh:
        with open("./README.md", "a") as rm:
            text = fh.read()
            rm.write(text)

        long_description = text
except FileNotFoundError:
    long_description = short_desc

try:
    copyfile("../helper_requirements.txt", "./helper_requirements.txt")
    copyfile("../requirements.txt", "./requirements.txt")
except:
    print('copyfile failed.')

setuptools.setup(
    name="DisJotter",
    version="1.0.2",
    author="Wilco Kruijer",
    author_email="wilcokruijer@gmail.com",
    description=short_desc,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WilcoKruijer/DisJotter",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        "docker>=4.2.0",
        "pigar>=0.10.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

try:
    os.remove("./README.md")
    # os.remove("./helper_requirements.txt")
    # os.remove("./requirements.txt")
except:
    print('delete error.')