from setuptools import setup, find_packages

setup(
    name="doc-tpu",
    version="1.0.0",
    description="CLI-генератор отчётных документов ТПУ",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click",
        "python-docx",
        "fpdf2",
        "python-pptx",
        "mistune",
    ],
    entry_points={
        "console_scripts": [
            "doc-tpu=doc_tpu.cli:main",
        ],
    },
)
