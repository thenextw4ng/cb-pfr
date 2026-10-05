"""Usmanov-style categorical loading constraints and an exact QUBO expansion."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations, product
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

BURNUP_LABELS = ("fresh", "once_burned", "twice_burned")
FRESH, ONCE_BURNED, TWICE_BURNED = range(3)

class ModelSpecificationError(ValueError): pass
class CandidateMappingError(ValueError): pass

@dataclass(frozen=True)
class CoreSpec:
    name: str
    positions: tuple[str, ...]
    boundary: frozenset[str]
    inner: frozenset[str]
    edges: tuple[tuple[str, str], ...]
    inventory: tuple[int, int, int]
    symmetry_pairs: tuple[tuple[str, str], ...] = ()
    description: str = ""
    def __post_init__(self) -> None:
        identifiers=set(self.positions)
        if not self.positions or len(identifiers)!=len(self.positions):
            raise ModelSpecificationError("positions must be nonempty and unique")
        if not self.boundary <= identifiers or not self.inner <= identifiers:
            raise ModelSpecificationError("boundary and inner positions must belong to positions")
        if self.boundary & self.inner:
            raise ModelSpecificationError("boundary and inner regions must be disjoint")
        if len(self.inventory)!=3 or any(n<0 for n in self.inventory):
            raise ModelSpecificationError("inventory must have three nonnegative counts")
        if sum(self.inventory)!=len(self.positions):
            raise ModelSpecificationError("inventory total must equal number of positions")
        canonical_edges=set()
        for left,right in self.edges:
            if left not in identifiers or right not in identifiers or left==right:
                raise ModelSpecificationError("each edge must join two distinct known positions")
            edge=tuple(sorted((left,right)))
            if edge in canonical_edges:
                raise ModelSpecificationError("undirected edges must be listed once")
            canonical_edges.add(edge)
        for left,right in self.symmetry_pairs:
            if left not in identifiers or right not in identifiers or left==right:
                raise ModelSpecificationError("symmetry pairs must join distinct known positions")
    @classmethod
    def from_json(cls,path: str|Path)->"CoreSpec":
        raw=json.loads(Path(path).read_text(encoding="utf-8"))
        inventory=raw["inventory"]
        return cls(name=raw["name"],positions=tuple(raw["positions"]),boundary=frozenset(raw["boundary"]),inner=frozenset(raw["inner"]),edges=tuple(tuple(edge) for edge in raw["edges"]),inventory=tuple(inventory[label] for label in BURNUP_LABELS),symmetry_pairs=tuple(tuple(pair) for pair in raw.get("symmetry_pairs",[])),description=raw.get("description",""))

@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    vector: tuple[int,...]

@dataclass(frozen=True)
class QuboModel:
    spec: CoreSpec
    q_upper: tuple[tuple[float,...],...]
    offset: float
    @property
    def variable_count(self)->int: return len(self.spec.positions)*len(BURNUP_LABELS)
    def variable_index(self,burnup:int,position:str)->int:
        return burnup*len(self.spec.positions)+self.spec.positions.index(position)
    def _require_binary(self,vector:Sequence[int])->tuple[int,...]:
        if len(vector)!=self.variable_count:
            raise CandidateMappingError(f"candidate has {len(vector)} variables; expected {self.variable_count}")
        converted=tuple(vector)
        if any(value not in (0,1) for value in converted):
            raise CandidateMappingError("candidate variables must all be binary 0 or 1")
        return converted
    def quadratic_energy(self,vector:Sequence[int])->float:
        z=self._require_binary(vector)
        return sum(self.q_upper[row][column]*z[row]*z[column] for row in range(self.variable_count) for column in range(row,self.variable_count))
    def energy(self,vector:Sequence[int])->float:
        return self.quadratic_energy(vector)+self.offset
    def value(self,vector:Sequence[int],burnup:int,position:str)->int:
        return self._require_binary(vector)[self.variable_index(burnup,position)]
    def direct_penalty_terms(self,vector:Sequence[int])->dict[str,float]:
        z=self._require_binary(vector); x=lambda burnup,position:z[self.variable_index(burnup,position)]
        cell_loading=sum((sum(x(burnup,position) for burnup in range(3))-1)**2 for position in self.spec.positions)
        inventory=sum((sum(x(burnup,position) for position in self.spec.positions)-self.spec.inventory[burnup])**2 for burnup in range(3))
        forbidden_regions=sum(x(TWICE_BURNED,position) for position in self.spec.boundary)**2+sum(x(FRESH,position) for position in self.spec.inner)**2
        fresh_adjacency=sum(x(FRESH,left)*x(FRESH,right) for left,right in self.spec.edges if left not in self.spec.boundary and right not in self.spec.boundary)
        twice_burned_adjacency=sum(x(TWICE_BURNED,left)*x(TWICE_BURNED,right) for left,right in self.spec.edges)
        symmetry=sum((x(burnup,left)-x(burnup,right))**2 for left,right in self.spec.symmetry_pairs for burnup in range(3))
        return {"cell_loading":float(cell_loading),"inventory":float(inventory),"forbidden_regions":float(forbidden_regions),"fresh_adjacency":float(fresh_adjacency),"twice_burned_adjacency":float(twice_burned_adjacency),"symmetry":float(symmetry)}
    def constraint_violations(self,vector:Sequence[int])->dict[str,int]:
        z=self._require_binary(vector); x=lambda burnup,position:z[self.variable_index(burnup,position)]
        values={}
        for position in self.spec.positions:
            values[f"cell:{position}"]=abs(sum(x(burnup,position) for burnup in range(3))-1)
        for burnup,label in enumerate(BURNUP_LABELS):
            values[f"inventory:{label}"]=abs(sum(x(burnup,position) for position in self.spec.positions)-self.spec.inventory[burnup])
        values["forbidden:fresh_inner"]=sum(x(FRESH,position) for position in self.spec.inner)
        values["forbidden:twice_burned_boundary"]=sum(x(TWICE_BURNED,position) for position in self.spec.boundary)
        values["adjacency:fresh_nonboundary"]=sum(x(FRESH,left)*x(FRESH,right) for left,right in self.spec.edges if left not in self.spec.boundary and right not in self.spec.boundary)
        values["adjacency:twice_burned"]=sum(x(TWICE_BURNED,left)*x(TWICE_BURNED,right) for left,right in self.spec.edges)
        values["symmetry"]=sum(int(x(burnup,left)!=x(burnup,right)) for left,right in self.spec.symmetry_pairs for burnup in range(3))
        return values
    def is_feasible(self,vector:Sequence[int])->bool:
        return all(value==0 for value in self.constraint_violations(vector).values())
    def decode(self,vector:Sequence[int])->dict[str,str]:
        if not self.is_feasible(vector):
            violations={name:value for name,value in self.constraint_violations(vector).items() if value}
            raise CandidateMappingError(f"candidate violates loading constraints: {violations}")
        return {position:BURNUP_LABELS[next(burnup for burnup in range(3) if self.value(vector,burnup,position)==1)] for position in self.spec.positions}

def _add_square(q_upper:list[list[float]],coefficients:Mapping[int,float],constant:float)->float:
    indexes=sorted(coefficients)
    for index in indexes:
        coefficient=coefficients[index]
        q_upper[index][index]+=coefficient*coefficient+2.0*constant*coefficient
    for left,right in combinations(indexes,2):
        q_upper[left][right]+=2.0*coefficients[left]*coefficients[right]
    return constant*constant

def _add_pair(q_upper:list[list[float]],left:int,right:int,weight:float=1.0)->None:
    if left==right: q_upper[left][left]+=weight
    else: q_upper[min(left,right)][max(left,right)]+=weight

def build_usmanov_style_qubo(spec:CoreSpec)->QuboModel:
    variable_count=len(spec.positions)*3
    q_upper=[[0.0 for _ in range(variable_count)] for _ in range(variable_count)]
    model_index=lambda burnup,position:burnup*len(spec.positions)+spec.positions.index(position)
    offset=0.0
    for position in spec.positions:
        offset+=_add_square(q_upper,{model_index(burnup,position):1.0 for burnup in range(3)},-1.0)
    for burnup,target in enumerate(spec.inventory):
        offset+=_add_square(q_upper,{model_index(burnup,position):1.0 for position in spec.positions},-float(target))
    offset+=_add_square(q_upper,{model_index(TWICE_BURNED,position):1.0 for position in spec.boundary},0.0)
    offset+=_add_square(q_upper,{model_index(FRESH,position):1.0 for position in spec.inner},0.0)
    for left,right in spec.edges:
        if left not in spec.boundary and right not in spec.boundary:
            _add_pair(q_upper,model_index(FRESH,left),model_index(FRESH,right))
        _add_pair(q_upper,model_index(TWICE_BURNED,left),model_index(TWICE_BURNED,right))
    for left,right in spec.symmetry_pairs:
        for burnup in range(3):
            offset+=_add_square(q_upper,{model_index(burnup,left):1.0,model_index(burnup,right):-1.0},0.0)
    return QuboModel(spec,tuple(tuple(row) for row in q_upper),offset)

def categorical_vector(spec:CoreSpec,categories:Sequence[int])->tuple[int,...]:
    if len(categories)!=len(spec.positions) or any(category not in range(3) for category in categories):
        raise CandidateMappingError("categorical candidate must give one value in {0,1,2} per position")
    return tuple(int(categories[position_index]==burnup) for burnup in range(3) for position_index in range(len(spec.positions)))

def enumerate_feasible_candidates(model:QuboModel,max_categorical_states:int=100_000)->list[Candidate]:
    state_count=3**len(model.spec.positions)
    if state_count>max_categorical_states:
        raise ModelSpecificationError(f"exact enumeration would visit {state_count} categorical states; increase the limit deliberately")
    candidates=[]
    for state_index,categories in enumerate(product(range(3),repeat=len(model.spec.positions))):
        vector=categorical_vector(model.spec,categories)
        if model.is_feasible(vector):
            candidates.append(Candidate(f"enum-{state_index:04d}",vector))
    return candidates

def deduplicate_candidates(candidates:Iterable[Candidate])->list[Candidate]:
    seen=set(); deduplicated=[]
    for candidate in candidates:
        if candidate.vector not in seen:
            seen.add(candidate.vector); deduplicated.append(candidate)
    return deduplicated
