import setuptools
from distutils.core import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='agda_kernel',
    version='0.62',
    #packages=['src/agda_kernel'],
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    description='A rudimentary Jupyter kernel for Agda',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='Lorenzo Clemente',
    author_email='clementelorenzo@gmail.com',
    url='https://github.com/lclem/agda-kernel',
    #install_requires=['jupyter_client', 'IPython', 'ipykernel'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ]
)
