"""Strict OpenMC preflight and result-parsing boundary.

No OpenMC model is shipped because the supplied materials do not specify one.
The functions here refuse to turn a categorical loading into material cards or
geometry without a documented benchmark mapping.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
import json,os,re,shutil
from pathlib import Path
from typing import Any
from .qubo import Candidate,CandidateMappingError,QuboModel

@dataclass(frozen=True)
class OpenMCPreflight:
    status:str
    executable:str|None
    cross_sections:str|None
    missing_files:tuple[str,...]
    reasons:tuple[str,...]
    @property
    def runnable(self)->bool: return self.status=="ready"
    def to_dict(self)->dict[str,Any]: return asdict(self)

class OpenMCIntegrationError(RuntimeError): pass

def preflight_openmc(model_directory:str|Path)->OpenMCPreflight:
    model_directory=Path(model_directory); executable=shutil.which("openmc"); cross_sections=os.environ.get("OPENMC_CROSS_SECTIONS")
    required_files=("materials.xml","geometry.xml","settings.xml")
    missing_files=tuple(filename for filename in required_files if not (model_directory/filename).is_file())
    reasons=[]
    if executable is None: reasons.append("OpenMC executable is not on PATH")
    if not cross_sections: reasons.append("OPENMC_CROSS_SECTIONS is unset")
    elif not Path(cross_sections).is_file(): reasons.append("OPENMC_CROSS_SECTIONS does not name a readable XML file")
    if missing_files: reasons.append("required model XML is absent")
    return OpenMCPreflight(status="ready" if not reasons else "blocked",executable=executable,cross_sections=cross_sections,missing_files=missing_files,reasons=tuple(reasons))

def candidate_loading_manifest(model:QuboModel,candidate:Candidate)->dict[str,Any]:
    try: loading=model.decode(candidate.vector)
    except CandidateMappingError as exc: return {"candidate_id":candidate.candidate_id,"status":"rejected","reason":str(exc)}
    return {"candidate_id":candidate.candidate_id,"status":"accepted_for_benchmark_mapping","loading_labels":loading,"not_an_openmc_input":True,"required_before_simulation":["documented benchmark geometry and materials","burnup-label to material/temperature/composition mapping","cross-section library provenance","eigenvalue settings and tallies","physical metric limits and independent reference procedure"]}

def write_candidate_manifest(model:QuboModel,candidate:Candidate,path:str|Path)->dict[str,Any]:
    manifest=candidate_loading_manifest(model,candidate); Path(path).write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return manifest

_KEFF_PATTERN=re.compile(r"Combined k-effective\\s*=\\s*([+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[Ee][+-]?\\d+)?)\\s*\\+/-\\s*([+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[Ee][+-]?\\d+)?)")

def parse_openmc_stdout_keff(text:str)->tuple[float,float]:
    match=_KEFF_PATTERN.search(text)
    if match is None: raise OpenMCIntegrationError("no 'Combined k-effective = mean +/- std' line found")
    return float(match.group(1)),float(match.group(2))

def parse_openmc_statepoint(path:str|Path)->dict[str,Any]:
    statepoint=Path(path)
    if not statepoint.is_file(): raise OpenMCIntegrationError(f"statepoint file does not exist: {statepoint}")
    try: import h5py
    except ImportError as exc: raise OpenMCIntegrationError("h5py is required to parse an OpenMC statepoint") from exc
    with h5py.File(statepoint,"r") as handle:
        if "k_combined" not in handle: raise OpenMCIntegrationError("statepoint lacks documented k_combined dataset")
        keff=handle["k_combined"][()]
        if len(keff)!=2: raise OpenMCIntegrationError("k_combined does not contain mean and standard deviation")
        result={"keff_mean":float(keff[0]),"keff_standard_deviation":float(keff[1])}
        for key in ("n_particles","n_batches","n_inactive","generations_per_batch"):
            if key in handle: result[key]=int(handle[key][()])
        if "openmc_version" in handle: result["openmc_version"]=[int(value) for value in handle["openmc_version"][()]]
        return result
