"""Calculate the company's greenhouse-gas inventory from data.xlsx."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


INPUT_FILE = Path("data.xlsx")
OUTPUT_FILE = Path("ghg_assessment_results.xlsx")
FIGURES_DIRECTORY = Path("figures")
REQUIRED_COLUMNS = {
    "Activity data",
    "Value",
    "Unit",
    "Emission factor",
    "Unit2",
    "Ufe",
    "Udata",
    "Upost",
    "Scope",
    "GHG Emissions",
    "Unit3",
}


def load_activity_data(input_file: Path) -> pd.DataFrame:
    """Load and validate the activity-data workbook."""
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input workbook not found: {input_file}. "
            "Rename the workbook to data.xlsx and run the script again."
        )

    data = pd.read_excel(input_file)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns in {input_file}: {missing}")

    numeric_columns = [
        "Value",
        "Emission factor",
        "Ufe",
        "Udata",
        "Upost",
        "Scope",
        "GHG Emissions",
    ]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="raise")

    if (data["Value"] < 0).any() or (data["Emission factor"] < 0).any():
        raise ValueError("Value and Emission factor must not contain negative values.")
    if (~data["Scope"].isin([1, 2, 3])).any():
        raise ValueError("Scope must contain only 1, 2, or 3.")

    return data


def calculate_results(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Calculate source, scope, and company-level results."""
    results = data.copy()
    results["Central emissions (kgCO2e)"] = (
        results["Value"] * results["Emission factor"]
    )
    results["Combined uncertainty (%)"] = (
        np.sqrt(results["Ufe"] ** 2 + results["Udata"] ** 2) * 100
    )
    results["Uncertainty (kgCO2e)"] = (
        results["Central emissions (kgCO2e)"] * results["Combined uncertainty (%)"] / 100
    )
    results["Lower bound (kgCO2e)"] = (
        results["Central emissions (kgCO2e)"] - results["Uncertainty (kgCO2e)"]
    )
    results["Upper bound (kgCO2e)"] = (
        results["Central emissions (kgCO2e)"] + results["Uncertainty (kgCO2e)"]
    )
    results["Central emissions (tCO2e)"] = results["Central emissions (kgCO2e)"] / 1000
    results["Uncertainty (tCO2e)"] = results["Uncertainty (kgCO2e)"] / 1000
    results["Scope"] = results["Scope"].astype(int)

    scope_summary = (
        results.groupby("Scope", as_index=False)
        .agg(
            **{
                "Central emissions (kgCO2e)": ("Central emissions (kgCO2e)", "sum"),
                "Uncertainty (kgCO2e)": ("Uncertainty (kgCO2e)", "sum"),
            }
        )
        .sort_values("Scope")
    )
    scope_summary["Central emissions (tCO2e)"] = (
        scope_summary["Central emissions (kgCO2e)"] / 1000
    )
    scope_summary["Uncertainty (tCO2e)"] = scope_summary["Uncertainty (kgCO2e)"] / 1000
    scope_summary["Lower bound (tCO2e)"] = (
        scope_summary["Central emissions (tCO2e)"] - scope_summary["Uncertainty (tCO2e)"]
    )
    scope_summary["Upper bound (tCO2e)"] = (
        scope_summary["Central emissions (tCO2e)"] + scope_summary["Uncertainty (tCO2e)"]
    )
    scope_summary["Share of total (%)"] = (
        scope_summary["Central emissions (tCO2e)"]
        / scope_summary["Central emissions (tCO2e)"].sum()
        * 100
    )

    total_emissions = results["Central emissions (tCO2e)"].sum()
    total_uncertainty = results["Uncertainty (tCO2e)"].sum()
    employee_count = results.loc[
        results["Unit"].str.casefold().eq("employees"), "Value"
    ].sum()
    if employee_count <= 0:
        raise ValueError("The workbook must contain a positive employee count.")

    company_summary = pd.DataFrame(
        [
            {
                "Metric": "Total company footprint",
                "Value": total_emissions,
                "Unit": "tCO2e",
                "Uncertainty": total_uncertainty,
                "Lower bound": total_emissions - total_uncertainty,
                "Upper bound": total_emissions + total_uncertainty,
            },
            {
                "Metric": "Footprint per employee",
                "Value": total_emissions / employee_count,
                "Unit": "tCO2e/employee",
                "Uncertainty": total_uncertainty / employee_count,
                "Lower bound": (total_emissions - total_uncertainty) / employee_count,
                "Upper bound": (total_emissions + total_uncertainty) / employee_count,
            },
            {
                "Metric": "Number of employees",
                "Value": employee_count,
                "Unit": "employees",
                "Uncertainty": np.nan,
                "Lower bound": np.nan,
                "Upper bound": np.nan,
            },
        ]
    )
    return results, scope_summary, company_summary


def save_results(
    results: pd.DataFrame,
    scope_summary: pd.DataFrame,
    company_summary: pd.DataFrame,
    output_file: Path,
) -> None:
    """Save all deliverable quantities to a multi-sheet Excel workbook."""
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        results.to_excel(writer, sheet_name="Source results", index=False)
        scope_summary.to_excel(writer, sheet_name="Scope summary", index=False)
        company_summary.to_excel(writer, sheet_name="Company summary", index=False)


def create_figures(results: pd.DataFrame, scope_summary: pd.DataFrame) -> None:
    """Create and save the required footprint figures."""
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 7))
    plt.pie(
        scope_summary["Central emissions (tCO2e)"],
        labels=[f"Scope {scope}" for scope in scope_summary["Scope"]],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#4C78A8", "#F58518", "#54A24B"],
    )
    plt.title("Carbon footprint per scope")
    plt.tight_layout()
    plt.savefig(FIGURES_DIRECTORY / "carbon_footprint_per_scope.png", dpi=300)
    plt.close()

    source_results = results.sort_values("Central emissions (tCO2e)")
    plt.figure(figsize=(12, 9))
    plt.barh(
        source_results["Activity data"],
        source_results["Central emissions (tCO2e)"],
        xerr=source_results["Uncertainty (tCO2e)"],
        color="#4C78A8",
        ecolor="#222222",
        capsize=3,
    )
    plt.xlabel("Emissions (tCO2e); error bars show uncertainty")
    plt.ylabel("Emission source")
    plt.title("Emissions by source with uncertainty")
    plt.tight_layout()
    plt.savefig(
        FIGURES_DIRECTORY / "emissions_by_source_with_uncertainty.png",
        dpi=300,
    )
    plt.close()


def print_summary(company_summary: pd.DataFrame, scope_summary: pd.DataFrame) -> None:
    """Print the main deliverable values."""
    total = company_summary.iloc[0]
    per_employee = company_summary.iloc[1]
    print("GHG assessment results")
    print(f"Total company footprint: {total['Value']:.2f} ± {total['Uncertainty']:.2f} tCO2e")
    print(
        "Footprint per employee: "
        f"{per_employee['Value']:.2f} ± {per_employee['Uncertainty']:.2f} tCO2e/employee"
    )
    print("\nFootprint by scope:")
    for _, row in scope_summary.iterrows():
        print(
            f"Scope {int(row['Scope'])}: {row['Central emissions (tCO2e)']:.2f} ± "
            f"{row['Uncertainty (tCO2e)']:.2f} tCO2e "
            f"({row['Share of total (%)']:.1f}%)"
        )


def main() -> None:
    """Run the complete assessment pipeline."""
    data = load_activity_data(INPUT_FILE)
    results, scope_summary, company_summary = calculate_results(data)
    save_results(results, scope_summary, company_summary, OUTPUT_FILE)
    create_figures(results, scope_summary)
    print_summary(company_summary, scope_summary)
    print(f"\nResults saved to {OUTPUT_FILE}")
    print(f"Figures saved to {FIGURES_DIRECTORY}/")


if __name__ == "__main__":
    main()
