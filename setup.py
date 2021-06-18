import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rocketify_sdk",
    version="0.1.0",
    author="Rocketify",
    author_email="admin@rocketcop.io",
    description="Rocketify Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['rocketify_sdk'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=["requests"]
)
