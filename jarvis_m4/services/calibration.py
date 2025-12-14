import numpy as np
from typing import Dict, List, Tuple
import os
import json
from sklearn.isotonic import IsotonicRegression

class CalibrationLayer:
    """
    Calibrates raw LLM/system confidence scores into true probabilities.
    Addresses the '42% F1' problem by quantifying uncertainty accurately.
    Uses Isotonic Regression trained on validation data (SciFact-Open or internal).
    """
    
    def __init__(self, model_path: str = "data/calibration_model.json"):
        self.model_path = model_path
        self.calibrator = None
        self.is_fitted = False
        self._load_model()
        
    def _load_model(self):
        """Load fitted calibration model if exists"""
        if os.path.exists(self.model_path):
            try:
                # Simple serialization for IsotonicRegression (it's just X_thresholds/y_values)
                # But sklearn models pickle best. For robustness/security, we might just store arrays.
                # For now, we assume we need to fit it or use a default linear mapping.
                pass
            except Exception as e:
                print(f"Failed to load calibration model: {e}")
                
    def train(self, raw_confidences: List[float], true_labels: List[int]):
        """
        Train calibrator on validation data.
        raw_confidences: list of 0.0-1.0 scores from system
        true_labels: 0 (incorrect/refuted) or 1 (correct/supported)
        """
        self.calibrator = IsotonicRegression(out_of_bounds='clip')
        self.calibrator.fit(raw_confidences, true_labels)
        self.is_fitted = True
        self._save_model()
        
    def _save_model(self):
        # Placeholder for persistence
        pass
        
    def calibrate(self, raw_confidence: float) -> Tuple[float, str]:
        """
        Returns (calibrated_probability, description)
        Example: (0.42, "Low Confidence")
        """
        if not self.is_fitted:
            # Fallback: Just return raw if not trained
            # Or use a conservative heuristic (e.g. dampen extremes)
            calibrated = raw_confidence * 0.9 # Conservative dampening
        else:
            calibrated = self.calibrator.predict([raw_confidence])[0]
            
        # Interpretation
        if calibrated < 0.3:
            desc = "Uncertain / Likely Noise"
        elif calibrated < 0.6:
            desc = "Weak Evidence"
        elif calibrated < 0.85:
            desc = "Moderate Confidence"
        else:
            desc = "High Confidence"
            
        return float(calibrated), desc

    def get_expected_precision(self, calibrated_score: float) -> str:
        """Return formatted expected precision string for UI"""
        return f"{calibrated_score*100:.1f}%"
