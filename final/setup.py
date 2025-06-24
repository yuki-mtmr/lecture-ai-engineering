from setuptools import setup, find_packages

setup(
    name="lecture-slide-copilot",
    version="0.1.0",
    description="講義スライド作成をサポートするCopilot",
    author="Matsuo Lab",
    packages=find_packages(),
    install_requires=[
        "google-generativeai>=0.3.0",
        "python-pptx>=0.6.21",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.8.0",
        "pydantic>=2.5.0",
        "aiohttp>=3.9.0",
        "pillow>=10.0.0"
    ],
    entry_points={
        'console_scripts': [
            'slide-copilot=src.cli:cli',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)