from setuptools import setup, find_packages
from typing import List

def get_requirements() -> List[str]:
    """ This function will return a list of requirements"""

    requirement_lst:List[str] = []

    try:
        with open('requirements.txt') as f:
            lines = f.readlines()
            for line in lines:
                requirement = line.strip()
                # ignore empty lines and -e .
                if requirement and requirement != '-e .':
                    requirement_lst.append(requirement)
    except FileNotFoundError:
        print("requirements.txt file not found. Please make sure it exists in the same directory as setup.py")

    return requirement_lst

setup(
    name='network-security',
    version='0.1.0',
    packages=find_packages(),
    install_requires=get_requirements(),
    author="Sam Villa-Smith, PhD"
)
