# GHG Assessment - Case Study

This project calculates the greenhouse-gas (GHG) inventory of the company from
the Excel workbook [`data.xlsx`](./data.xlsx).

## How to run

Install the project dependencies and run:

```bash
uv run python ghg_assessment.py
```

The script expects the input workbook to be named `data.xlsx` in the project
root. It reads the following columns, preserving their order and units:

`Activity data`, `Value`, `Unit`, `Emission factor`, `Unit2`, `Ufe`, `Udata`,
`Upost`, `Scope`, `GHG Emissions`, and `Unit3`.

All code, generated labels, workbook sheet names, figure names, and this
documentation are in English.

## Method

For each source, the central emission is calculated as:

```text
central emissions (kgCO2e) = Value × Emission factor
```

`Ufe` and `Udata` are treated as relative uncertainties. The combined relative
uncertainty is:

```text
combined uncertainty = sqrt(Ufe² + Udata²)
```

The absolute uncertainty is then calculated from the central emission. This is
why the existing `GHG Emissions` column is retained as an input/reference
column, while the new central-emission columns provide the inventory used for
the results. The workbook's `Upost` values are checked against this formula by
the data structure, but the calculation is recomputed from `Ufe` and `Udata`
to avoid silently trusting a derived input.

The script converts kilograms to tonnes using `1 tCO2e = 1,000 kgCO2e`.
Scope totals are obtained by summing source-level emissions. The uncertainty
reported for a total is the sum of the source absolute uncertainties, which is
a conservative aggregation suitable for this assessment.

## Deliverables

Running the script creates:

- [`ghg_assessment_results.xlsx`](./ghg_assessment_results.xlsx), with:
  - **Source results**: every input row, central emissions, absolute and
    relative uncertainties, and lower/upper bounds;
  - **Scope summary**: emissions, uncertainty, bounds, and share of total for
    Scopes 1, 2, and 3;
  - **Company summary**: total company footprint, footprint per employee, and
    employee count.
- [`figures/carbon_footprint_per_scope.png`](./figures/carbon_footprint_per_scope.png),
  a pie chart of the footprint by scope.
- [`figures/emissions_by_source_with_uncertainty.png`](./figures/emissions_by_source_with_uncertainty.png),
  a source-level bar chart with uncertainty error bars.

## Results for the current workbook

Using the current `data.xlsx`, the calculated results are:

| Metric | Result |
|---|---:|
| Total company footprint | **928.20 ± 388.64 tCO2e** |
| Footprint per employee (179 employees) | **5.19 ± 2.17 tCO2e/employee** |

| Scope | Emissions | Share |
|---|---:|---:|
| Scope 1 | **405.00 ± 45.28 tCO2e** | **43.6%** |
| Scope 2 | **37.71 ± 19.60 tCO2e** | **4.1%** |
| Scope 3 | **485.49 ± 323.75 tCO2e** | **52.3%** |

The dominant sources are **Cars (thermal)**, **E-cars**, **Other consultancy
fees**, and **Fuel consumption**. Scope 3 is therefore the main reduction
opportunity. The largest uncertainty comes from the financial-procurement
sources, because their emission-factor uncertainty is 80%, and from vehicle
embodied emissions.

## Interpretation and recommendations

1. **Prioritize fleet and mobility.** Thermal cars are the largest source.
   Replace combustion vehicles with low-carbon alternatives, reduce mileage
   through travel policies, encourage public transport and car sharing, and
   measure vehicle activity separately by fuel type and distance.
2. **Improve Scope 3 procurement data.** Consultancy fees and other financial
   categories dominate Scope 3 and have high factor uncertainty. Request
   supplier-specific product carbon footprints, distinguish purchased services
   from spend-based estimates, and update the factors annually.
3. **Reduce office and vehicle electricity demand.** Combine efficiency measures
   with renewable electricity contracts and verify the market- and
   location-based electricity factors used in the inventory.
4. **Extend the digital and equipment life cycle.** Keep laptops and printers
   in service longer, repair and refurbish equipment, buy lower-carbon models,
   and reduce unnecessary data storage and online meeting time.
5. **Use the uncertainty results to guide data collection.** Better activity
   data and supplier-specific emission factors will improve the reliability of
   future inventories more than adding precision to already uncertain
   calculations.

The recommendations should be reassessed after the company confirms the
activity definitions, reporting year, and whether the vehicle values represent
new purchases, the fleet stock, or a full life-cycle inventory.
