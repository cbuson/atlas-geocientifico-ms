#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

from pyproj import CRS, Transformer
from shapely.geometry import box, mapping, shape
from shapely.ops import transform, unary_union
try:
    from shapely import make_valid
except ImportError:
    make_valid = None

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'docs' / 'index.html'
OUT = ROOT / 'data' / 'imc_v32_snapshot.json'
COVERAGE_OUT = ROOT / 'data' / 'cobertura_cartografica_v32.geojson'
DATE = '2026-08-13'

# Coberturas com nomenclatura cartográfica explicitamente documentada em produtos SGB/CPRM.
# Produtos conhecidos sem polígono/folha exata materializada neste corte não entram silenciosamente.
COVERAGES = [
    # PLGB 1:250.000
    {'code':'SE.21-Y-D','name':'Corumbá','scale':250000,'year':2001,'source':'SGB/CPRM · PLGB Corumbá, Aldeia Tomázia e Porto Murtinho'},
    {'code':'SF.21-V-B','name':'Aldeia Tomázia','scale':250000,'year':2001,'source':'SGB/CPRM · PLGB Corumbá, Aldeia Tomázia e Porto Murtinho'},
    {'code':'SF.21-V-D','name':'Porto Murtinho','scale':250000,'year':2001,'source':'SGB/CPRM · PLGB Corumbá, Aldeia Tomázia e Porto Murtinho'},
    {'code':'SF.21-X-A','name':'Aquidauana','scale':250000,'year':1999,'source':'SGB/CPRM · PLGB Folha Aquidauana'},

    # Folhas 1:100.000 com código de folha explicitamente identificado.
    {'code':'SF.21-V-B-VI','name':'Aldeia Tomázia','scale':100000,'year':None,'source':'SGB · folha geológica 1:100.000'},
    {'code':'SF.21-V-D-III','name':'Fazenda Santa Otília','scale':100000,'year':2014,'source':'SGB · folha geológica 1:100.000'},
    {'code':'SF.21-V-D-VI','name':'Colônia São Lourenço','scale':100000,'year':2020,'source':'SGB · folha geológica 1:100.000'},
    {'code':'SF.21-X-A-IV','name':'Vila Campão','scale':100000,'year':2020,'source':'SGB · folha geológica 1:100.000'},
    {'code':'SF.21-X-C-I','name':'Rio Perdido','scale':100000,'year':2020,'source':'SGB · folha geológica 1:100.000'},
    {'code':'SF.21-X-C-IV','name':'Fazenda Margarida','scale':100000,'year':2014,'source':'SGB · folha geológica 1:100.000'},

    # PLGB Serra do Amolar, 1991, três folhas 1:100.000 documentadas no RIGeo.
    {'code':'SE.21-V-D-V','name':'Morraria da Ínsua','scale':100000,'year':1991,'source':'SGB/CPRM · PLGB Geologia da região da Serra do Amolar'},
    {'code':'SE.21-Y-B-II','name':'Lagoa Mandioré','scale':100000,'year':1991,'source':'SGB/CPRM · PLGB Geologia da região da Serra do Amolar'},
    {'code':'SE.21-Y-B-III','name':'Amolar','scale':100000,'year':1991,'source':'SGB/CPRM · PLGB Geologia da região da Serra do Amolar'},
]

PENDING_EXACT_FOOTPRINT = [
    'Projeto Rio Apa · 1:100.000 · polígono exato ainda não materializado neste corte',
    'Projeto Bonito–Aquidauana · 1:50.000 · polígono exato ainda não materializado neste corte',
    'PIMA Fosfato da Serra da Bodoquena · 1:50.000 · polígono exato ainda não materializado neste corte',
    'Projeto Bodoquena · 1:250.000 · polígono exato ainda não materializado neste corte',
]

GRID_IDS = {
    '250': 'malha_r5_250km2',
    '500': 'malha_500km2',
    '1000': 'malha_1000km2',
}


def extract_atlas_data(text: str, layer_id: str):
    prefix = f'window.ATLAS_DATA["{layer_id}"]='
    start = text.index(prefix) + len(prefix)
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def million_extent(code: str) -> Tuple[float,float,float,float]:
    # code e.g. SF.21 or SE.21
    m = re.fullmatch(r'S([A-Z])\.(\d{2})', code)
    if not m:
        raise ValueError(f'Código milionésimo inválido {code}')
    lat_letter, col_s = m.groups()
    col = int(col_s)
    # Coluna 21 = 60W–54W, aumentando 6° para leste.
    west = -60.0 + 6.0 * (col - 21)
    east = west + 6.0
    # SA 0–4S, SB 4–8S ... SF 20–24S.
    idx = ord(lat_letter) - ord('A')
    north = -4.0 * idx
    south = north - 4.0
    return west, south, east, north


def split_quadrant(ext, code):
    west, south, east, north = ext
    midx = (west + east) / 2.0
    midy = (south + north) / 2.0
    q = {
        'V': (west, midy, midx, north),   # NW
        'X': (midx, midy, east, north),   # NE
        'Y': (west, south, midx, midy),   # SW
        'Z': (midx, south, east, midy),   # SE
        'A': (west, midy, midx, north),
        'B': (midx, midy, east, north),
        'C': (west, south, midx, midy),
        'D': (midx, south, east, midy),
    }
    return q[code]


def split_100k(ext, roman):
    west, south, east, north = ext
    dx = (east - west) / 3.0
    dy = (north - south) / 2.0
    rc = {
        'I': (0,1), 'II': (1,1), 'III': (2,1),
        'IV': (0,0), 'V': (1,0), 'VI': (2,0),
    }
    c, r = rc[roman]
    x0 = west + c * dx
    x1 = x0 + dx
    y0 = south + r * dy
    y1 = y0 + dy
    return x0, y0, x1, y1


def sheet_extent(code: str) -> Tuple[float,float,float,float]:
    parts = code.split('-')
    head = parts[0]
    ext = million_extent(head)
    if len(parts) >= 2:
        ext = split_quadrant(ext, parts[1])
    if len(parts) >= 3:
        ext = split_quadrant(ext, parts[2])
    if len(parts) >= 4:
        ext = split_100k(ext, parts[3])
    if len(parts) > 4:
        raise ValueError(f'Escala abaixo de 1:100.000 não suportada por código neste corte {code}')
    return ext


def safe_geom(g):
    if g.is_empty:
        return g
    if g.is_valid:
        return g
    if make_valid is not None:
        g2 = make_valid(g)
        if not g2.is_empty:
            return g2
    return g.buffer(0)


def imc_class(v: float) -> str:
    if v < 20: return 'muito baixo'
    if v < 40: return 'baixo'
    if v < 60: return 'médio'
    if v < 75: return 'alto'
    return 'muito alto'


def pct(v):
    return round(100.0 * v, 2)


def main():
    text = HTML.read_text(encoding='utf-8')
    grids = {k: extract_atlas_data(text, v) for k,v in GRID_IDS.items()}
    state_fc = extract_atlas_data(text, 'limite_ms_ibge_2025')
    state = safe_geom(shape(state_fc['features'][0]['geometry']))

    # Equal-area local projection for areal weights.
    laea = CRS.from_proj4('+proj=laea +lat_0=-20.5 +lon_0=-54.5 +datum=WGS84 +units=m +no_defs')
    fwd = Transformer.from_crs('EPSG:4326', laea, always_xy=True).transform

    coverage_features = []
    cover_geoms_by_scale: Dict[int, List] = {100000: [], 250000: []}
    cover_records = []
    for rec in COVERAGES:
        ext = sheet_extent(rec['code'])
        raw = box(*ext)
        clipped = safe_geom(raw.intersection(state))
        if clipped.is_empty:
            # Keep audit evidence but it has no MS contribution.
            ms_area = 0.0
        else:
            ms_area = transform(fwd, clipped).area / 1e6
            cover_geoms_by_scale[rec['scale']].append(clipped)
        props = dict(rec)
        props['extent_wgs84'] = [round(x,6) for x in ext]
        props['area_em_ms_km2'] = round(ms_area, 3)
        props['regra_geometria'] = 'extensão oficial da folha pela nomenclatura cartográfica sistemática, recortada ao limite de MS'
        cover_records.append(props)
        if not clipped.is_empty:
            coverage_features.append({'type':'Feature','properties':props,'geometry':mapping(clipped)})

    union100 = safe_geom(unary_union(cover_geoms_by_scale[100000]))
    union250 = safe_geom(unary_union(cover_geoms_by_scale[250000]))
    union100_p = transform(fwd, union100)
    union250_p = transform(fwd, union250)

    out = {
        'version': 'V32',
        'date': DATE,
        'projection_area': '+proj=laea +lat_0=-20.5 +lon_0=-54.5 +datum=WGS84 +units=m +no_defs',
        'formula': 'IMC_h = 100 × [1,00 A100 + 0,40 A250 + 0,10 A1000] / A_h',
        'rule': 'A escala mais detalhada prevalece nas sobreposições. A1000 é a área remanescente coberta pela base estadual 1:1.000.000.',
        'baseline': 'SGB/CPRM · mapa geológico estadual de Mato Grosso do Sul · 1:1.000.000 · 2006',
        'verified_coverages': cover_records,
        'pending_exact_footprints': PENDING_EXACT_FOOTPRINT,
        'grids': {},
    }

    for scale_name, fc in grids.items():
        scores = {}
        vals = []
        for feat in fc['features']:
            hid = str(feat.get('properties',{}).get('hex_id',''))
            hg = safe_geom(shape(feat['geometry']))
            hp = safe_geom(transform(fwd, hg))
            ah = hp.area
            if ah <= 0:
                scores[hid] = {'imc_100': None, 'classe_imc':'sem dados', 'erro':'área projetada inválida'}
                continue

            # Best available scale. 100k overrides 250k. Baseline 1M fills the remainder.
            i100 = safe_geom(hp.intersection(union100_p))
            a100 = i100.area
            rem_after_100 = safe_geom(hp.difference(union100_p))
            i250 = safe_geom(rem_after_100.intersection(union250_p))
            a250 = i250.area
            a1000 = max(0.0, ah - a100 - a250)
            imc = 100.0 * (1.0*a100 + 0.4*a250 + 0.1*a1000) / ah
            imc = min(100.0, max(0.0, imc))

            # Supporting sheet codes by geometric intersection in geographic CRS.
            support = []
            for rec in COVERAGES:
                sg = box(*sheet_extent(rec['code']))
                if hg.intersects(sg) and not hg.intersection(sg).is_empty:
                    # Avoid listing sheets whose only contact is a zero-area boundary touch.
                    int_area = transform(fwd, safe_geom(hg.intersection(sg))).area
                    if int_area > 1.0:
                        support.append(rec['code'])

            best_scale = '1:1.000.000'
            if a250 > 1.0:
                best_scale = '1:250.000'
            if a100 > 1.0:
                best_scale = '1:100.000'

            recp = {
                'imc_100': round(imc, 1),
                'classe_imc': imc_class(imc),
                'pct_100k': pct(a100/ah),
                'pct_250k': pct(a250/ah),
                'pct_1000k': pct(a1000/ah),
                'melhor_escala_detectada': best_scale,
                'folhas_detalhadas_intersectadas': support,
                'area_calculo_km2': round(ah/1e6, 4),
                'formula': 'IMC_h = 100 × [1,00 A100 + 0,40 A250 + 0,10 A1000] / A_h',
                'metodo': 'V32 · interseção areal exata em projeção Lambert Azimutal Equal-Area · melhor escala prevalece nas sobreposições',
                'base_minima': 'SGB/CPRM · Mato Grosso do Sul 1:1.000.000 · 2006',
                'cobertura_detalhada': 'snapshot conservador de folhas SGB/CPRM com código cartográfico e escala verificados',
                'limite_metodologico': 'Projetos conhecidos sem polígono exato materializado neste corte não são imputados espacialmente. Constam como pendentes de captura.',
                'data_calculo': DATE,
            }
            scores[hid] = recp
            vals.append(imc)

        # Stats
        classes = {}
        for v in vals:
            c = imc_class(v)
            classes[c] = classes.get(c,0)+1
        out['grids'][scale_name] = {
            'grid_id': GRID_IDS[scale_name],
            'n_cells': len(fc['features']),
            'n_valid': len(vals),
            'min': round(min(vals), 3) if vals else None,
            'max': round(max(vals), 3) if vals else None,
            'mean': round(sum(vals)/len(vals), 3) if vals else None,
            'unique_rounded_1dp': len(set(round(v,1) for v in vals)),
            'classes': classes,
            'scores': scores,
        }

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(',',':')), encoding='utf-8')
    coverage_fc = {
        'type':'FeatureCollection',
        'features':coverage_features,
        'atlas_metadata':{
            'version':'V32',
            'date':DATE,
            'purpose':'Coberturas detalhadas efetivamente usadas no IMC V32',
            'baseline_not_drawn':'Mapa estadual SGB/CPRM 1:1.000.000 de 2006',
            'pending_exact_footprints':PENDING_EXACT_FOOTPRINT,
        }
    }
    COVERAGE_OUT.write_text(json.dumps(coverage_fc, ensure_ascii=False, separators=(',',':')), encoding='utf-8')

    print('Wrote', OUT)
    for k,v in out['grids'].items():
        print(k, {kk:vv for kk,vv in v.items() if kk!='scores'})
    print('Coverage features', len(coverage_features))
    for c in cover_records:
        print(c['code'], c['name'], c['scale'], c['extent_wgs84'], c['area_em_ms_km2'])

if __name__ == '__main__':
    main()
