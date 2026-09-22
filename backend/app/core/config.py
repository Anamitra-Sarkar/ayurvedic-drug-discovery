"""
Central Config for Ayurvedic Pipeline
"""
import os
from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
REPORT_DIR = DATA_DIR / "reports"
FAISS_INDEX_DIR = Path(__file__).parent / "rag" / "faiss_index"

@dataclass
class PipelineConfig:
    target_plant: str = "Withania somnifera"
    target_protein: str = "6LU7"
    embedding_model: str = "all-MiniLM-L6-v2"
    docking_center: tuple = (-10.7, 12.4, 68.1)
    docking_box: tuple = (20, 20, 20)
    ml_model_path: str = str(DATA_DIR / "ml_model.pkl")
    checkpoint_dir: str = str(CHECKPOINT_DIR)
    report_dir: str = str(REPORT_DIR)
    faiss_index_dir: str = str(FAISS_INDEX_DIR)
    enable_parallel: bool = True

    @classmethod
    def from_env(cls):
        return cls(
            target_plant=os.getenv("TARGET_PLANT", "Withania somnifera"),
            target_protein=os.getenv("TARGET_PROTEIN", "6LU7"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )

config = PipelineConfig.from_env()
