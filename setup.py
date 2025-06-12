from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="diocesan-persona-builder",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI tool for generating diocesan personas using O*NET data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/diocesan-persona-builder",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "jinja2>=3.1.0",
        "requests>=2.31.0",
        "tenacity>=8.2.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
        "crewai>=0.1.0",
        "pydantic-ai>=0.0.1",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "diocesan-persona-builder=diocesan_persona_builder.cli:cli",
            "dpbuilder=diocesan_persona_builder.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "diocesan_persona_builder": ["../../templates/*.j2"],
    },
)