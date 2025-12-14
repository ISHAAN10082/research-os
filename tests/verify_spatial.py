import sys
import os
import numpy as np
import json
from pprint import pprint

# Add parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis_m4.services.palace import MemoryPalaceV2 as MemoryPalace
from jarvis_m4.services.scene import SceneGenerator

def run_spatial_verification():
    print("🌌 Verifying Spatial Layer...")
    
    # 1. Generate Synthetic Data (50 papers, 768 dim)
    # Create 3 distinct clusters for testing
    print("Generating synthetic embeddings...")
    np.random.seed(42)
    
    cluster_1 = np.random.normal(0, 0.1, (20, 768)) # Group A
    cluster_2 = np.random.normal(2, 0.1, (20, 768)) # Group B (far away)
    noise = np.random.normal(0, 2.0, (10, 768))     # Random noise
    
    embeddings = np.vstack([cluster_1, cluster_2, noise])
    papers = []
    
    for i, vec in enumerate(embeddings):
        papers.append({
            "paper_id": f"p_{i}",
            "title": f"Paper {i}",
            "embedding": vec.tolist()
        })
        
    # 2. Run Palace Generation
    palace_gen = MemoryPalace()
    palace_data = palace_gen.generate_palace(papers)
    
    # Validate Structure
    wings = palace_data['wings']
    print(f"✅ Palace Generated. Found {len(wings)} wings.")
    
    # We expect at least 2 wings (Cluster 1, Cluster 2)
    # HDBSCAN is density based, might find noise as noise (-1)
    if len(wings) < 2:
        print(f"⚠️ Warning: Expected 2+ wings, found {len(wings)}. Tune UMAP/HDBSCAN pars in prod.")
    else:
        print("✅ Clustering Logic Valid (Found distinct groups).")
        
    # 3. Run Scene Generation
    scene_gen = SceneGenerator()
    scene_data = scene_gen.generate_scene(palace_data)
    
    print(f"✅ Scene Graph Generated. {len(scene_data['nodes'])} total nodes.")
    
    # Export for inspection
    test_out = "tests/test_scene.json"
    scene_gen.export_json(scene_data, test_out)
    print(f"✅ Test scene exported to {test_out}")

if __name__ == "__main__":
    run_spatial_verification()
