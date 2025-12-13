import torch
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
from research_os.config import settings
from research_os.foundation.graph import graph_engine
from loguru import logger
import numpy as np

class ManifoldEngine:
    """
    SOTA Geometric Intelligence.
    Projects high-dimensional research embeddings onto a Hypersphere manifold.
    Uses Apple Metal (MPS) for acceleration.
    """
    def __init__(self):
        # We work on a high-dimensional sphere
        self.dim = 128
        self.manifold = Hypersphere(dim=self.dim)
        
        # Determine device
        self.device = "mps" if settings.USE_MPS and torch.backends.mps.is_available() else "cpu"
        logger.info(f"Manifold Engine Init on {self.device}")

    def project(self, vector: list[float]) -> list[float]:
        """
        Project infinite vector space -> Compact Manifold.
        """
        try:
            # 1. Convert to Tensor
            t_vec = torch.tensor(vector, dtype=torch.float32, device=self.device)
            
            # 2. Dimensionality Reduction (Simple Projection for MVP)
            # In production, this would be a trained GCN autoencoder
            # Here we just slice/pad to fit manifold dim + 1 (embedding space)
            target_dim = self.dim + 1
            if len(vector) > target_dim:
                t_vec = t_vec[:target_dim]
            elif len(vector) < target_dim:
                t_vec = torch.nn.functional.pad(t_vec, (0, target_dim - len(vector)))
            
            # 3. Geomstats Projection (Ensure it lies on the sphere)
            # Switch to numpy/geomstats backend temporarily as Geomstats MPS support is experimental
            np_vec = t_vec.cpu().numpy()
            projected = self.manifold.projection(np_vec)
            
            return projected.tolist()
            
        except Exception as e:
            logger.error(f"Manifold projection failed: {e}")
            return vector # Fail open

    def compute_distance(self, point_a, point_b):
        """Geodesic distance on the manifold (True semantic distance)."""
        return self.manifold.metric.dist(np.array(point_a), np.array(point_b))

manifold_engine = ManifoldEngine()
