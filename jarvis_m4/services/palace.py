"""Fixed palace.py - Uses MPNet instead of SPECTER2"""


import numpy as np
from typing import List, Dict

class MemoryPalaceV2:
    def __init__(self, schema=None):
        # Use cached model (FastEmbed via ModelCache)
        from research_os.foundation.model_cache import get_mpnet
        self.embedder = get_mpnet()
        print("✅ Using cached Embedder (FastEmbed) for Memory Palace")
        
        self.schema = schema
    
    def generate_palace(self, papers: List[Dict]) -> Dict:
        """Generate memory palace"""
        if not papers:
            return {"wings": {}, "debris": []}
        
        print(f"🏰 Generating Memory Palace from {len(papers)} papers...")
        
        # Get embeddings
        texts = [p.get('title', '') + ' ' + p.get('abstract', '')[:500] for p in papers]
        embeddings = self.embedder.encode(texts, show_progress_bar=False)
        
        # Reduce to 3D using PCA (simple and reliable)
        from sklearn.decomposition import PCA
        pca = PCA(n_components=3, random_state=42)
        coords_3d = pca.fit_transform(embeddings)
        
        # Simple clustering by position
        clusters = self._simple_cluster(coords_3d)
        
        # Build palace
        palace = {"wings": {}, "debris": []}
        
        for cluster_id, indices in clusters.items():
            wing_papers = []
            for i in indices:
                paper = papers[i].copy()
                paper['position'] = {
                    'x': float(coords_3d[i, 0]),
                    'y': float(coords_3d[i, 1]),
                    'z': float(coords_3d[i, 2])
                }
                wing_papers.append(paper)
            
            palace["wings"][f"Wing {cluster_id}"] = wing_papers
        
        print(f"✅ Palace generated: {len(palace['wings'])} wings")
        return palace
    
    def _simple_cluster(self, coords_3d: np.ndarray) -> Dict:
        """Simple clustering by x-coordinate"""
        clusters = {0: [], 1: [], 2: []}
        x_coords = coords_3d[:, 0]
        
        for i, x in enumerate(x_coords):
            if x < np.percentile(x_coords, 33):
                clusters[0].append(i)
            elif x < np.percentile(x_coords, 67):
                clusters[1].append(i)
            else:
                clusters[2].append(i)
        
        return clusters

def test():
    print("Testing palace...")
    p = MemoryPalaceV2()
    test_papers = [
        {"paper_id": "1", "title": "Test 1", "abstract": "Abstract 1"},
        {"paper_id": "2", "title": "Test 2", "abstract": "Abstract 2"},
        {"paper_id": "3", "title": "Test 3", "abstract": "Abstract 3"}
    ]
    palace = p.generate_palace(test_papers)
    print(f"✅ Generated {len(palace['wings'])} wings")
    return True

if __name__ == "__main__":
    test()
