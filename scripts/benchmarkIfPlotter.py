#!/usr/bin/env python3

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")


METRICS = [
    "peak_rss_mb",
    "state_classes_explored",
    "build_seconds",
]

FAMILY_AXES = {
    "structural": ("num_states", "branching_factor"),
    "temporal": ("num_states", "num_clocks"),
}


def get_family_axes(family):
    return FAMILY_AXES.get(family, ("num_states", "branching_factor"))


def flatten_columns(df):
    """
    Flatten multi-index columns after aggregation.
    Example:
        ('build_seconds', 'mean') -> build_seconds_mean
    """

    df.columns = [
        f"{col[0]}_{col[1]}" if col[1] else col[0]
        for col in df.columns.to_flat_index()
    ]

    return df


def load_and_prepare(csv_path):
    df = pd.read_csv(csv_path)

    required = [
        "family",
        "num_states",
        "branching_factor",
        "num_clocks",
        "seed",
        *METRICS,
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    grouped_frames = []

    for family, family_df in df.groupby("family"):
        x_column, y_column = get_family_axes(family)

        missing = [column for column in (x_column, y_column) if column not in family_df.columns]
        if missing:
            raise ValueError(f"Missing required columns for family '{family}': {missing}")

        grouped = (
            family_df.groupby(["family", x_column, y_column])
            .agg({
                "peak_rss_mb": ["mean", "std", "min", "max"],
                "state_classes_explored": ["mean", "std", "min", "max"],
                "build_seconds": ["mean", "std", "min", "max"],
                "seed": "count",
            })
            .reset_index()
        )

        grouped = flatten_columns(grouped)
        grouped = grouped.rename(columns={"seed_count": "num_runs"})
        grouped["x_axis"] = x_column
        grouped["y_axis"] = y_column

        grouped_frames.append(grouped)

    return pd.concat(grouped_frames, ignore_index=True)


def make_heatmap(df, metric, output_dir, family):
    """
    Heatmap of mean metric values.
    """

    family_df = df[df["family"] == family]
    x_column, y_column = get_family_axes(family)

    pivot = family_df.pivot_table(
        index=x_column,
        columns=y_column,
        values=f"{metric}_mean",
        aggfunc="mean",
    )

    plt.figure(figsize=(10, 7))

    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="viridis",
    )

    plt.title(f"{family}: {metric} (mean across seeds)")
    plt.xlabel(y_column)
    plt.ylabel(x_column)

    plt.tight_layout()

    out_path = output_dir / f"heatmap_{family}_{metric}.png"

    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def make_lineplot(df, metric, output_dir, family):
    """
    Line plot with standard deviation bands.
    """

    family_df = df[df["family"] == family]
    x_column, y_column = get_family_axes(family)

    plt.figure(figsize=(10, 6))

    y_values = sorted(family_df[y_column].unique())

    for value in y_values:
        subset = family_df[family_df[y_column] == value].sort_values(x_column)

        x = subset[x_column]
        y = subset[f"{metric}_mean"]
        std = subset[f"{metric}_std"].fillna(0)

        plt.plot(
            x,
            y,
            marker="o",
            label=f"{y_column}={value}",
        )

        plt.fill_between(
            x,
            y - std,
            y + std,
            alpha=0.2,
        )

    plt.title(f"{family}: {metric} scaling")
    plt.xlabel(x_column)
    plt.ylabel(metric)

    plt.legend(title=y_column)

    plt.tight_layout()

    out_path = output_dir / f"lineplot_{family}_{metric}.png"

    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def make_std_heatmap(df, metric, output_dir, family):
    """
    Heatmap of standard deviation.
    Useful to visualize instability/noise.
    """

    family_df = df[df["family"] == family]
    x_column, y_column = get_family_axes(family)

    pivot = family_df.pivot_table(
        index=x_column,
        columns=y_column,
        values=f"{metric}_std",
        aggfunc="mean",
    )

    plt.figure(figsize=(10, 7))

    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="magma",
    )

    plt.title(f"{family}: {metric} standard deviation")
    plt.xlabel(y_column)
    plt.ylabel(x_column)

    plt.tight_layout()

    out_path = output_dir / f"std_heatmap_{family}_{metric}.png"

    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved: {out_path}")


def save_aggregated_csv(df, output_dir):
    out_path = output_dir / "aggregated_results.csv"

    df.to_csv(out_path, index=False)

    print(f"Saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate benchmark plots from CSV results."
    )

    parser.add_argument(
        "csv_file",
        help="Input CSV file",
    )

    parser.add_argument(
        "--output-dir",
        default="results/plots",
        help="Directory to store plots",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_and_prepare(args.csv_file)

    save_aggregated_csv(df, output_dir)

    for family in sorted(df["family"].unique()):
        for metric in METRICS:
            make_heatmap(df, metric, output_dir, family)
            make_std_heatmap(df, metric, output_dir, family)
            make_lineplot(df, metric, output_dir, family)

    print("\nAll plots generated successfully.")


if __name__ == "__main__":
    print("Starting benchmark plot generation...")
    main()
    print("Finished benchmark plot generation.")
