import setuptools

setuptools.setup(
    name="langchain_forecast",
    version="0.1.0",
    author="Pedro Lima",
    author_email="pedro.lima@gmail.com",
    description="Forecasting tool for langchain AI",
    long_description_content_type="text/markdown",
    url="https://github.com/pvl/langchain_forecast",
    packages=setuptools.find_packages(),
    install_requires=open('requirements.txt').readlines(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)