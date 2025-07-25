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

# *//// CHANGE: Updated function signature to accept item_description_col parameter
def perform_trade_analysis(df, product_col, quantity_col, value_col, importer_col, supplier_col, item_description_col=None):
    results = {}

    try:
        # *//// CHANGE: Define columns to include in groupby operations
        base_groupby_cols = [importer_col, supplier_col]
        if item_description_col and item_description_col in df.columns:
            base_groupby_cols.append(item_description_col)

        # 1. Which importer is importing the most from a particular supplier for the selected product?
        # *//// CHANGE: Include item_description_col in groupby
        groupby_cols_1 = [importer_col, supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_1.append(item_description_col)
        
        most_importing = df.groupby(groupby_cols_1)[value_col].sum().reset_index()
        most_importing = most_importing.sort_values(by=value_col, ascending=False).head(10)
        results["1. Top Importer-Supplier Combinations"] = most_importing.to_dict(orient="records")

        # 2. What are the top countries exporting for a given product?
        # *//// CHANGE: Include item_description_col in groupby if available
        groupby_cols_2 = [supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_2.append(item_description_col)
        
        top_exporting = df.groupby(groupby_cols_2)[value_col].sum().reset_index()
        top_exporting = top_exporting.sort_values(by=value_col, ascending=False).head(10)
        results["2. Top Exporting Countries"] = top_exporting.to_dict(orient="records")

        # 3. What are the top importing cities/states for a given product from a supplier country?
        # *//// CHANGE: Include item_description_col in groupby
        groupby_cols_3 = [importer_col, supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_3.append(item_description_col)
        
        top_importing_cities = df.groupby(groupby_cols_3)[value_col].sum().reset_index()
        top_importing_cities = top_importing_cities.sort_values(by=value_col, ascending=False).head(10)
        results["3. Top Importing Cities/States by Supplier"] = top_importing_cities.to_dict(orient="records")

        # 4. Is there any country that dominates in export of selected product?
        dominant_export = top_exporting.copy()
        total_export = dominant_export[value_col].sum()
        dominant_export["% Share"] = (dominant_export[value_col] / total_export) * 100
        results["4. Export Dominance Share"] = dominant_export.to_dict(orient="records")

        # 5. Which supplier country is sending the highest value of the product to particular importer?
        # *//// CHANGE: Include item_description_col in groupby
        groupby_cols_5 = [supplier_col, importer_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_5.append(item_description_col)
        
        top_supplier_to_importer = df.groupby(groupby_cols_5)[value_col].sum().reset_index()
        top_supplier_to_importer = top_supplier_to_importer.sort_values(by=value_col, ascending=False).head(10)
        results["5. Highest Supplier to Importer Values"] = top_supplier_to_importer.to_dict(orient="records")

        # 6. Has the trade value increased or decreased over time?
        time_col = None
        if "YEAR" in df.columns:
            time_col = "YEAR"
        elif "Month" in df.columns:
            try:
                df["year_temp"] = pd.to_datetime(df["Month"], errors="coerce").dt.year
                time_col = "year_temp"
            except:
                pass

        if time_col and df[time_col].notna().any():
            # *//// CHANGE: Include item_description_col in time trend groupby if available
            groupby_cols_time = [time_col]
            if item_description_col and item_description_col in df.columns:
                # For time analysis, we might want to aggregate across all items or keep item breakdown
                # Let's keep it simple and aggregate across all items for trend
                pass
            
            trend_df = df.groupby(time_col)[value_col].sum().reset_index()
            trend_df = trend_df.sort_values(by=time_col)
            trend_df["Change"] = trend_df[value_col].diff()
            trend_df["% Change"] = trend_df[value_col].pct_change() * 100
            results["6. Trade Value Trend Over Time"] = trend_df.to_dict(orient="records")
            
            # Add trend analysis summary
            if len(trend_df) >= 2:
                first_year = trend_df.iloc[0]
                last_year = trend_df.iloc[-1]
                total_change = last_year[value_col] - first_year[value_col]
                percent_change = ((last_year[value_col] - first_year[value_col]) / first_year[value_col]) * 100 if first_year[value_col] != 0 else 0
                
                trend_direction = "increased" if total_change > 0 else "decreased" if total_change < 0 else "remained stable"
                results["Trend Analysis"] = f"From {int(first_year[time_col])} to {int(last_year[time_col])}, trade value has {trend_direction} by {percent_change:.1f}% (from {first_year[value_col]:,.0f} to {last_year[value_col]:,.0f})"

        # 7. Which supplier country is giving the lowest/highest average value per unit?
       # if quantity_col and quantity_col in df.columns:
            # Clean quantity data - remove zeros and negatives
        #    df_clean = df[df[quantity_col] > 0].copy()
         #   df_clean["Unit_Value"] = df_clean[value_col] / df_clean[quantity_col]
            
         #   if not df_clean.empty:
                # *//// CHANGE: Include item_description_col in unit value groupby
           #     groupby_cols_unit = [supplier_col, importer_col]
           #     if item_description_col and item_description_col in df.columns:
             #       groupby_cols_unit.append(item_description_col)
                
             #   avg_unit_value = df_clean.groupby(groupby_cols_unit)["Unit_Value"].mean().reset_index()
             #   avg_unit_value = avg_unit_value[avg_unit_value["Unit_Value"].notna()]
                
               # if not avg_unit_value.empty:
               #     highest_avg = avg_unit_value.sort_values(by="Unit_Value", ascending=False).head(5)
                 #   lowest_avg = avg_unit_value.sort_values(by="Unit_Value", ascending=True).head(5)
                 #   results["7A. Highest Avg Value per Unit"] = highest_avg.to_dict(orient="records")
                  #  results["7B. Lowest Avg Value per Unit"] = lowest_avg.to_dict(orient="records")

        # 8. Heatmap: Importer/supplier pairs with highest trade value
        # *//// CHANGE: Include item_description_col in heatmap groupby
        groupby_cols_heatmap = [importer_col, supplier_col]
        if item_description_col and item_description_col in df.columns:
            groupby_cols_heatmap.append(item_description_col)
        
        heatmap_data = df.groupby(groupby_cols_heatmap)[value_col].sum().reset_index()
        
        # Limit to top importers and suppliers to make heatmap manageable
        top_importers = df.groupby(importer_col)[value_col].sum().nlargest(10).index
        top_suppliers = df.groupby(supplier_col)[value_col].sum().nlargest(10).index
        
        heatmap_filtered = heatmap_data[
            (heatmap_data[importer_col].isin(top_importers)) & 
            (heatmap_data[supplier_col].isin(top_suppliers))
        ]
        
        if not heatmap_filtered.empty:
            # *//// CHANGE: For heatmap, if we have item descriptions, we might want to aggregate them
            # or create a more complex pivot. For now, let's aggregate by importer-supplier pairs
            if item_description_col and item_description_col in df.columns:
                # Aggregate item descriptions for heatmap (sum values across items)
                heatmap_for_pivot = heatmap_filtered.groupby([importer_col, supplier_col])[value_col].sum().reset_index()
            else:
                heatmap_for_pivot = heatmap_filtered
            
            heatmap_pivot = heatmap_for_pivot.pivot(
                index=importer_col, 
                columns=supplier_col, 
                values=value_col
            ).fillna(0)
            results["8. Importer-Supplier Heatmap Data"] = heatmap_pivot.reset_index().to_dict(orient="records")

    except Exception as e:
        results["error"] = f"Trade analysis failed: {str(e)}"
        print(f"Analysis error: {str(e)}")

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
