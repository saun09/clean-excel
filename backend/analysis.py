import pandas as pd
from data_cleaning import safe_numeric_conversion
import calendar
from dateutil import parser
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def group_data(df, group_by_columns, aggregation_rules=None):
    """
    Group data by specified columns with optional aggregations.
    
    Args:
        df: DataFrame to group
        group_by_columns: List of columns to group by
        aggregation_rules: Dictionary of {column: aggregation_function}
                           If None, will default to count aggregation
    
    Returns:
        Grouped DataFrame
    """
    if not group_by_columns:
        return df
    
    # Default to count aggregation if no rules provided
    if aggregation_rules is None:
        aggregation_rules = {'__count__': 'size'}
    
    try:
        grouped_df = df.groupby(group_by_columns).agg(aggregation_rules).reset_index()
        return grouped_df
    except Exception as e:
        print(f"Error during grouping: {str(e)}")
        return df

#-------------------------cluster analysis-------------------
def perform_cluster_analysis(df, cluster_col, analysis_type, target_col=None, group_by_col=None, selected_clusters=None):
    """Perform various types of analysis on clustered data"""
    
    if cluster_col not in df.columns:
        return None, "Cluster column not found"
    
    # Filter by selected clusters if specified
    if selected_clusters:
        df_filtered = df[df[cluster_col].isin(selected_clusters)]
    else:
        df_filtered = df
    
    if df_filtered.empty:
        return None, "No data found for selected clusters"
    
    try:
        if analysis_type == "cluster_summary":
            # Basic cluster summary
            result = df_filtered.groupby(cluster_col).agg({
                cluster_col: 'count'
            }).rename(columns={cluster_col: 'Total_Records'})
            
            if target_col and target_col in df_filtered.columns:
                numeric_data = safe_numeric_conversion(df_filtered[target_col])
                df_temp = df_filtered.copy()
                df_temp[f'{target_col}_numeric'] = numeric_data
                
                summary = df_temp.groupby(cluster_col)[f'{target_col}_numeric'].agg([
                    'sum', 'mean', 'count'
                ]).round(2)
                summary.columns = [f'{target_col}_Total', f'{target_col}_Average', f'{target_col}_Count']
                
                result = pd.concat([result, summary], axis=1)
            
            return result, "Analysis completed successfully"
        
        elif analysis_type == "top_clusters":
            if not target_col or target_col not in df_filtered.columns:
                return None, "Target column required for top clusters analysis"
            
            numeric_data = safe_numeric_conversion(df_filtered[target_col])
            df_temp = df_filtered.copy()
            df_temp[f'{target_col}_numeric'] = numeric_data
            
            result = df_temp.groupby(cluster_col)[f'{target_col}_numeric'].sum().sort_values(ascending=False).head(10)
            result = result.to_frame(f'Total_{target_col}')
            
            return result, "Top clusters analysis completed"
        
        elif analysis_type == "cluster_by_category":
            if not group_by_col or group_by_col not in df_filtered.columns:
                return None, "Group by column required for categorical analysis"
            
            if target_col and target_col in df_filtered.columns:
                numeric_data = safe_numeric_conversion(df_filtered[target_col])
                df_temp = df_filtered.copy()
                df_temp[f'{target_col}_numeric'] = numeric_data
                
                result = df_temp.groupby([cluster_col, group_by_col])[f'{target_col}_numeric'].sum().unstack(fill_value=0)
            else:
                result = df_filtered.groupby([cluster_col, group_by_col]).size().unstack(fill_value=0)
            
            return result, "Categorical analysis completed"
        
        elif analysis_type == "detailed_breakdown":
            if not group_by_col or group_by_col not in df_filtered.columns:
                return None, "Group by column required for detailed breakdown"
            
            result_list = []
            
            for cluster in df_filtered[cluster_col].unique():
                cluster_data = df_filtered[df_filtered[cluster_col] == cluster]
                
                breakdown = cluster_data.groupby(group_by_col).agg({
                    cluster_col: 'count'
                }).rename(columns={cluster_col: 'Record_Count'})
                
                if target_col and target_col in df_filtered.columns:
                    numeric_data = safe_numeric_conversion(cluster_data[target_col])
                    cluster_data_temp = cluster_data.copy()
                    cluster_data_temp[f'{target_col}_numeric'] = numeric_data
                    
                    summary = cluster_data_temp.groupby(group_by_col)[f'{target_col}_numeric'].sum()
                    breakdown[f'Total_{target_col}'] = summary
                
                breakdown['Cluster'] = cluster
                result_list.append(breakdown.reset_index())
            
            if result_list:
                result = pd.concat(result_list, ignore_index=True)
                return result, "Detailed breakdown completed"
            else:
                return None, "No data to analyze"
        
    except Exception as e:
        return None, f"Analysis error: {str(e)}"
    
    return None, "Unknown analysis type"

#-------------------------filter trade data-------------------
import pandas as pd
import numpy as np

def normalize(s):
    return str(s).strip().lower()

def filter_trade_data(df, trade_type_col, country_col, supplier_col, 
                      selected_trade_type=None, selected_country=None, selected_supplier=None):
    
    print("### 🔎 Selected Filters")
    print(f"- Trade Type: `{selected_trade_type}`")
    print(f"- Importer Country: `{selected_country}`")
    print(f"- Supplier Country: `{selected_supplier}`")

    if selected_trade_type and trade_type_col in df.columns:
        df = df[df[trade_type_col].astype(str).apply(normalize) == normalize(selected_trade_type)]
    if selected_country and country_col in df.columns:
        if "All" not in selected_country:
            normalized_selected = set(normalize(val) for val in selected_country)
            df = df[df[country_col].astype(str).apply(normalize).isin(normalized_selected)]

    if selected_supplier and supplier_col in df.columns:
        if "All" not in selected_supplier:
            normalized_suppliers = set(normalize(val) for val in selected_supplier)
            df = df[df[supplier_col].astype(str).apply(normalize).isin(normalized_suppliers)]

    print(f"Filtered data shape: {df.shape}")
    return df
import re
import numpy as np
import pandas as pd

from data_cleaning import safe_numeric_conversion

def perform_trade_analysis(
    df,
    product_col,                 # keep your original signature
    quantity_col,
    value_col,
    importer_col,
    supplier_col,
    item_description_col=None
):
    results = {}

    # -------------// AUTO-DETECT HELPERS
    def _col_contains(col, kws):
        c = str(col).lower()
        return any(k in c for k in kws)

    # -------------// Heuristic detection of value / quantity / unit-price columns
    def detect_columns(df, value_col, quantity_col):
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        lower_cols = {c.lower(): c for c in df.columns}

        # If provided, trust user but still coerce numeric
        vc = value_col if value_col in df.columns else None
        qc = quantity_col if quantity_col in df.columns else None

        unit_price_candidates = []
        total_value_candidates = []
        quantity_candidates = []

        for c in numeric_cols:
            cl = c.lower()
            if _col_contains(c, ["unit", "rate", "price", "per unit"]):
                unit_price_candidates.append(c)
            if _col_contains(c, ["qty", "quantity", "mt", "mts", "kg", "kgs", "ton", "tons"]):
                quantity_candidates.append(c)
            if _col_contains(c, ["fob", "cif", "assess", "invoice", "value", "val", "amount", "total"]):
                # Avoid misclassifying unit price as value
                if not _col_contains(c, ["unit", "rate", "price"]):
                    total_value_candidates.append(c)

        # If not provided, choose best guess
        if qc is None:
            # prefer an explicitly named quantity column
            if quantity_candidates:
                qc = quantity_candidates[0]
            else:
                # fall back to the smallest-magnitude numeric column as a guess
                qc = min(numeric_cols, key=lambda c: df[c].abs().median()) if numeric_cols else None

        if vc is None:
            # prefer explicit total value candidates
            if total_value_candidates:
                # choose the one with the largest median as it's likely total value
                vc = max(total_value_candidates, key=lambda c: df[c].abs().median())
            else:
                # fallback: pick the largest magnitude numeric col as value
                vc = max(numeric_cols, key=lambda c: df[c].abs().median()) if numeric_cols else None

        # Also track if there's a unit price column
        up = unit_price_candidates[0] if unit_price_candidates else None

        return vc, qc, up
    # -------------// END AUTO-DETECT HELPERS

    try:
        # -------------// RUN DETECTION
        detected_value_col, detected_quantity_col, detected_unit_price_col = detect_columns(df, value_col, quantity_col)

        # -------------// LOG (optional)
        # print(f"[detect] value_col={detected_value_col}, quantity_col={detected_quantity_col}, unit_price_col={detected_unit_price_col}")

        # -------------// Coerce to numeric safely
        if detected_value_col:
            df[detected_value_col] = safe_numeric_conversion(df[detected_value_col])
        if detected_quantity_col:
            df[detected_quantity_col] = safe_numeric_conversion(df[detected_quantity_col])
        if detected_unit_price_col:
            df[detected_unit_price_col] = safe_numeric_conversion(df[detected_unit_price_col])

        # -------------// If what we think is value_col is actually a unit price column, rebuild total value
        # Heuristic: if we have unit_price AND quantity, and value ~= unit_price * quantity (within tolerance),
        # then the detected_value_col is actually a total value. Otherwise, if detected_value_col name suggests unit price, rebuild.
        def is_unit_price_like(col):
            return col is not None and _col_contains(col, ["unit", "rate", "price"])

        if detected_value_col is None and detected_unit_price_col and detected_quantity_col:
            # no value col, but we have unit price & qty -> synthesize
            df["_Total_Value_Synth"] = df[detected_unit_price_col] * df[detected_quantity_col]
            detected_value_col = "_Total_Value_Synth"
        elif is_unit_price_like(detected_value_col) and detected_quantity_col:
            # value col is actually a unit price -> synthesize true total
            df["_Total_Value_Synth"] = df[detected_value_col] * df[detected_quantity_col]
            detected_value_col = "_Total_Value_Synth"

        # guard rails
        if detected_value_col is None or detected_quantity_col is None:
            results["error"] = (
                f"Could not reliably detect value/quantity columns. "
                f"Detected value: {detected_value_col}, quantity: {detected_quantity_col}"
            )
            return results

        # ORIGINAL ANALYSIS (uses detected_* now)
        # ----------------------------------------------------------
        # 1. Which importer is importing the most from a particular supplier for the selected product?
        groupby_cols_1 = [importer_col, supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_1.append(item_description_col)

        most_importing = (
            df.groupby(groupby_cols_1)[detected_value_col]
            .sum()
            .reset_index()
            .sort_values(by=detected_value_col, ascending=False)
            .head(10)
        )
        results["1. Top Importer-Supplier Combinations"] = most_importing.to_dict(orient="records")

        # 2. Top exporting countries for a given product
        groupby_cols_2 = [supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_2.append(item_description_col)

        top_exporting = (
            df.groupby(groupby_cols_2)[detected_value_col]
            .sum()
            .reset_index()
            .sort_values(by=detected_value_col, ascending=False)
            .head(10)
        )
        results["2. Top Exporting Countries"] = top_exporting.to_dict(orient="records")

        # 3. Top importing cities/states by supplier
        groupby_cols_3 = [importer_col, supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_3.append(item_description_col)

        top_importing_cities = (
            df.groupby(groupby_cols_3)[detected_value_col]
            .sum()
            .reset_index()
            .sort_values(by=detected_value_col, ascending=False)
            .head(10)
        )
        results["3. Top Importing Cities/States by Supplier"] = top_importing_cities.to_dict(orient="records")

        # 4. Country dominance
        dominant_export = top_exporting.copy()
        total_export = dominant_export[detected_value_col].sum()
        dominant_export["% Share"] = (dominant_export[detected_value_col] / total_export) * 100 if total_export else 0
        results["4. Export Dominance Share"] = dominant_export.to_dict(orient="records")

        # 5. Highest supplier to importer values
        groupby_cols_5 = [supplier_col, importer_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_5.append(item_description_col)

        top_supplier_to_importer = (
            df.groupby(groupby_cols_5)[detected_value_col]
            .sum()
            .reset_index()
            .sort_values(by=detected_value_col, ascending=False)
            .head(10)
        )
        results["5. Highest Supplier to Importer Values"] = top_supplier_to_importer.to_dict(orient="records")

        # 6. Trend over time (YEAR or Month -> year)
        time_col = None
        if "YEAR" in df.columns:
            time_col = "YEAR"
        elif "Month" in df.columns:
            try:
                df["__year_tmp"] = pd.to_datetime(df["Month"], errors="coerce").dt.year
                time_col = "__year_tmp"
            except Exception:
                pass

        if time_col and df[time_col].notna().any():
            trend_df = (
                df.groupby(time_col)[detected_value_col]
                .sum()
                .reset_index()
                .sort_values(by=time_col)
            )
            trend_df["Change"] = trend_df[detected_value_col].diff()
            trend_df["% Change"] = trend_df[detected_value_col].pct_change() * 100
            results["6. Trade Value Trend Over Time"] = trend_df.to_dict(orient="records")

            if len(trend_df) >= 2:
                first_year = trend_df.iloc[0]
                last_year = trend_df.iloc[-1]
                total_change = last_year[detected_value_col] - first_year[detected_value_col]
                percent_change = (
                    (total_change / first_year[detected_value_col]) * 100
                    if first_year[detected_value_col] != 0 else 0
                )
                direction = "increased" if total_change > 0 else "decreased" if total_change < 0 else "remained stable"
                results["Trend Analysis"] = (
                    f"From {int(first_year[time_col])} to {int(last_year[time_col])}, "
                    f"trade value has {direction} by {percent_change:.1f}% "
                    f"(from {first_year[detected_value_col]:,.0f} to {last_year[detected_value_col]:,.0f})"
                )

        # 7. Highest / Lowest Avg Value per Unit
        if detected_quantity_col in df.columns:
            df_clean = df[df[detected_quantity_col] > 0].copy()
            df_clean["Unit_Value"] = df_clean[detected_value_col] / df_clean[detected_quantity_col]  # -------------//
            groupby_cols_unit = [supplier_col, importer_col]
            if item_description_col and item_description_col in df.columns:
                groupby_cols_unit.append(item_description_col)

            avg_unit_value = (
                df_clean.groupby(groupby_cols_unit)["Unit_Value"]
                .mean()
                .reset_index()
                .dropna(subset=["Unit_Value"])
            )

            if not avg_unit_value.empty:
                results["7A. Highest Avg Value per Unit"] = (
                    avg_unit_value.sort_values(by="Unit_Value", ascending=False).head(5).to_dict(orient="records")
                )
                results["7B. Lowest Avg Value per Unit"] = (
                    avg_unit_value.sort_values(by="Unit_Value", ascending=True).head(5).to_dict(orient="records")
                )

        # 8. Heatmap data
        groupby_cols_heatmap = [importer_col, supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_heatmap.append(item_description_col)

        heatmap_data = (
            df.groupby(groupby_cols_heatmap)[detected_value_col]
            .sum()
            .reset_index()
        )

        top_importers = (
            df.groupby(importer_col)[detected_value_col]
            .sum()
            .nlargest(10)
            .index
        )
        top_suppliers = (
            df.groupby(supplier_col)[detected_value_col]
            .sum()
            .nlargest(10)
            .index
        )

        heatmap_filtered = heatmap_data[
            (heatmap_data[importer_col].isin(top_importers)) &
            (heatmap_data[supplier_col].isin(top_suppliers))
        ]

        if not heatmap_filtered.empty:
            if item_description_col and item_description_col in df.columns:
                heatmap_for_pivot = (
                    heatmap_filtered.groupby([importer_col, supplier_col])[detected_value_col]
                    .sum()
                    .reset_index()
                )
            else:
                heatmap_for_pivot = heatmap_filtered

            heatmap_pivot = (
                heatmap_for_pivot.pivot(index=importer_col, columns=supplier_col, values=detected_value_col)
                .fillna(0)
                .reset_index()
            )
            results["8. Importer-Supplier Heatmap Data"] = heatmap_pivot.to_dict(orient="records")

    except Exception as e:
        results["error"] = f"Trade analysis failed: {str(e)}"

    return results


def analyze_trend(df, trade_type, product_name, selected_years):
    """
    Analyze trend in trade value for a selected product across years.
    Updated to use your column structure.
    """
    try:
        # Check if required columns exist
        if "Item_Description" not in df.columns or "CTH_HSCODE" not in df.columns:
            return "Required columns (Item_Description, CTH_HSCODE) not found in data"

        # Determine year column
        time_col = None
        if "YEAR" in df.columns:
            time_col = "YEAR"
        elif "Month" in df.columns:
            try:
                df["year_temp"] = pd.to_datetime(df["Month"], errors="coerce").dt.year
                time_col = "year_temp"
            except:
                return "Unable to extract year from Month column"

        if not time_col:
            return "No valid year column found"

        # Use your actual column names
        item_col = "Item_Description"
        trade_col = "Type"
        value_col = df.select_dtypes(include="number").columns[0]  # First numeric column

        # Filter data
        filtered = df[
            (df[trade_col].str.lower() == trade_type.lower()) &
            (df[item_col].str.lower() == product_name.lower()) &
            (df[time_col].isin(selected_years))
        ]

        if filtered.empty or len(filtered[time_col].unique()) < 2:
            return "Insufficient data for trend analysis"

        # Calculate trend
        trend = filtered.groupby(time_col)[value_col].sum().reset_index()
        trend = trend.sort_values(by=time_col)

        y1, y2 = int(trend.iloc[0][time_col]), int(trend.iloc[-1][time_col])
        v1, v2 = trend.iloc[0][value_col], trend.iloc[-1][value_col]

        if v2 > v1:
            status = "increased"
        elif v2 < v1:
            status = "decreased"
        else:
            status = "remained constant"

        change = v2 - v1
        percent = (change / v1) * 100 if v1 != 0 else 0
        
        return f"From {y1} to {y2}, the trade value has **{status}** from **{v1:,.0f}** to **{v2:,.0f}** (change: {percent:.2f}%)."

    except Exception as e:
        return f"Trend analysis failed: {e}"


#-------------forecasting functions----------------
def get_fy(date):
    if pd.isnull(date): return None
    if date.month <= 3:
        return f"FY {date.year - 1}-{str(date.year)[-2:]}"
    else:
        return f"FY {date.year}-{str(date.year + 1)[-2:]}"


def full_periodic_analysis(df, date_col, value_col):
    if date_col not in df.columns or value_col not in df.columns:
        return None, "Required columns not found"

    df_clean = df.copy()
    df_clean["_numeric"] = safe_numeric_conversion(df_clean[value_col])

    df_clean["Parsed_Date"] = pd.to_datetime(df_clean[date_col], errors="coerce")
    df_clean.dropna(subset=["Parsed_Date"], inplace=True)

    df_clean["Month_Period"] = df_clean["Parsed_Date"].dt.to_period("M").astype(str)
    df_clean["Quarter"] = df_clean["Parsed_Date"].dt.to_period("Q").astype(str)
    df_clean["Calendar Year"] = df_clean["Parsed_Date"].dt.year.astype(str)
    df_clean["Financial Year"] = df_clean["Parsed_Date"].apply(get_fy)

    monthly_avg = df_clean.groupby("Month_Period")["_numeric"].mean().reset_index(name="Monthly Avg")
    quarterly_avg = df_clean.groupby("Quarter")["_numeric"].mean().reset_index(name="Quarterly Avg")
    fy_avg = df_clean.groupby("Financial Year")["_numeric"].mean().reset_index(name="FY Avg")
    cy_avg = df_clean.groupby("Calendar Year")["_numeric"].mean().reset_index(name="CY Avg")

    return {
        "Monthly Average": monthly_avg,
        "Quarterly Average": quarterly_avg,
        "Financial Year Average": fy_avg,
        "Calendar Year Average": cy_avg
    }," All time-based averages computed"


def analyze_trend(df, trade_type, product_name, selected_years):
    df_filtered = df[
        (df["Type"] == trade_type) &
        (df["Item_Description"] == product_name) &
        (df["YEAR"].isin(selected_years))
    ]

    if len(selected_years) < 2:
        return "Please select at least two years to perform trend analysis."

    years_sorted = sorted(selected_years)
    year1, year2 = years_sorted[0], years_sorted[-1]

    q1 = df_filtered[df_filtered["YEAR"] == year1]["Quantity"].sum()
    q2 = df_filtered[df_filtered["YEAR"] == year2]["Quantity"].sum()
    diff = q2 - q1

    trend = "increased" if diff > 0 else "decreased"
    trend_type = "growing" if diff > 0 else "declining"

    result = (
        f"From {year1} to {year2}, {trade_type.lower()}s have {trend} by {abs(diff):,.0f} units, "
        f"indicating a {trend_type} trend for the product '{product_name}'.\n\n"
        f"It was {q1:,.0f} units in {year1} and {q2:,.0f} units in {year2}, "
        f"hence it is {trend}."
    )
    return result

#------------------comparative analysis-------------------
def comparative_analysis(df, selected_years, time_period_type, selected_quarter_or_month, selected_hscode, selected_item, quantity_col='Quantity', month_col='Month'):
    import pandas as pd

    # Convert "Month" column to datetime
    df[month_col] = pd.to_datetime(df[month_col], errors='coerce')

    # Extract year and month/quarter
    df['year'] = df[month_col].dt.year
    df['month_num'] = df[month_col].dt.month
    df['quarter'] = df[month_col].dt.quarter

    # Step 1: Filter by selected years
    df_filtered = df[df['year'].isin(selected_years)]

    # Step 2: Filter by time period
    if time_period_type.lower() == 'quarter':
        if selected_quarter_or_month.upper() != 'ALL':
            quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
            selected_q = quarter_map.get(selected_quarter_or_month.upper())
            if selected_q is not None:
                df_filtered = df_filtered[df_filtered['quarter'] == selected_q]

    elif time_period_type.lower() == 'month':
        month_map = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                     'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
        selected_m = month_map[selected_quarter_or_month.upper()]
        df_filtered = df_filtered[df_filtered['month_num'] == selected_m]

    # Step 3: Filter by HS Code and Item Description
    df_filtered = df_filtered[
        (df_filtered['CTH_HSCODE'] == selected_hscode) &
        (df_filtered['Item_Description'] == selected_item)
    ]

    # Step 4: Aggregate quantities by year
    result = df_filtered.groupby('year')[quantity_col].sum().reset_index()

    return result
