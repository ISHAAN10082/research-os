from setuptools import setup, find_packages

setup(
    name="research_os",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
        "loguru>=0.7",
        "pymupdf>=1.23",
        "kuzu>=0.4",
        "mlx>=0.5",
        "mlx-lm>=0.10",
        "groq>=0.5",
        "rank-bm25>=0.2",
        "FlagEmbedding>=1.2",
        "sentence-transformers>=2.2",
    ],
    python_requires=">=3.10",
)
