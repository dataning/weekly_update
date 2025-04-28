# treemap_component.py
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from jinja2 import Template
import json
import logging # Optional: for better debugging

# Configure logging (optional)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TreemapComponent:
    """
    A reusable hierarchical treemap component for Streamlit using Highcharts.

    Supports a three-level hierarchy. Box sizes can be determined either by
    item count or by a specified numeric column. Box colors are determined
    by a separate numeric performance/value column.
    """

    def __init__(self, title="Hierarchical Performance Treemap", subtitle="Click to drill down"):
        """
        Initialize the treemap component.

        Parameters:
        -----------
        title : str
            Chart title.
        subtitle : str
            Chart subtitle.
        """
        self.title = title
        self.subtitle = subtitle
        self.js_template = self._get_default_js_template()
        self.html_template = self._get_default_html_template()

    def _numpy_safe_encoder(self, obj):
        """Convert NumPy types to native Python types for JSON."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            if np.isnan(obj):
                return None # Use None for JSON null
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj): # Handle pandas NAs as well
             return None # Use None for JSON null
        else:
            # Handle potential non-serializable types gracefully
            try:
                 # Attempt a default conversion, might raise TypeError for unsupported types
                 json.dumps(obj)
                 return obj
            except TypeError:
                 # Log or handle the non-serializable type
                 logging.warning(f"Object of type {type(obj)} is not JSON serializable, converting to string.")
                 return str(obj) # Fallback to string representation


    def create_treemap_data(self, df, level1_column, level2_column, level3_column,
                            value_column, size_column=None, auto_scale_percentage=False,
                            fill_hierarchy_na="Unknown"):
        """
        Creates the hierarchical data structure for the Highcharts treemap.
        (Implementation unchanged from previous correct version)
        """
        treemap_data = []
        df_processed = df.copy() # Work on a copy

        # --- Pre-calculate Sizes ---
        if size_column:
            df_processed[size_column] = pd.to_numeric(df_processed[size_column], errors='coerce').fillna(1.0)
            if (df_processed[size_column] <= 0).any():
                 logging.warning(f"Size column '{size_column}' contains non-positive values. Replacing with 1.0.")
                 df_processed.loc[df_processed[size_column] <= 0, size_column] = 1.0 # Use .loc for assignment

            level1_sizes = df_processed.groupby(level1_column)[size_column].sum().to_dict()
            level2_sizes = df_processed.groupby([level1_column, level2_column])[size_column].sum().to_dict()
        else:
            level1_sizes = df_processed[level1_column].value_counts().to_dict()
            level2_group_sizes = df_processed.groupby([level1_column, level2_column]).size()
            level2_sizes = level2_group_sizes.to_dict()

        # --- Calculate Average Values (for color) ---
        df_processed[value_column] = pd.to_numeric(df_processed[value_column], errors='coerce')
        level1_avg_values = df_processed.groupby(level1_column)[value_column].mean(numeric_only=True).to_dict()
        level2_avg_values = df_processed.groupby([level1_column, level2_column])[value_column].mean(numeric_only=True).to_dict()

        # --- Build Treemap Structure ---
        unique_level1 = df_processed[level1_column].unique()
        existing_node_ids = set() # Keep track of all generated IDs

        # Level 1 Nodes
        for level1 in unique_level1:
            node_id = str(level1) # Ensure ID is string
            if node_id in existing_node_ids:
                 logging.warning(f"Duplicate Level 1 ID '{node_id}' encountered. This might cause issues.")
                 # Consider modifying ID if duplicates are possible and problematic: node_id = f"L1_{node_id}"
            existing_node_ids.add(node_id)

            size = float(level1_sizes.get(level1, 1.0))
            raw_value = level1_avg_values.get(level1, float('nan'))
            is_nan = pd.isna(raw_value)
            color_value = float('nan') if is_nan else float(raw_value)

            if not is_nan and auto_scale_percentage and -1 <= color_value <= 1:
                color_value *= 100

            treemap_data.append({
                "id": node_id,
                "name": str(level1), # Ensure name is string
                "value": size,
                "colorValue": color_value,
                "custom": {
                    "fullName": str(level1),
                    "performance_value": color_value,
                    "isNaN": is_nan
                 }
            })

        # Level 2 Nodes
        unique_level2_pairs = df_processed[[level1_column, level2_column]].drop_duplicates().to_records(index=False)
        for level1, level2 in unique_level2_pairs:
            parent_id = str(level1)
            node_id = f"{parent_id}|{level2}" # Use string representation of level2
            if node_id in existing_node_ids:
                 logging.warning(f"Duplicate Level 2 ID '{node_id}' encountered. Appending suffix.")
                 counter = 1
                 new_node_id = f"{node_id}_{counter}"
                 while new_node_id in existing_node_ids:
                     counter += 1
                     new_node_id = f"{node_id}_{counter}"
                 node_id = new_node_id # Use the unique suffixed ID
            existing_node_ids.add(node_id)

            size_key = (level1, level2)
            value_key = (level1, level2)
            size = float(level2_sizes.get(size_key, 1.0))
            raw_value = level2_avg_values.get(value_key, float('nan'))
            is_nan = pd.isna(raw_value)
            color_value = float('nan') if is_nan else float(raw_value)

            if not is_nan and auto_scale_percentage and -1 <= color_value <= 1:
                color_value *= 100

            treemap_data.append({
                "id": node_id,
                "name": str(level2), # Ensure name is string
                "parent": parent_id,
                "value": size,
                "colorValue": color_value,
                "custom": {
                    "fullName": str(level2),
                    "performance_value": color_value,
                    "isNaN": is_nan
                 }
            })

        # Level 3 Nodes (Leaf Nodes)
        for _, row in df_processed.iterrows():
            level1_val = row[level1_column]
            level2_val = row[level2_column]
            level3_val = row[level3_column]
            value = row[value_column]
            size = float(row[size_column]) if size_column else 1.0

            # Find the potentially suffixed parent ID created above
            parent_base_id = f"{level1_val}|{level2_val}"
            parent_id = parent_base_id
            counter = 1
            while parent_id != parent_base_id and parent_id not in existing_node_ids: # Search for suffixed parent if base ID not found (should not happen often)
                 parent_id = f"{parent_base_id}_{counter}"
                 counter += 1
                 if counter > 100: # Safety break
                      logging.error(f"Could not find parent ID for base {parent_base_id}")
                      parent_id = parent_base_id # Fallback
                      break

            node_base_id = f"{parent_id}|{level3_val}" # Base ID for level 3
            node_id = node_base_id
            counter = 1
            while node_id in existing_node_ids: # Ensure unique leaf ID
                # logging.warning(f"Duplicate leaf ID detected: {node_base_id}. Appending suffix.")
                node_id = f"{node_base_id}_{counter}"
                counter += 1
            existing_node_ids.add(node_id)

            is_nan = pd.isna(value)
            color_value = float('nan') if is_nan else float(value)
            performance_text = "N/A"

            if not is_nan:
                 scaled_value = color_value
                 if auto_scale_percentage and -1 <= color_value <= 1:
                     scaled_value *= 100
                 color_value = scaled_value
                 sign = "+" if color_value >= 0 else ""
                 performance_text = f"{sign}{color_value:.2f}%"

            treemap_data.append({
                "id": node_id,
                "name": str(level3_val), # Ensure name is string
                "parent": parent_id,
                "value": size,
                "colorValue": color_value,
                "custom": {
                    "fullName": str(level3_val),
                    "performance": performance_text,
                    "performance_value": color_value,
                    "isNaN": is_nan
                }
            })

        return treemap_data


    def render(self, df, level1_column, level2_column, level3_column, value_column,
               size_column=None, height=800, value_min=-30, value_max=30,
               color_min='#d40000', color_max='#00b52a', validate_data=True,
               nan_color='#333333', nan_label='N/A', handle_nan='show',
               auto_scale_percentage=False, fill_hierarchy_na="Unknown"):
        """
        Renders the hierarchical treemap in Streamlit.
        (Implementation unchanged from previous correct version)
        """
         # --- Input Validation ---
        if not isinstance(df, pd.DataFrame):
            st.error("Input 'df' must be a pandas DataFrame.")
            return
        if df.empty:
            st.warning("Input DataFrame is empty. Cannot render treemap.")
            return

        required_columns = [level1_column, level2_column, level3_column, value_column]
        if size_column:
            required_columns.append(size_column)

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns in DataFrame: {', '.join(missing_cols)}")
            return

        # Attempt to convert value_column to numeric early
        try:
            if not pd.api.types.is_numeric_dtype(df[value_column]):
                 logging.info(f"Attempting conversion of value column '{value_column}' to numeric.")
                 df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
            # Check after conversion if it's still not numeric (means errors='coerce' produced all NaNs or failed)
            if not pd.api.types.is_numeric_dtype(df[value_column].dropna()):
                 st.error(f"Value column '{value_column}' could not be reliably converted to numeric. Please check data type.")
                 return
        except KeyError:
            st.error(f"Value column '{value_column}' not found in DataFrame.")
            return
        except Exception as e:
            st.error(f"Error processing value column '{value_column}': {e}")
            return

        # Attempt to convert size_column to numeric early if provided
        if size_column:
            try:
                if not pd.api.types.is_numeric_dtype(df[size_column]):
                    logging.info(f"Attempting conversion of size column '{size_column}' to numeric.")
                    df[size_column] = pd.to_numeric(df[size_column], errors='coerce')
                # Check after conversion
                if not pd.api.types.is_numeric_dtype(df[size_column].dropna()):
                    st.warning(f"Size column '{size_column}' could not be reliably converted to numeric. It may contain only NaNs or non-numeric values. Sizes might default to 1.")
                    # If handle_nan is hide, these rows might be dropped later anyway
            except KeyError:
                 st.error(f"Size column '{size_column}' not found in DataFrame.")
                 return
            except Exception as e:
                 st.error(f"Error processing size column '{size_column}': {e}")
                 return


        # --- Data Preparation ---
        df_copy = df[required_columns].copy()

        # Handle NaNs in hierarchy columns
        hierarchy_cols = [level1_column, level2_column, level3_column]
        for col in hierarchy_cols:
            if col in df_copy.columns:
                 # Convert to string first to handle mixed types gracefully before fillna
                 df_copy[col] = df_copy[col].astype(str).fillna(fill_hierarchy_na).replace('', fill_hierarchy_na)
            else:
                 st.error(f"Hierarchy column '{col}' not found after copy. This should not happen.")
                 return

        # Handle NaNs in value column based on user choice
        original_rows = len(df_copy)
        value_nan_mask = df_copy[value_column].isna()
        rows_before_hide = len(df_copy)

        if handle_nan == 'hide':
            df_copy = df_copy.dropna(subset=[value_column])
            rows_after_hide = len(df_copy)
            if validate_data and rows_before_hide > rows_after_hide:
                 st.write(f"Removed {rows_before_hide - rows_after_hide} rows due to NaN in '{value_column}'.")
        elif handle_nan == 'zero':
            nan_count = value_nan_mask.sum()
            if nan_count > 0:
                df_copy.loc[value_nan_mask, value_column] = 0 # Use .loc for assignment
                if validate_data:
                     st.write(f"Replaced {nan_count} NaN values in '{value_column}' with 0.")
        # else 'show', NaNs are kept and handled during data creation/JS

        # Handle NaNs/negatives in size column (AFTER potential row removal by handle_nan='hide')
        if size_column and size_column in df_copy.columns:
             size_nan_mask = df_copy[size_column].isna()
             nan_size_count = size_nan_mask.sum()
             if nan_size_count > 0:
                  # Fill NaNs with 1 for visibility (unless row was already hidden)
                  df_copy.loc[size_nan_mask, size_column] = 1.0
                  if validate_data:
                      st.write(f"Replaced {nan_size_count} NaN values in size column '{size_column}' with 1.0.")

             # Ensure positivity after fillna
             non_positive_mask = (df_copy[size_column] <= 0)
             non_positive_count = non_positive_mask.sum()
             if non_positive_count > 0:
                 df_copy.loc[non_positive_mask, size_column] = 1.0
                 if validate_data:
                      st.write(f"Replaced {non_positive_count} non-positive values in size column '{size_column}' with 1.0.")

        if df_copy.empty:
             st.warning("DataFrame is empty after handling NaNs. Cannot render treemap.")
             return

        # --- Create Treemap Data ---
        try:
            treemap_data = self.create_treemap_data(
                df_copy, level1_column, level2_column, level3_column, value_column,
                size_column, auto_scale_percentage, fill_hierarchy_na
            )
        except Exception as e:
            st.error(f"Error creating treemap data: {e}")
            logging.exception("Treemap data creation failed.")
            return

        # Serialize data safely
        try:
            # Use the numpy_safe_encoder which now handles NaNs correctly -> None
            treemap_data_json = json.dumps(treemap_data, default=self._numpy_safe_encoder)
            # Replacements are likely unnecessary if encoder maps NaN to None, but keep as safety net
            treemap_data_json = (
                treemap_data_json
                .replace(': true', ': true')
                .replace(': false', ': false')
                # .replace(': NaN', ': null') # Should be handled by encoder
                # .replace(': Infinity', ': null') # Should be handled by encoder
                # .replace(': -Infinity', ': null') # Should be handled by encoder
                .replace('NaN', 'null') # Catchall for string "NaN" just in case
            )
        except Exception as e:
            st.error(f"Error serializing treemap data to JSON: {e}")
            logging.exception("JSON serialization failed.")
            return

        # --- Validation (Optional) ---
        if validate_data:
            self._validate_treemap_data(df_copy, value_column, treemap_data, handle_nan, size_column, nan_label)


        # --- Render Chart ---
        chart_settings = {
            'title': self.title,
            'subtitle': self.subtitle,
            'value_min': float(value_min),
            'value_max': float(value_max),
            'color_min': color_min,
            'color_max': color_max,
            'nan_color': nan_color, # Pass the color value
            'nan_label': nan_label, # Pass the label value
            'has_size_column': bool(size_column)
        }

        try:
            js_with_settings = self._customize_js(chart_settings)
            html = Template(self.html_template).render(
                CHART_JS=js_with_settings,
                TREE_DATA_JSON=treemap_data_json
            )
            components.html(html, height=height, scrolling=True)
        except Exception as e:
            st.error(f"Error rendering HTML/JS: {e}")
            logging.exception("HTML/JS rendering failed.")

    # --- Validation Method ---
    def _validate_treemap_data(self, df_processed, value_column, treemap_data, handle_nan, size_column, nan_label_setting):
        """Validates treemap data against the processed source dataframe."""
        # (Implementation unchanged from previous correct version)
        st.subheader("Data Validation")
        try:
            source_rows = len(df_processed)
            # Correctly identify leaf nodes (level 3) based on parent structure
            leaf_nodes = [node for node in treemap_data if node.get('parent', '').count('|') == 1]
            leaf_total = len(leaf_nodes)

            if source_rows != leaf_total:
                st.warning(f"Row count mismatch: Processed DataFrame has {source_rows} rows, but Treemap has {leaf_total} leaf nodes. This might indicate issues with unique ID generation or filtering.")
            else:
                st.success(f"Row count matches: Processed DataFrame ({source_rows}) and Treemap leaf nodes ({leaf_total}).")

            # Value checks (consider handle_nan='zero')
            if handle_nan == 'zero':
                source_negatives = (df_processed[value_column] < 0).sum()
                source_nan = 0 # They were replaced
            else:
                 source_negatives = (df_processed[value_column] < 0).sum() # NaN is not < 0
                 source_nan = df_processed[value_column].isna().sum()

            source_total = len(df_processed) if len(df_processed)>0 else 1 # Avoid division by zero
            source_negative_pct = (source_negatives / source_total) * 100
            source_nan_pct = (source_nan / source_total) * 100


            # Use colorValue and isNaN flag from treemap data
            leaf_negatives = sum(1 for node in leaf_nodes if node.get('colorValue') is not None and node.get('colorValue') < 0)
            leaf_nan = sum(1 for node in leaf_nodes if node.get('custom', {}).get('isNaN', False) or node.get('colorValue') is None) # Check custom flag or if colorValue ended up null
            leaf_total_safe = leaf_total if leaf_total > 0 else 1 # Avoid division by zero
            leaf_negative_pct = (leaf_negatives / leaf_total_safe) * 100
            leaf_nan_pct = (leaf_nan / leaf_total_safe) * 100

            # Display counts and percentages
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Processed DF: {source_negatives} negative ({source_negative_pct:.1f}%)")
                if handle_nan != 'zero':
                    st.info(f"Processed DF: {source_nan} NaN ({source_nan_pct:.1f}%)")
                else:
                    st.info("Processed DF: NaNs replaced with 0")
            with col2:
                st.info(f"Treemap Leaves: {leaf_negatives} negative ({leaf_negative_pct:.1f}%)")
                st.info(f"Treemap Leaves: {leaf_nan} NaN ({leaf_nan_pct:.1f}%)")


            # Size check (if applicable)
            if size_column and size_column in df_processed.columns:
                 total_source_size = df_processed[size_column].sum()
                 total_leaf_size = sum(node.get('value', 0) for node in leaf_nodes if node.get('value') is not None) # Sum only non-null values
                 if not np.isclose(total_source_size, total_leaf_size):
                      st.warning(f"Total size mismatch: Source '{size_column}' sums to {total_source_size:.2f}, Treemap leaves sum to {total_leaf_size:.2f}. Check NaN/negative handling in size column.")
                 else:
                      st.success(f"Total size matches: Source and Treemap leaves sum to approx {total_leaf_size:.2f}.")


            # Value vs. Display Text Check
            discrepancies = []
            for node in leaf_nodes:
                is_nan_node = node.get('custom', {}).get('isNaN', False) or node.get('colorValue') is None
                value = node.get('colorValue') # Can be float or None
                performance = node.get('custom', {}).get('performance', '')

                if is_nan_node:
                    # Check if the performance text matches the expected NaN label
                    if performance != nan_label_setting:
                        discrepancies.append({'id': node.get('id', ''), 'value': 'NaN/Null', 'performance': performance, 'expected_nan': nan_label_setting, 'issue': "NaN display text mismatch"})
                    continue # Skip further checks for NaN

                # If not NaN, value should be a float
                if value is None: # Should not happen if is_nan_node is False, but check anyway
                    discrepancies.append({'id': node.get('id', ''), 'value': 'None', 'performance': performance, 'issue': "Value missing for non-NaN node"})
                    continue

                # Extract numeric value from performance string robustly
                try:
                     perf_num_str = performance.strip().replace('%', '').replace('+', '')
                     perf_value = float(perf_num_str)
                except ValueError:
                     # Allow for '0.00%' case when handle_nan='zero' resulted in 0
                     if handle_nan == 'zero' and np.isclose(value, 0) and performance == '0.00%':
                          continue # This is expected
                     discrepancies.append({'id': node.get('id', ''), 'value': value, 'performance': performance, 'issue': "Cannot parse performance text"})
                     continue

                # Check sign and value (use tolerance for float comparison)
                if not np.isclose(value, perf_value, atol=0.01): # Tolerance of 0.01%
                    if np.isclose(abs(value), abs(perf_value), atol=0.01):
                         discrepancies.append({'id': node.get('id', ''), 'value': f"{value:.3f}", 'performance': performance, 'parsed_perf': f"{perf_value:.3f}", 'issue': "Sign mismatch"})
                    else:
                         discrepancies.append({'id': node.get('id', ''), 'value': f"{value:.3f}", 'performance': performance, 'parsed_perf': f"{perf_value:.3f}", 'issue': "Value mismatch"})

            if discrepancies:
                st.warning(f"Found {len(discrepancies)} potential discrepancies in leaf nodes:")
                st.dataframe(pd.DataFrame(discrepancies))
            else:
                st.success("Leaf node values and display text appear consistent.")

        except Exception as e:
            st.error(f"Error during validation: {e}")
            logging.exception("Validation failed.")

        # Display sample nodes
        with st.expander("View Sample Treemap Leaf Nodes"):
            sample_size = min(5, len(leaf_nodes))
            st.write(leaf_nodes[:sample_size])

    # --- JS/HTML Templates ---
    def _customize_js(self, settings):
        """Customize the JavaScript with provided settings"""
        js = self.js_template
        js = js.replace('__CHART_TITLE__', json.dumps(settings['title']))
        js = js.replace('__CHART_SUBTITLE__', json.dumps(settings['subtitle']))
        # These are used inside JS strings, so direct replacement is fine
        js = js.replace('__COLOR_MIN__', settings['color_min'])
        js = js.replace('__COLOR_MAX__', settings['color_max'])
        # These are used as JS numbers
        js = js.replace('__VALUE_MIN__', str(settings['value_min']))
        js = js.replace('__VALUE_MAX__', str(settings['value_max']))
        # **FIX:** Use json.dumps for nan_color and nan_label to ensure they are valid JS strings
        js = js.replace('__NAN_COLOR__', json.dumps(settings['nan_color']))
        js = js.replace('__NAN_LABEL__', json.dumps(settings['nan_label']))
        # Used as boolean
        js = js.replace('__HAS_SIZE_COLUMN__', 'true' if settings['has_size_column'] else 'false')
        return js

    def _get_default_js_template(self):
        """Returns the default JavaScript template for the treemap chart"""
        # (JS template unchanged from previous correct version)
        return """
const renderChart = data => {
    // Log data to check formatting just before rendering
    // console.log('Rendering treemap data:', data); // Uncomment for debugging

    const hasSizeColumn = __HAS_SIZE_COLUMN__; // Get info from Python

    Highcharts.chart('container', {
      chart: {
        backgroundColor: '#252931',
        spacing: [10, 10, 0, 10],
        spacingBottom: 0,
        marginTop: 60,
        marginRight: 20,
      },

      credits: { enabled: false },

      series: [{
        name: 'All',
        type: 'treemap',
        layoutAlgorithm: 'squarified',
        allowDrillToNode: true,
        animationLimit: 1000,
        borderColor: '#252931',
        borderWidth: 1, // Slightly visible border
        // color: '#252931', // Let colorAxis handle colors based on colorValue
        colorKey: 'colorValue',  // Use colorValue for coloring nodes
        // nodeSizeBy: 'value', // REMOVED: Highcharts defaults size to 'value' property
        dataLabels: {
          enabled: false, // Default labels off, controlled by levels
          allowOverlap: true,
          style: { fontSize: '0.9em', textOutline: 'none' }
        },
        // --- Levels Configuration ---
        levels: [
          { // Level 1: Top level (e.g., Sector)
            level: 1,
            borderWidth: 3, // Thicker border for top level
            borderColor: '#1a1d24', // Darker border for contrast
            dataLabels: {
              enabled: true,
              align: 'left',
              verticalAlign: 'top',
              padding: 3,
              style: {
                fontWeight: 'bold',
                fontSize: '0.8em', // Slightly larger
                textTransform: 'uppercase',
                color: 'white'
              },
              // Formatter now checks for null colorValue (from NaN)
              formatter: function() {
                const perfValue = this.point.colorValue; // Use colorValue set in Python
                const isNaN = (perfValue === null || perfValue === undefined); // Check if value is null/undefined

                if (isNaN) {
                  // Use the nan_label passed from Python
                  return `<div>${this.point.name}<br><span style="font-size:0.8em; color: #cccccc">${__NAN_LABEL__}</span></div>`;
                }

                const textColor = (perfValue < 0) ? '#ff9999' : '#99ff99'; // Lighter red/green
                const sign = (perfValue < 0) ? "" : "+";
                const perfText = `${sign}${perfValue.toFixed(2)}%`;
                return `<div>${this.point.name}<br><span style="font-size:0.8em; color: ${textColor}">${perfText}</span></div>`;
              }
            }
          },
          { // Level 2: Middle level (e.g., Industry)
            level: 2,
            borderWidth: 1,
            borderColor: '#252931', // Match background
            // Color applied via colorAxis based on colorValue (avg performance)
            dataLabels: {
              enabled: true,
              align: 'center',
              verticalAlign: 'middle',
              padding: 2,
              style: {
                color: 'white',
                fontSize: '0.7em', // Slightly smaller
                textTransform: 'uppercase',
                textOutline: '1px #1a1d24' // Add outline for readability
              },
              formatter: function() {
                const perfValue = this.point.colorValue;
                const isNaN = (perfValue === null || perfValue === undefined);

                if (isNaN) {
                  return `<div>${this.point.name}<br><span style="font-size:0.8em; color: #cccccc">${__NAN_LABEL__}</span></div>`;
                }

                const sign = (perfValue < 0) ? "" : "+";
                const perfText = `${sign}${perfValue.toFixed(2)}%`;
                return `<div>${this.point.name}<br><span style="font-size:0.8em;">${perfText}</span></div>`;
              }
            }
          },
          { // Level 3: Bottom level (leaf nodes, e.g., Company)
            level: 3,
            borderWidth: 0, // No border for leaves unless hovered
            // Color applied via colorAxis based on colorValue (individual performance)
            dataLabels: {
              enabled: true,
              defer: false, // Render immediately
              useHTML: true, // Allow HTML for better styling control
              align: 'center',
              verticalAlign: 'middle',
              formatter: function() {
                // Access data prepared in Python via point.custom
                const name = this.point.name || '';
                const perfText = this.point.custom?.performance || ''; // Use text from Python ('+X.XX%' or 'N/A')
                const perfValue = this.point.colorValue; // Raw numeric value or null
                const isNaN = (perfValue === null || perfValue === undefined);

                // Base style
                let valueStyle = 'font-size:0.8em; display: block; margin-top: 2px;';
                let containerStyle = 'text-align: center; word-wrap: break-word; overflow: hidden;'; // Added overflow/wrap

                if (isNaN) {
                   valueStyle += ' color: #cccccc;'; // Lighter color for N/A label
                   // Use the nan_label passed from Python
                   return `<div style="${containerStyle}">${name}<br><span style="${valueStyle}">${__NAN_LABEL__}</span></div>`;
                } else {
                    // Use color based on value sign for the text itself
                    valueStyle += (perfValue < 0) ? ' color: #ffcccc;' : ' color: #ccffcc;'; // Even lighter red/green
                    return `<div style="${containerStyle}">${name}<br><span style="${valueStyle}">${perfText}</span></div>`;
                }
              },
              style: { color: 'white', fontSize: '0.9em', textOutline: '1px #1a1d24' } // Base style, size adjusts below
            }
          }
        ],
        // --- Data ---
        data: data, // Data from Python

        // --- Tooltip ---
        tooltip: {
            useHTML: true, // Allow HTML
            outside: true, // Allow tooltip to overflow chart bounds
            formatter: function() {
                const point = this.point;
                const name = point.custom?.fullName || point.name || '';
                const level = point.node?.level || 0; // Get node level
                const value = point.value || 0; // Box size value
                const colorValue = point.colorValue; // Color metric (performance) or null
                const perfText = point.custom?.performance || ''; // Formatted performance string from Python
                const isNaN = (colorValue === null || colorValue === undefined);

                let tooltipHtml = `<span style="font-size:1.1em; font-weight:bold;">${name}</span><br/>`;

                if (level === 1 || level === 2) {
                    tooltipHtml += `<b>Avg Performance:</b> `;
                } else {
                    tooltipHtml += `<b>Performance:</b> `;
                }

                if (isNaN) {
                    // Use the nan_label passed from Python
                    tooltipHtml += `<span style="color:#cccccc;">${__NAN_LABEL__}</span>`;
                } else {
                    const textColor = (colorValue < 0) ? '#ff8080' : '#80ff80'; // Brighter red/green for tooltip
                    tooltipHtml += `<span style="color:${textColor}; font-weight: bold;">${perfText}</span>`;
                }

                // Add size information if it's meaningful
                if (hasSizeColumn && level === 3) { // Show individual size for leaves if size_column was used
                    tooltipHtml += `<br/><b>Size Metric:</b> ${value.toFixed(2)}`;
                } else if (hasSizeColumn && (level === 1 || level === 2)) { // Show aggregated size for parents
                     tooltipHtml += `<br/><b>Total Size:</b> ${value.toFixed(2)}`;
                } else if (!hasSizeColumn && (level === 1 || level === 2)) { // Show item count if size is count-based
                     tooltipHtml += `<br/><b>Item Count:</b> ${Math.round(value)}`; // Value is count here
                }
                // For level 3 count-based, size is always 1, maybe don't show?

                return tooltipHtml;
            }
        },

      }], // End series

      // --- Title & Subtitle ---
      title: {
        text: __CHART_TITLE__,
        align: 'left',
        style: { color: 'white' }
      },
      subtitle: {
        text: __CHART_SUBTITLE__,
        align: 'left',
        style: { color: 'silver' }
      },

      // --- Color Axis ---
      colorAxis: {
        minColor: '__COLOR_MIN__',
        maxColor: '__COLOR_MAX__',
        stops: [ // Define the color gradient stops explicitly
          [0,   '__COLOR_MIN__'],   // Value at min maps to min color
          [0.475, '#414555'],     // Values slightly below center map to gray
          [0.525, '#414555'],     // Values slightly above center map to gray
          [1,   '__COLOR_MAX__']    // Value at max maps to max color
        ],
        min: __VALUE_MIN__, // Use min/max from Python settings
        max: __VALUE_MAX__,
        gridLineWidth: 0, // Hide grid lines on axis
        labels: {
          enabled: true,
          format: '{value}%', // Assume values are percentages for the axis labels
          style: { color: 'white' }
        },
        // Let Highcharts handle null colorValue by default (often shows as gray or similar)
        // We override specific NaN node colors in the event handler below if needed.
      },

      // --- Exporting & Navigation ---
       exporting: { enabled: true }, // Keep exporting enabled
       navigation: { // Standard navigation buttons
            buttonOptions: {
                theme: {
                   fill: '#252931', // Dark background for buttons
                   stroke: '#444',   // Border for buttons
                   style: { color: 'silver' }, // Icon color
                   states: {
                       hover: { fill: '#3a3f4a', style: { color: 'white' } },
                       select: { fill: '#414555', style: { color: 'white' } }
                   }
                }
            }
       }

    }); // End Highcharts.chart

    // --- Additional Highcharts Plugins/Events ---

    // Dynamic Font Size and NaN Coloring Plugin
    Highcharts.addEvent(Highcharts.Series, 'afterDrawDataLabels', function () {
        if (this.type === 'treemap') {
            this.points.forEach(point => {
                // Ensure data label exists and shape arguments are calculated
                if (point.dataLabel && point.shapeArgs) {
                    const isLeaf = point.node?.level === 3;
                    const colorValue = point.colorValue;
                    const isNaN = (colorValue === null || colorValue === undefined);

                    // Apply NaN color explicitly if needed using the color string from Python
                    if (isNaN && point.graphic) {
                         // Use the nan_color passed from Python (already json.dumps'd)
                         point.graphic.attr({ fill: __NAN_COLOR__ });
                         // Optionally style the label background too if using HTML labels extensively
                         // if (point.dataLabel.element) { point.dataLabel.element.style.backgroundColor = __NAN_COLOR__; } // Less reliable?
                    }

                    // Adjust font size for leaf nodes based on area
                    if (isLeaf) {
                        const area = point.shapeArgs.width * point.shapeArgs.height;
                        // Simple dynamic font size - adjust multipliers as needed
                        const fontSize = Math.max(8, Math.min(16, 7 + Math.sqrt(area) * 0.15));
                        if (point.dataLabel.element) {
                             // Check if style object exists before setting fontSize
                            if (!point.dataLabel.element.style) {
                                point.dataLabel.element.style = {}; // Initialize if missing
                            }
                            point.dataLabel.element.style.fontSize = fontSize + 'px';
                        }
                    }
                }
            });
        }
    });

}; // End renderChart function
        """

    def _get_default_html_template(self):
        """Returns the default HTML template for the treemap chart"""
        # **FIX:** Removed the problematic 'const undefined = null;' and 'const nan = null;' lines.
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Hierarchical Treemap</title>
    <!-- Highcharts -->
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/treemap.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://code.highcharts.com/modules/accessibility.js"></script>
    <script src="https://code.highcharts.com/modules/coloraxis.js"></script>
    <style>
      html, body { margin: 0; padding: 0; background-color: #252931; color: white; font-family: sans-serif; height: 100%; overflow: hidden; } /* Added overflow hidden */
      #container { width: 100%; height: 100%; min-height: 600px; }
    </style>
  </head>
  <body>
    <div id="container"></div>
    <!-- 1) JS template injected here -->
    <script>
        {{CHART_JS}}
    </script>
    <!-- 2) Data injected and chart rendered -->
    <script>
      // **FIX:** Removed definitions for 'nan' and 'undefined'.
      // Proper JSON serialization handles NaN -> null.

      // Data is injected directly as a JSON literal
      const treeData = {{TREE_DATA_JSON}};

      // Check if Highcharts is loaded before rendering
      if (typeof Highcharts !== 'undefined') {
          try {
              renderChart(treeData);
          } catch (e) {
               console.error("Error executing renderChart:", e);
               document.getElementById('container').innerHTML = '<p style="color:red; text-align:center;">Error rendering chart. Check console for details.</p>';
          }
      } else {
          console.error("Highcharts library not loaded.");
          document.getElementById('container').innerHTML = '<p style="color:red; text-align:center;">Error: Could not load Highcharts library.</p>';
      }
    </script>
  </body>
</html>"""