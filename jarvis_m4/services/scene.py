from typing import Dict, Any
import json

class SceneGenerator:
    """
    Translates Memory Palace data into a Three.js compatible Scene Graph.
    Handles visual aesthetics: colors, scaling, camera positioning.
    """
    
    # Material Palette (Cyberpunk/ResearchOS aesthetic)
    COLORS = [
        0x00ff88, # Neon Green
        0x00d4ff, # Cyan
        0xff0055, # Magenta
        0xffcc00, # Gold
        0x9d00ff, # Purple
        0xff5500  # Orange
    ]
    
    def generate_scene(self, palace_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: Palace dict from MemoryPalace.generate_palace()
        Output: JSON structure for frontend renderer
        """
        scene = {
            "version": "3.0",
            "environment": {
                "skyColor": 0x050510,
                "gridColor": 0x1a1a2e,
                "fogDensity": 0.02
            },
            "nodes": [],
            "labels": []
        }
        
        # Process Clusters (Wings) to assign colors
        wing_colors = {}
        for i, (wing_id, wing_data) in enumerate(palace_data.get("wings", {}).items()):
            color = self.COLORS[i % len(self.COLORS)]
            wing_colors[wing_id] = color
            
            # Add Wing Label
            scene["labels"].append({
                "text": wing_data['label'],
                "position": wing_data['center'],
                "color": color,
                "scale": 10.0
            })
            
            # Process Papers in Wing
            for paper in wing_data['papers']:
                scene["nodes"].append({
                    "id": paper['id'],
                    "type": "paper",
                    "position": paper['position'],
                    "scale": 1.0, # Could map to importance
                    "color": color,
                    "metadata": {
                        "title": paper['title'],
                        "wing": wing_data['label']
                    }
                })
        
        # Process Debris (Unclustered)
        for paper in palace_data.get("debris", []):
            scene["nodes"].append({
                "id": paper['id'],
                "type": "paper_ghost", # Visual style: transparent
                "position": paper['position'],
                "scale": 0.5,
                "color": 0x444455, # Gray
                "metadata": {
                    "title": paper['title'],
                    "wing": "Unclustered"
                }
            })
            
        print(f"🎬 Scene Generated: {len(scene['nodes'])} nodes, {len(scene['labels'])} labels.")
        return scene

    def export_json(self, scene_data: Dict, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(scene_data, f, indent=2)
