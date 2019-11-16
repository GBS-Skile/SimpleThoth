from setuptools import setup, find_packages

setup(
    name='simplethoth',
    version='0.1.5',
    author='Jeongmin Lee (Skile)',
    author_email='imleejm@gmail.com',
    packages=find_packages(),
    url='https://github.com/GBS-Skile/SimpleThoth',
    python_requires='>=3',
    install_requires=['flask'],
)