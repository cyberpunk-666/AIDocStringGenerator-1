from setuptools import setup, find_packages

setup(
    name='AIDocStringGenerator',
    version='1.0',
    packages=find_packages(),
    description='AIDocStringGenerator is an automated tool that utilizes AI technologies like Anthropic and OpenAI GPT-3.5 to generate and manage docstrings in Python code. It streamlines documentation by processing both single files and entire directories, offering customizable settings for docstring verbosity and style. This tool is ideal for enhancing code readability and maintainability in Python projects.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Francois Girard',
    author_email='fantasiiio@hotmail.com',
    url='https://github.com/fantasiiio/AIDocStringGenerator',
    entry_points={
        'console_scripts': [
            'AIDocstringGenerator = AIDocstringGenerator:main',
        ],
    },    
)