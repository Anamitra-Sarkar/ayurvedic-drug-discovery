"""
Vina Wrapper — Real Binary Detection, Config Generation, Output Parsing
Backend: backend/app/core/docking/vina_wrapper.py

Implements:
- detection of AutoDock Vina binary (1.2.x compatible)
- config generation (.txt conf)
- subprocess execution with timeout
- PDBQT parsing, affinity extraction
- fallback mock mode signaling

Notes:
- AutoDock Vina expects receptor.pdbqt and ligand.pdbqt.
- For mock environments without Vina, caller should use DockingAgent.mock_scoring.

PDBBind-style evaluation: wrapper logs RMSD-relevant metadata and captures
best pose metrics.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Regex patterns to parse Vina stdout / log
VINA_AFFINITY_PATTERN = re.compile(
    r"^\s*(\d+)\s+([-\d\.]+)\s+[\d\.]+\s+[\d\.]+", re.MULTILINE
)
VINA_MODE_LINE = re.compile(r"mode \|   affinity")

@dataclass
class VinaConfig:
    """
    Configuration for a single Vina docking run.

    Coordinates define the search space box.
    See AutoDock Vina manual for details.

    Example box for ~24 Å cubic region centered on binding site.
    """
    receptor_pdbqt: str  # path to receptor.pdbqt
    ligand_pdbqt: str    # path to ligand.pdbqt

    center_x: float
    center_y: float
    center_z: float

    size_x: float = 24.0
    size_y: float = 24.0
    size_z: float = 24.0

    exhaustiveness: int = 16  # 8 default; 16 for more thorough search; 32 for benchmarking
    num_modes: int = 9
    energy_range: float = 3.0
    cpu: int = 2
    seed: Optional[int] = None

    # Output
    out_pdbqt: Optional[str] = None  # If None, temp file
    log_file: Optional[str] = None

    def to_config_text(self) -> str:
        lines = [
            f"receptor = {self.receptor_pdbqt}",
            f"ligand = {self.ligand_pdbqt}",
            f"center_x = {self.center_x}",
            f"center_y = {self.center_y}",
            f"center_z = {self.center_z}",
            f"size_x = {self.size_x}",
            f"size_y = {self.size_y}",
            f"size_z = {self.size_z}",
            f"exhaustiveness = {self.exhaustiveness}",
            f"num_modes = {self.num_modes}",
            f"energy_range = {self.energy_range}",
            f"cpu = {self.cpu}",
        ]
        if self.out_pdbqt:
            lines.append(f"out = {self.out_pdbqt}")
        if self.seed is not None:
            lines.append(f"seed = {self.seed}")
        return "\n".join(lines) + "\n"

    def write(self, path: str) -> None:
        Path(path).write_text(self.to_config_text())
        logger.info(f"Wrote Vina config to {path}")

    @classmethod
    def from_binding_site(
        cls,
        receptor_pdbqt: str,
        ligand_pdbqt: str,
        binding_site: Dict[str, float],
        **overrides
    ) -> "VinaConfig":
        """
        Create config from binding site dict with center_x,y,z and optional sizes.
        binding_site example: {"center_x": 12.3, "center_y": -5.1, "center_z": 18.7, "size": 25}
        """
        size = binding_site.get("size", 24.0)
        return cls(
            receptor_pdbqt=receptor_pdbqt,
            ligand_pdbqt=ligand_pdbqt,
            center_x=binding_site["center_x"],
            center_y=binding_site["center_y"],
            center_z=binding_site["center_z"],
            size_x=binding_site.get("size_x", size),
            size_y=binding_site.get("size_y", size),
            size_z=binding_site.get("size_z", size),
            **overrides
        )

@dataclass
class VinaPose:
    mode: int
    affinity_kcal_mol: float
    rmsd_lb: float
    rmsd_ub: float
    pdbqt_block: str = ""
    confidence: float = 0.0  # derived metric

@dataclass
class VinaResult:
    success: bool
    best_affinity: Optional[float]
    poses: List[VinaPose] = field(default_factory=list)
    raw_log: str = ""
    out_pdbqt_path: Optional[str] = None
    duration_sec: float = 0.0
    vina_version: Optional[str] = None
    mock_used: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "best_affinity_kcal_mol": self.best_affinity,
            "poses": [
                {
                    "mode": p.mode,
                    "affinity": p.affinity_kcal_mol,
                    "rmsd_lb": p.rmsd_lb,
                    "rmsd_ub": p.rmsd_ub,
                    "confidence": p.confidence
                } for p in self.poses
            ],
            "num_modes": len(self.poses),
            "vina_version": self.vina_version,
            "mock_used": self.mock_used,
            "duration_sec": self.duration_sec,
            "error": self.error,
            # PDBBind-style note
            "pdbbind_note": "Vina score is empirical; correlation to experimental Kd ~0.5-0.6 R. "
                            "For evaluation: RMSD <2A success, >70% top pose success on PDBbind Core Set."
        }

class VinaBinaryDetector:
    """
    Robust detection of Vina binary.
    Checks PATH, common conda locations, and user-supplied path.
    """

    CANDIDATE_BIN_NAMES = ["vina", "vina_1.2.5", "vina_1.2.3", "autodock_vina"]

    @staticmethod
    def find_binary(custom_path: Optional[str] = None) -> Optional[str]:
        if custom_path and os.path.exists(custom_path) and os.access(custom_path, os.X_OK):
            return custom_path

        for name in VinaBinaryDetector.CANDIDATE_BIN_NAMES:
            found = shutil.which(name)
            if found:
                logger.info(f"Found Vina binary: {found}")
                return found

        # Common conda / pip locations
        common_paths = [
            os.path.expanduser("~/.conda/envs/*/bin/vina"),
            "/opt/anaconda3/bin/vina",
            "/usr/local/bin/vina",
            "/usr/bin/vina",
        ]
        import glob
        for pattern in common_paths:
            matches = glob.glob(pattern)
            for m in matches:
                if os.access(m, os.X_OK):
                    return m
        return None

    @staticmethod
    def get_version(binary_path: str) -> Optional[str]:
        try:
            result = subprocess.run(
                [binary_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            out = result.stdout + result.stderr
            # examples: "AutoDock Vina 1.2.5"
            match = re.search(r"Vina\s+([\d\.]+)", out)
            return match.group(1) if match else out.strip()[:50]
        except Exception as e:
            logger.debug(f"Could not get Vina version: {e}")
            return None


class VinaWrapper:
    """
    High-level wrapper that encapsulates binary detection,
    config writing, execution, and parsing.
    """

    def __init__(self, vina_binary: Optional[str] = None, default_cpu: int = 2):
        self.vina_binary = vina_binary or VinaBinaryDetector.find_binary()
        self.default_cpu = default_cpu
        self.available = self.vina_binary is not None
        if self.available:
            self.version = VinaBinaryDetector.get_version(self.vina_binary)
            logger.info(f"VinaWrapper initialized: {self.vina_binary} version={self.version}")
        else:
            self.version = None
            logger.warning("Vina binary NOT found. Wrapper will run in mock mode; docking_agent must use empirical scoring.")

    def is_available(self) -> bool:
        return self.available

    def run(
        self,
        config: VinaConfig,
        timeout_sec: int = 300
    ) -> VinaResult:
        """
        Execute Vina docking.

        Returns VinaResult. If binary not available, returns success=False with mock_used=False
        and caller should trigger mock scoring in DockingAgent.

        This method is deliberately blocking; DockingAgent may wrap in ProcessPool for batch.
        """
        import time
        start = time.time()

        if not self.available:
            return VinaResult(
                success=False,
                best_affinity=None,
                raw_log="Vina binary not found",
                mock_used=True,
                error="VINA_BINARY_NOT_FOUND",
                vina_version=None
            )

        # Ensure out file exists
        if not config.out_pdbqt:
            tmp_dir = tempfile.mkdtemp(prefix="vina_")
            config.out_pdbqt = os.path.join(tmp_dir, "out.pdbqt")

        # Write temp config file
        config_file = None
        try:
            fd, config_file = tempfile.mkstemp(prefix="vina_conf_", suffix=".txt")
            os.close(fd)
            config.write(config_file)

            # Build command: vina --config conf.txt --log log.txt
            log_file = config.log_file or config_file.replace(".txt", ".log")
            cmd = [
                self.vina_binary,
                "--config", config_file,
                "--log", log_file
            ]

            logger.info(f"Running Vina: {' '.join(cmd)}")
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )

            raw_log = proc.stdout + "\n" + proc.stderr
            # Also read log_file if exists
            if os.path.exists(log_file):
                raw_log += "\n" + Path(log_file).read_text()

            # Parse poses
            poses = self._parse_log(raw_log)

            # Also parse out PDBQT if present to extract pose blocks (optional)
            out_blocks = []
            if config.out_pdbqt and os.path.exists(config.out_pdbqt):
                out_blocks = self._split_pdbqt_models(Path(config.out_pdbqt).read_text())

            # Merge blocks into poses if lengths match
            for i, pose in enumerate(poses):
                if i < len(out_blocks):
                    pose.pdbqt_block = out_blocks[i]
                # Confidence heuristic: lower (more negative) affinity + low RMSD => higher confidence
                # Map affinity -12 to -4 => confidence 0.95 to 0.35
                aff = pose.affinity_kcal_mol
                base_conf = max(0.1, min(0.98, ( -aff - 2 ) / 12 ))  # rough
                rmsd_penalty = (pose.rmsd_lb + pose.rmsd_ub) / 20.0
                pose.confidence = max(0.05, min(0.99, base_conf - rmsd_penalty))

            best = min((p.affinity_kcal_mol for p in poses), default=None) if poses else None
            success = len(poses) > 0 and proc.returncode == 0
            duration = time.time() - start

            return VinaResult(
                success=success,
                best_affinity=best,
                poses=poses,
                raw_log=raw_log[:10000],  # cap
                out_pdbqt_path=config.out_pdbqt,
                duration_sec=duration,
                vina_version=self.version,
                mock_used=False,
                error=None if success else f"Vina exit code {proc.returncode}: {raw_log[-500:]}"
            )

        except subprocess.TimeoutExpired as te:
            duration = time.time() - start
            logger.error(f"Vina timed out after {timeout_sec}s")
            return VinaResult(
                success=False,
                best_affinity=None,
                raw_log=te.stdout.decode() if te.stdout else "" if isinstance(te.stdout, bytes) else str(te.stdout or ""),
                duration_sec=duration,
                vina_version=self.version,
                mock_used=False,
                error=f"TIMEOUT after {timeout_sec}s"
            )
        except Exception as e:
            duration = time.time() - start
            logger.exception("Vina execution failed")
            return VinaResult(
                success=False,
                best_affinity=None,
                raw_log=str(e),
                duration_sec=duration,
                vina_version=self.version,
                mock_used=False,
                error=str(e)
            )
        finally:
            # Cleanup config file (keep out pdbqt for caller)
            if config_file and os.path.exists(config_file):
                try:
                    os.remove(config_file)
                except Exception:
                    pass

    @staticmethod
    def _parse_log(log_text: str) -> List[VinaPose]:
        """
        Parse Vina log table:
        mode |   affinity | dist from best mode
             | (kcal/mol) | rmsd l.b.| rmsd u.b.
        -----+------------+----------+----------
        1         -8.2      0.000      0.000
        2         -7.9      1.235      2.341
        ...
        """
        poses: List[VinaPose] = []
        in_table = False
        for line in log_text.splitlines():
            if "affinity" in line and "rmsd" in line:
                in_table = True
                continue
            if in_table:
                # delimiter line
                if "-----" in line:
                    continue
                # stop when empty or non numeric
                m = re.match(r"\s*(\d+)\s+([-\d\.]+)\s+([\d\.]+)\s+([\d\.]+)", line)
                if m:
                    mode = int(m.group(1))
                    aff = float(m.group(2))
                    lb = float(m.group(3))
                    ub = float(m.group(4))
                    poses.append(VinaPose(mode=mode, affinity_kcal_mol=aff, rmsd_lb=lb, rmsd_ub=ub))
                else:
                    # If we already got some and line is empty/not matching, break
                    if poses and line.strip() == "":
                        continue
                    # Heuristic stop: if line not parseable and we have poses, break after a couple failures?
                    pass
        # Fallback: try secondary pattern (single mode logs)
        if not poses:
            for m in VINA_AFFINITY_PATTERN.finditer(log_text):
                try:
                    mode = int(m.group(1))
                    aff = float(m.group(2))
                    # We don't have rmsd in this fallback regex; approximate
                    poses.append(VinaPose(mode=mode, affinity_kcal_mol=aff, rmsd_lb=0.0, rmsd_ub=0.0))
                except Exception:
                    continue
        return poses

    @staticmethod
    def _split_pdbqt_models(pdbqt_text: str) -> List[str]:
        """
        Split multi-MODEL PDBQT file into individual blocks.
        Vina outputs MODEL 1 ... ENDMDL
        Returns list of strings.
        """
        blocks = []
        current = []
        inside = False
        for line in pdbqt_text.splitlines():
            if line.startswith("MODEL"):
                inside = True
                current = [line]
            elif line.startswith("ENDMDL"):
                current.append(line)
                blocks.append("\n".join(current))
                inside = False
                current = []
            elif inside:
                current.append(line)
        if not blocks and pdbqt_text.strip():
            # Single model without MODEL tag
            blocks = [pdbqt_text]
        return blocks

    @staticmethod
    def generate_box_from_pdb(pdb_path: str, padding: float = 6.0) -> Dict[str, float]:
        """
        Estimate binding box from PDB by finding centroid of heteroatoms or whole protein
        if ligand absent. This is a crude fallback for when binding site unknown;
        real pipeline should use Fpocket / co-crystallized ligand centroid.

        Returns dict with center_x,y,z,size_x,y,z
        """
        try:
            xs, ys, zs = [], [], []
            with open(pdb_path) as f:
                for line in f:
                    if line.startswith("ATOM") or line.startswith("HETATM"):
                        try:
                            x = float(line[30:38])
                            y = float(line[38:46])
                            z = float(line[46:54])
                            xs.append(x); ys.append(y); zs.append(z)
                        except Exception:
                            continue
            if not xs:
                raise ValueError("No coordinates found in PDB")

            cx = sum(xs)/len(xs)
            cy = sum(ys)/len(ys)
            cz = sum(zs)/len(zs)
            # size from spread
            sx = max(max(xs)-min(xs)+padding, 20.0)
            sy = max(max(ys)-min(ys)+padding, 20.0)
            sz = max(max(zs)-min(zs)+padding, 20.0)
            # cap at 30 to avoid huge box
            sx = min(sx, 30.0); sy = min(sy, 30.0); sz = min(sz, 30.0)

            return {
                "center_x": cx,
                "center_y": cy,
                "center_z": cz,
                "size_x": sx,
                "size_y": sy,
                "size_z": sz,
                "size": max(sx, sy, sz)
            }
        except Exception as e:
            logger.warning(f"Box generation fallback due to {e}; using origin box")
            return {
                "center_x": 0.0, "center_y": 0.0, "center_z": 0.0,
                "size_x": 24.0, "size_y": 24.0, "size_z": 24.0,
                "size": 24.0
            }
