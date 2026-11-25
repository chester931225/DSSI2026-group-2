"""Unit 0.4 environment checks; synthetic tests and read-only raw smoke reads.

Run from the research root with .venv/Scripts/python.exe. No old notebook is run.
Only this validation JSON and ignored data/temp/urban_crash_environment are written.
This is a tool check, not a research finding or a raw-data quality certification.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import traceback
import warnings
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
TEMP = ROOT / "data/temp/urban_crash_environment"
REPORT = ROOT / "data/code/urban_crash_environment_validation.json"
EXPECTED_PYTHON = ROOT / ".venv/Scripts/python.exe"
TEMP.mkdir(parents=True, exist_ok=True)
for variable, folder in {
    "MPLCONFIGDIR": "matplotlib", "IPYTHONDIR": "ipython",
    "JUPYTER_CONFIG_DIR": "jupyter_config", "JUPYTER_RUNTIME_DIR": "jupyter_runtime",
    "XDG_CACHE_HOME": "cache", "XDG_DATA_HOME": "local_data",
    "NUMBA_CACHE_DIR": "numba", "TEMP": "scratch", "TMP": "scratch",
}.items():
    target = TEMP / folder
    target.mkdir(exist_ok=True)
    os.environ[variable] = str(target)
os.environ["PROJ_NETWORK"] = "OFF"
os.environ["JUPYTER_PATH"] = str(ROOT / ".venv/share/jupyter")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PACKAGES = {
    "pandas": "pandas", "numpy": "numpy", "scipy": "scipy",
    "statsmodels": "statsmodels", "geopandas": "geopandas", "shapely": "shapely",
    "pyproj": "pyproj", "pyogrio": "pyogrio", "scikit-learn": "sklearn",
    "libpysal": "libpysal", "esda": "esda", "matplotlib": "matplotlib",
    "seaborn": "seaborn", "jupyterlab": "jupyterlab", "ipykernel": "ipykernel",
    "nbformat": "nbformat", "nbclient": "nbclient", "pymupdf": "pymupdf",
    "astral": "astral",
}
RESULT = {
    "scope": "Unit 0.4: environment validation only; synthetic results are not research findings",
    "run_utc": datetime.now(timezone.utc).isoformat(),
    "python": platform.python_version(), "platform": platform.platform(),
    "bits": struct.calcsize("P") * 8,
    "python_project_relative": ".venv/Scripts/python.exe",
    "tests": {},
}


def import_libpysal_with_local_example_cache():
    """Route only the example-cache locator; spatial methods remain unmodified.

    libpysal has no data-home environment override in this installed release.
    Its import otherwise creates an unused per-user example-data directory.
    """
    from unittest.mock import patch
    import platformdirs
    original = platformdirs.user_data_dir

    def locate(appname=None, *args, **kwargs):
        if appname == "pysal":
            return str(TEMP / "pysal_examples")
        return original(appname, *args, **kwargs)

    with patch("platformdirs.user_data_dir", side_effect=locate):
        return importlib.import_module("libpysal")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(name, function):
    try:
        detail = function()
        status = "not checked" if isinstance(detail, dict) and detail.get("status") == "not checked" else "passed"
        RESULT["tests"][name] = {"status": status, "detail": detail}
        print(f"{status.upper()} {name}", flush=True)
    except Exception as exc:
        RESULT["tests"][name] = {
            "status": "failed", "error": str(exc), "traceback": traceback.format_exc()
        }
        print(f"FAIL {name}: {exc}", flush=True)


def package_check():
    from packaging.version import Version
    assert Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve()
    assert sys.prefix != sys.base_prefix and RESULT["bits"] == 64
    cfg = (ROOT / ".venv/pyvenv.cfg").read_text(encoding="utf-8")
    assert "include-system-site-packages = false" in cfg
    versions = {}
    for package, module_name in PACKAGES.items():
        module = (import_libpysal_with_local_example_cache() if module_name == "libpysal"
                  else importlib.import_module(module_name))
        assert Path(module.__file__).resolve().is_relative_to(ROOT / ".venv")
        version = metadata.version(package)
        assert not Version(version).is_prerelease and not Version(version).is_devrelease
        versions[package] = version
    assert versions["astral"] == "3.2"
    import pyogrio
    import shapely
    import pyproj
    RESULT["packages"] = versions
    RESULT["gis_libraries"] = {
        "GDAL": pyogrio.__gdal_version_string__,
        "GEOS": shapely.geos_version_string, "PROJ": pyproj.proj_version_str,
    }
    proc = subprocess.run([sys.executable, "-m", "pip", "check"],
                          capture_output=True, text=True, check=True)
    RESULT["pip_check"] = proc.stdout.strip()
    return {"imports": len(versions), "isolated": True, "stable_releases": True}


def data_check():
    import numpy as np
    import pandas as pd
    frame = pd.DataFrame({"group": ["甲", "甲", "乙"], "value": [4., np.nan, 6.]})
    path = TEMP / "synthetic.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    loaded = pd.read_csv(path, encoding="utf-8-sig")
    assert loaded.equals(frame) and loaded.value.isna().sum() == 1
    summary = loaded.groupby("group", as_index=False).value.sum()
    assert summary.set_index("group").value.to_dict() == {"甲": 4., "乙": 6.}
    merged = summary.merge(pd.DataFrame({"group": ["甲", "乙"], "label": [1, 2]}),
                           on="group", validate="one_to_one")
    assert len(merged) == 2 and merged.set_index("group").label.to_dict() == {"甲": 1, "乙": 2}
    assert loaded.value.fillna(0).tolist() == [4., 0., 6.]
    values = np.array([1., 2., 3.])
    assert values.mean() == 2 and values @ values == 14
    return {"csv_rows": 3, "group_sums": [4, 6], "missing_values": 1,
            "merge": "one_to_one", "numpy_dot": 14}


def synthetic_gis_check():
    import geopandas as gpd
    import numpy as np
    from shapely import make_valid
    from shapely.geometry import Point, LineString, Polygon, box
    x, y = 300000, 2770000
    a = box(x, y, x + 10, y + 10)
    b = box(x + 20, y, x + 30, y + 10)
    zones = gpd.GeoDataFrame({"zone": ["A", "B"]}, geometry=[a, b], crs=3826)
    points = gpd.GeoDataFrame(geometry=[Point(x + 1, y + 1), Point(x + 21, y + 1),
                                        Point(x + 50, y + 1)], crs=3826)
    joined = gpd.sjoin(points, zones, how="left", predicate="within")
    assert joined.zone.iloc[:2].tolist() == ["A", "B"] and joined.zone.isna().sum() == 1
    line = gpd.GeoSeries([LineString([(x, y), (x + 3, y + 4)])], crs=3826)
    np.testing.assert_allclose(zones.area, [100, 100])
    np.testing.assert_allclose(zones.length, [40, 40])
    assert line.length.iloc[0] == 5
    overlap = box(x + 5, y, x + 15, y + 10)
    assert a.intersection(overlap).area == 50
    other = gpd.GeoDataFrame(geometry=[overlap], crs=3826)
    intersection = gpd.overlay(zones.iloc[:1], other, how="intersection")
    union = gpd.overlay(zones.iloc[:1], other, how="union")
    assert intersection.area.sum() == 50 and union.area.sum() == 150
    roundtrip = zones.to_crs(4326).to_crs(3826)
    np.testing.assert_allclose(roundtrip.total_bounds, zones.total_bounds, atol=1e-5, rtol=0)
    origin = gpd.GeoSeries([Point(121, 25)], crs=4326).to_crs(3826)
    np.testing.assert_allclose(origin.x.iloc[0], 250000, atol=1e-5, rtol=0)
    invalid = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
    repaired = make_valid(invalid)
    assert not invalid.is_valid and repaired.is_valid and repaired.area == 2
    assert zones.is_valid.all()
    return {"crs": "EPSG:3826", "roundtrip": "3826 -> 4326 -> 3826",
            "spatial_join": ["A", "B", None], "polygon_area_m2": 100,
            "polygon_perimeter_m": 40, "line_length_m": 5,
            "intersection_area_m2": 50, "union_area_m2": 150,
            "make_valid": "invalid bowtie -> valid MultiPolygon, area 2"}


def machine_learning_check():
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score, adjusted_rand_score, adjusted_mutual_info_score
    rng = np.random.default_rng(5166)
    xy = np.vstack([rng.normal(center, .05, size=(30, 2))
                    for center in [(0, 0), (10, 0), (0, 10)]])
    values = np.column_stack([xy, xy.sum(axis=1)])
    scaled = StandardScaler().fit_transform(values)
    np.testing.assert_allclose(scaled.mean(axis=0), 0, atol=1e-12)
    np.testing.assert_allclose(scaled.std(axis=0), 1, atol=1e-12)
    pca = PCA(n_components=2).fit(scaled)
    np.testing.assert_allclose(pca.explained_variance_ratio_.sum(), 1, atol=1e-12)
    km = KMeans(n_clusters=3, n_init=20, random_state=5166).fit_predict(scaled)
    ward = AgglomerativeClustering(n_clusters=3, linkage="ward").fit_predict(scaled)
    truth = np.repeat(np.arange(3), 30)
    assert adjusted_rand_score(truth, km) == adjusted_rand_score(truth, ward) == 1
    assert adjusted_mutual_info_score(km, ward) > .999999
    silhouette = silhouette_score(scaled, km)
    assert silhouette > .9
    return {"seed": 5166, "synthetic_rows": 90, "clusters": 3,
            "silhouette": float(silhouette), "ARI": 1.,
            "AMI": float(adjusted_mutual_info_score(km, ward)),
            "PCA_explained_variance_sum": float(pca.explained_variance_ratio_.sum())}


def statistics_check():
    import numpy as np
    from scipy.stats import f_oneway, kruskal, chi2_contingency
    from statsmodels.stats.multitest import multipletests
    groups = ([1, 2, 3], [4, 5, 6], [7, 8, 9])
    anova, kw = f_oneway(*groups), kruskal(*groups)
    chi2, p, dof, _ = chi2_contingency([[10, 0], [0, 10]], correction=False)
    cramer_v = np.sqrt(chi2 / (20 * min(2 - 1, 2 - 1)))
    rejected, adjusted, _, _ = multipletests([.01, .04, .03, .2], method="fdr_bh")
    np.testing.assert_allclose([anova.statistic, kw.statistic, chi2, cramer_v], [27, 7.2, 20, 1])
    assert dof == 1 and 0 < p < 1
    np.testing.assert_allclose(adjusted, [.04, .0533333333333333, .0533333333333333, .2])
    assert rejected.tolist() == [True, False, False, False]
    return {"synthetic_ANOVA_F": float(anova.statistic), "synthetic_Kruskal_H": float(kw.statistic),
            "synthetic_chi2": float(chi2), "synthetic_Cramers_V": float(cramer_v),
            "BH_adjusted_p": adjusted.tolist(), "BH_rejected": rejected.tolist()}


def spatial_statistics_check():
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import box
    from libpysal.weights import Rook
    from esda.moran import Moran
    grid = gpd.GeoDataFrame(geometry=[box(300000 + c * 10, 2770000 + r * 10,
                                             300010 + c * 10, 2770010 + r * 10)
                                        for r in range(4) for c in range(4)], crs=3826)
    weights = Rook.from_dataframe(grid, use_index=True)
    assert weights.n == 16 and weights.sparse.nnz == 48 and not weights.islands
    weights.transform = "r"
    np.testing.assert_allclose(np.asarray(weights.sparse.sum(axis=1)).ravel(), 1)
    np.random.seed(5166)
    moran = Moran(np.arange(16, dtype=float), weights, permutations=99)
    np.testing.assert_allclose([moran.I, moran.EI], [.75, -1 / 15])
    return {"synthetic_grid": "4x4", "Rook_n": 16, "directed_neighbor_links": 48,
            "weight_transform": "row standardized", "Moran_I": float(moran.I),
            "expected_I": float(moran.EI), "permutations": 99, "seed": 5166,
            "interpretation": "tool validation only; no research inference"}


def visualization_check():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.ft2font import FT2Font
    import geopandas as gpd
    import seaborn as sns
    from shapely.geometry import box
    font = Path(os.environ["WINDIR"]) / "Fonts/msjh.ttc"
    assert font.is_file(), "Microsoft JhengHei missing; choose an installed CJK font before retrying"
    font_manager.fontManager.addfont(str(font))
    family = font_manager.FontProperties(fname=str(font)).get_name()
    probe = "合成資料測試數值熱圖地圖區域甲乙負號"
    face = FT2Font(str(font))
    assert all(face.get_char_index(ord(ch)) for ch in probe)
    fallback = font_manager.findfont("DejaVu Sans", fallback_to_default=False)
    assert FT2Font(fallback).get_char_index(ord("−"))
    plt.rcParams.update({"font.family": [family, "DejaVu Sans"], "axes.unicode_minus": True})
    assert Path(font_manager.findfont(family, fallback_to_default=False)).exists()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
        axes[0].plot([-1, 0, 1], [-1, 0, 1], marker="o")
        axes[0].set(title="合成資料測試", xlabel="數值", ylabel="負號 −1")
        sns.heatmap([[1, -1], [.5, 0]], annot=True, cmap="coolwarm", center=0,
                    xticklabels=["甲", "乙"], yticklabels=["甲", "乙"], ax=axes[1])
        axes[1].set_title("合成熱圖")
        zones = gpd.GeoDataFrame({"value": [-1, 1]},
                                geometry=[box(300000, 2770000, 300010, 2770010),
                                          box(300012, 2770000, 300022, 2770010)], crs=3826)
        zones.plot(column="value", cmap="coolwarm", edgecolor="black", ax=axes[2])
        for label, geometry in zip(["甲 −1", "乙 1"], zones.geometry):
            axes[2].text(geometry.centroid.x, geometry.centroid.y, label, ha="center")
        axes[2].set_title("合成地圖")
        axes[2].set_axis_off()
        fig.savefig(TEMP / "synthetic_visualization.png", dpi=150)
        minus_ticks = [t.get_text() for t in axes[0].get_xticklabels()]
        assert any("−" in text for text in minus_ticks)
        plt.close(fig)
    glyph_warnings = [str(w.message) for w in captured if "Glyph" in str(w.message)]
    assert not glyph_warnings, glyph_warnings
    return {"font": family, "minus_fallback": "DejaVu Sans", "font_file": "%WINDIR%/Fonts/msjh.ttc",
            "Chinese_and_U2212_glyph_check": "passed", "missing_glyph_warnings": glyph_warnings,
            "temporary_image": "data/temp/urban_crash_environment/synthetic_visualization.png",
            "visual_review": "requires human or image-tool inspection after rendering"}


def raw_smoke_check():
    import pandas as pd
    import geopandas as gpd
    import pymupdf
    detail = []
    for filename, encoding, expected in [
        ("113年-臺北市死傷交通事故明細.csv", "utf-8-sig", (51810, 49)),
        ("114年-臺北市死傷交通事故明細.csv", "utf-8-sig", (22762, 47)),
        ("112迄今各里人口數按年齡分.csv", "cp950", (64722, 107)),
    ]:
        path = ROOT / "data/raw" / filename
        before = sha256(path)
        frame = pd.read_csv(path, encoding=encoding, low_memory=False)
        assert frame.shape == expected and sha256(path) == before
        detail.append({"path": path.relative_to(ROOT).as_posix(), "encoding": encoding,
                       "rows": len(frame), "columns": len(frame.columns), "sha256": before})
    for filename, encoding, expected in [("G97_A_CAVLGE_P.shp", "utf-8", 456),
                                         ("細計-面.shp", "cp950", 15518),
                                         ("細計-文.shp", "cp950", 3)]:
        path = ROOT / "data/raw" / filename
        frame = gpd.read_file(path, engine="pyogrio", encoding=encoding)
        assert len(frame) == expected
        if filename == "G97_A_CAVLGE_P.shp":
            assert path.with_suffix(".prj").is_file() and frame.crs is not None
            assert frame.crs.to_epsg() == 3826
        else:
            assert not path.with_suffix(".prj").exists() and frame.crs is None
        detail.append({"path": path.relative_to(ROOT).as_posix(), "encoding": encoding,
                       "rows": len(frame), "columns": len(frame.columns),
                       "geometry_types": sorted(frame.geom_type.unique().tolist()),
                       "crs": str(frame.crs) if frame.crs else None,
                       "crs_epsg": frame.crs.to_epsg() if frame.crs else None,
                       "limit": "read only; no geometry quality validation, CRS assignment or spatial integration"})
    path = ROOT / "data/raw/事故對照表.pdf"
    with pymupdf.open(path) as document:
        assert len(document) == 4
        chars = [len(page.get_text()) for page in document]
        assert all(chars)
    detail.append({"path": path.relative_to(ROOT).as_posix(), "pages": 4,
                   "text_characters_by_page": chars, "sha256": sha256(path)})
    return detail


def notebook_check():
    import nbformat
    from nbclient import NotebookClient
    path = ROOT / ".venv/share/jupyter/kernels/dssi-urban-crash/kernel.json"
    kernel = json.loads(path.read_text(encoding="utf-8"))
    assert Path(kernel["argv"][0]).resolve() == EXPECTED_PYTHON.resolve()
    assert kernel["display_name"] == "DSSI Urban Crash"
    notebook = nbformat.v4.new_notebook(metadata={"kernelspec": {
        "name": "dssi-urban-crash", "display_name": "DSSI Urban Crash", "language": "python"}})
    notebook.cells = [
        nbformat.v4.new_code_cell("import sys, json\nfrom pathlib import Path\n"
            "expected = Path.cwd() / '.venv/Scripts/python.exe'\n"
            "assert Path(sys.executable).resolve() == expected.resolve()\n"
            "print(json.dumps({'sys.executable': sys.executable}))"),
        nbformat.v4.new_code_cell("import pandas as pd\nimport numpy as np\n"
            "sys.path.insert(0, str(Path.cwd() / 'data/code'))\n"
            "from validate_urban_crash_environment import import_libpysal_with_local_example_cache\n"
            "import_libpysal_with_local_example_cache()\n"
            "import geopandas, shapely, pyproj, pyogrio, sklearn, scipy, statsmodels\n"
            "import libpysal, esda, matplotlib, seaborn, pymupdf, astral\nprint('imports OK')"),
        nbformat.v4.new_code_cell("df = pd.DataFrame({'group': ['a', 'a', 'b'], 'x': [1, 2, 3]})\n"
            "result = df.groupby('group').x.sum().to_dict()\n"
            "assert result == {'a': 3, 'b': 3}\nassert np.arange(4).sum() == 6\nprint(result)"),
    ]
    client = NotebookClient(notebook, timeout=180, kernel_name="dssi-urban-crash",
                            resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    assert [cell.execution_count for cell in notebook.cells] == [1, 2, 3]
    assert not any(out.output_type == "error" for cell in notebook.cells for out in cell.outputs)
    first_output = "".join(out.get("text", "") for out in notebook.cells[0].outputs)
    actual = Path(json.loads(first_output)["sys.executable"])
    assert actual.resolve() == EXPECTED_PYTHON.resolve()
    nbformat.write(notebook, TEMP / "minimal_executed.ipynb")
    return {"kernel_name": "dssi-urban-crash", "display_name": kernel["display_name"],
            "kernelspec": ".venv/share/jupyter/kernels/dssi-urban-crash/kernel.json",
            "actual_python_matches_venv": True, "executed_code_cells": 3,
            "temporary_notebook": "data/temp/urban_crash_environment/minimal_executed.ipynb",
            "VS_Code_UI_selection": "not observable from CLI; student must select interpreter/kernel"}


def preserved_files_check():
    baseline = TEMP / "before_state.json"
    if not baseline.exists():
        return {"status": "not checked", "reason": "original Unit 0.4 baseline not available on this machine"}
    previous = json.loads(baseline.read_text(encoding="utf-8-sig"))
    protected = {p: digest for p, digest in previous["protected_files"].items() if p != "PROJECT.md"}
    changed = [p for p, digest in protected.items()
               if not (ROOT / p).is_file() or sha256(ROOT / p) != digest]
    assert not changed, changed
    return {"preexisting_files_checked": len(protected), "changed": changed,
            "allowed_exception": "PROJECT.md scoped update; no changes to existing raw data, notebooks, results or rules"}


if __name__ == "__main__":
    import argparse
    functions = [
        ("A_packages", package_check), ("B_data_processing", data_check),
        ("C_synthetic_GIS", synthetic_gis_check), ("D_synthetic_ML", machine_learning_check),
        ("E_synthetic_statistics", statistics_check), ("F_synthetic_spatial_statistics", spatial_statistics_check),
        ("G_visualization", visualization_check), ("raw_read_smoke", raw_smoke_check),
        ("notebook", notebook_check), ("preservation", preserved_files_check),
    ]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=[name for name, _ in functions],
                        help="Retry selected checks, preserving other results in an existing report")
    selected = parser.parse_args().only
    if selected and REPORT.is_file():
        previous = json.loads(REPORT.read_text(encoding="utf-8"))
        previous.update({k: v for k, v in RESULT.items() if k != "tests"})
        RESULT = previous
    for name, function in functions:
        if selected and name not in selected:
            continue
        check(name, function)
    RESULT["all_automated_checks_passed"] = all(
        RESULT["tests"].get(name, {}).get("status") == "passed" for name, _ in functions)
    REPORT.write_text(json.dumps(RESULT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.exit(0 if RESULT["all_automated_checks_passed"] else 1)
