from setuptools import setup, find_packages

setup(
    name="research_os_v2",
    version="3.0.0",
    description="ResearchOS 3.0 V2 (M4 Optimized)",
    packages=find_packages(),
    install_requires=[
        # Core V2 Logic
        "outlines>=0.0.1",
        "mlx>=0.5",
        "mlx-lm>=0.10",
        "sentence-transformers>=2.2",
        "kuzu>=0.4",
        "networkx>=3.0",
        
        # Web UI
        "fastapi",
        "uvicorn",
        "python-multipart",
        
        # Data & Utils
        "pydantic>=2.0",
        "faiss-cpu",
        "scikit-learn",
        "numpy",
        "scipy",
        "loguru",
        
        # Optional / Legacy support included for compatibility
        "chromadb",
        "langgraph",
        "langchain" 
    ],
    python_requires=">=3.10",
)
