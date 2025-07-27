from setuptools import setup, find_packages

setup(
    name='apkpurecrawler',
    version='1.0.0',
    description='Python crawler for APKPure that downloads APK/XAPK files and extracts detailed metadata into MongoDB',
    author='MD Shafiqul Islam',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'pymongo',
    ],
    entry_points={
        'console_scripts': [
            'apkpure-crawl=scripts.apkpure_crawl',
        ],
    },
    include_package_data=True,
    python_requires='>=3.6',
)

