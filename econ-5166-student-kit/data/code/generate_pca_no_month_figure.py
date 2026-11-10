"""Generate the slide-ready PCA figure for the no-month clustering specification."""

from pathlib import Path
import hashlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


def find_root() -> Path:
    for path in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        if (path / "AGENTS.md").is_file() and (path / "templates").is_dir():
            return path
    raise FileNotFoundError("請從學生專案內執行。")


ROOT = find_root()
OUTPUT = ROOT / "finding/assets/nighttime_midterm/pca_scree_no_month.png"
INPUTS = {
    "unweighted": (
        ROOT / "data/processed/taipei_2025_nighttime_clustering_matrix_unweighted.csv",
        "6a6d92299d333cce4dcc9b1f425faa28e0d8a20ba2b76dc7221ecc1d85328ab6",
        "一般 one-hot",
        "#356a9a",
    ),
    "block_weighted": (
        ROOT / "data/processed/taipei_2025_nighttime_clustering_matrix_block_weighted.csv",
        "88173998c8c597af0ce653e1b6764b03ed2582cdb961c3975de12079ab304e37",
        "類別區塊加權",
        "#c87936",
    ),
}

plt.rcParams.update({
    "font.sans-serif": ["Microsoft JhengHei", "Microsoft YaHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
})

results = {}
for key, (path, expected_hash, label, color) in INPUTS.items():
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(f"輸入版本已改變：{path.relative_to(ROOT)}")
    frame = pd.read_csv(path, encoding="utf-8-sig")
    if frame.shape != (6701, 50) or not frame["record_id"].is_unique:
        raise ValueError(f"輸入結構不符：{path.relative_to(ROOT)}")
    matrix = frame.drop(columns=["record_id", "z__month_sin", "z__month_cos"])
    if matrix.shape != (6701, 47) or matrix.isna().any().any():
        raise ValueError(f"不含月份矩陣結構不符：{path.relative_to(ROOT)}")
    pca = PCA(svd_solver="full").fit(matrix.to_numpy(dtype=float))
    ratio = pca.explained_variance_ratio_
    cumulative = ratio.cumsum()
    retained = int(np.searchsorted(cumulative, 0.80) + 1)
    results[key] = (ratio, cumulative, retained, label, color)

assert results["unweighted"][2] == 6
assert np.isclose(results["unweighted"][1][5], 0.8396746593409427)
assert results["block_weighted"][2] == 3
assert np.isclose(results["block_weighted"][1][2], 0.9212990172112467)

fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), dpi=150)
for ratio, cumulative, retained, label, color in results.values():
    component = np.arange(1, len(ratio) + 1)
    axes[0].plot(
        component, ratio * 100, marker="o", markersize=3.5,
        linewidth=1.8, color=color, label=label,
    )
    axes[1].plot(
        component, cumulative * 100, marker="o", markersize=3.5,
        linewidth=1.8, color=color, label=label,
    )
    retained_variance = cumulative[retained - 1] * 100
    axes[1].scatter([retained], [retained_variance], s=70, color=color, zorder=5)
    axes[1].annotate(
        f"{retained}個主成分：{retained_variance:.2f}%",
        xy=(retained, retained_variance), xytext=(8, -18),
        textcoords="offset points", color=color, fontsize=9,
    )

axes[0].set(
    title="各主成分解釋變異比例", xlabel="主成分編號", ylabel="解釋變異（%）",
)
axes[1].axhline(80, color="#666666", linestyle="--", linewidth=1.2, label="80%門檻")
axes[1].set(
    title="累積解釋變異", xlabel="保留主成分數",
    ylabel="累積解釋變異（%）", ylim=(0, 103),
)
for axis in axes:
    axis.grid(alpha=0.22)
    axis.legend(fontsize=9)

fig.suptitle("不含月份規格的PCA解釋變異比較（N=6,701；47個特徵）", fontsize=15)
fig.text(
    0.5, 0.015,
    "一般矩陣保留6個主成分（83.97%）；類別區塊加權矩陣保留3個主成分（92.13%）。",
    ha="center", fontsize=10,
)
fig.subplots_adjust(left=0.08, right=0.98, bottom=0.16, top=0.84, wspace=0.25)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT, dpi=180, bbox_inches="tight", pad_inches=0.25)
plt.close(fig)

print(OUTPUT.relative_to(ROOT))
