from setuptools import setup, find_packages

URLS = {
    # TBD
}

setup(
    name="digi",
    version="0.1.0",
    description="dSpace driver library",
    url=URLS,
    author="Silvery Fu",
    author_email="silveryfu@gmail.com",
    license="Apache 2.0",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=[
        "kubernetes",
        "pyyaml",
        "inflection",
        "pyjq",
        "python-box",
    ],
)