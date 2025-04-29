from setuptools import setup, find_packages

# Read dependencies from pyproject.toml
# This is a fallback setup.py for systems that don't fully support pyproject.toml

setup(
    name="linkedin-scraper",
    version="0.1.0",
    description="LinkedIn Scraper - Extract structured business information from LinkedIn",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "beautifulsoup4>=4.13.4",
        "email-validator>=2.2.0",
        "flask>=3.1.0",
        "flask-sqlalchemy>=3.1.1",
        "gunicorn>=23.0.0",
        "pip-tools>=7.4.1",
        "psycopg2-binary>=2.9.10",
        "requests>=2.32.3",
        "trafilatura>=2.0.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)