# setup.py

from setuptools import setup, find_packages

setup(
    name="XlementFitting",
    version="4.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=2.0.4",
        "matplotlib>=3.7.1",
        "scipy>=1.10.0"
    ],
    author="陈铭潜",
    author_email="chenbmehust@hust.edu.cn",
    description="量准公司独家开发的分子互作拟合包, 未经许可不得使用",
    url="https://www.liangzhunglobal.com/",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)