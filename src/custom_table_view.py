import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import sqlite3
from database_utils import execute_query, execute_query_df
import re
import io
from plotly import express as px
import numpy as np

class CustomTableView:
    """
    Enhanced table view component for better visualizing and interacting with database tables
    """
    
    def __init__(self, table_name, db_path='attendance_system.db'):
        """Initialize the table view with the specified table"""
        self.table_name = table_name
        self.db_path = db_path
        self.column_info = self._get_table_structure()
        self.primary_key = self._get_primary_key()
        self.foreign_keys = self._get_foreign_keys()

    def _get_db_connection(self):
        """Create a connection to the database"""
        return sqlite3.connect(self.db_path)

    def _get_table_structure(self):
        """Get the structure of the table"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        execute_query(f"PRAGMA table_info({self.table_name})")
        columns = cursor.fetchall()
        
        # Column info format: (cid, name, type, notnull, dflt_value, pk)
        column_info = [{
            'cid': col[0],
            'name': col[1],
            'type': col[2].lower(),
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        } for col in columns]
        
        conn.close()
        return column_info

    def _get_primary_key(self):
        """Extract primary key column from column info"""
        for col in self.column_info:
            if col['pk'] == 1:
                return col['name']
        return None

    def _get_foreign_keys(self):
        """Get foreign key information for the table"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        execute_query(f"PRAGMA foreign_key_list({self.table_name})")
        fk_data = cursor.fetchall()
        conn.close()
        
        # Format: (id, seq, table, from, to, on_update, on_delete, match)
        foreign_keys = {}
        for fk in fk_data:
            foreign_keys[fk[3]] = {
                'ref_table': fk[2],
                'ref_column': fk[4],
                'on_update': fk[5],
                'on_delete': fk[6]
            }
        
        return foreign_keys

    def _get_filtered_data(self, where_clause="", order_by="", limit=1000, offset=0):
        """Get data from the table with optional filtering"""
        conn = self._get_db_connection()
        
        query = f"SELECT * FROM {self.table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
            
        if order_by:
            query += f" ORDER BY {order_by}"
        elif self.primary_key:
            query += f" ORDER BY {self.primary_key}"
            
        query += f" LIMIT {limit} OFFSET {offset}"
        
        df = execute_query_df(query)
        
        # Get total row count
        count_query = f"SELECT COUNT(*) FROM {self.table_name}"
        if where_clause:
            count_query += f" WHERE {where_clause}"
        
        total_rows = execute_query_df(count_query).iloc[0, 0]
        
        conn.close()
        return df, total_rows

    def _get_referenced_values(self, fk_column):
        """Get values from referenced table for foreign key column"""
        fk_info = self.foreign_keys.get(fk_column)
        if not fk_info:
            return []
            
        conn = self._get_db_connection()
        ref_table = fk_info['ref_table']
        ref_column = fk_info['ref_column']
        
        query = f"SELECT {ref_column}, * FROM {ref_table} LIMIT 1000"
        df = execute_query_df(query)
        conn.close()
        
        # If there's a 'name' column, use it for display with the ID
        if 'name' in df.columns:
            return [f"{row[ref_column]} - {row['name']}" for _, row in df.iterrows()]
        else:
            return df[ref_column].tolist()

    def render_filter_panel(self):
        """Render the filter panel for the table"""
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Column names for filtering
            column_names = [col['name'] for col in self.column_info]
            filter_col = st.selectbox(
                "Filter by column:", 
                ["None"] + column_names, 
                key=f"filter_col_{self.table_name}"
            )
            
            where_clause = ""
            if filter_col != "None":
                # Check if it's a foreign key
                if filter_col in self.foreign_keys:
                    # Get values from referenced table
                    ref_values = self._get_referenced_values(filter_col)
                    filter_val = st.selectbox(
                        f"Select {filter_col}:", 
                        ["All"] + ref_values, 
                        key=f"filter_val_{self.table_name}"
                    )
                    
                    if filter_val != "All":
                        # Extract the ID from the display value
                        id_match = re.match(r"^(\d+)", filter_val)
                        if id_match:
                            filter_id = id_match.group(1)
                            where_clause = f"{filter_col} = {filter_id}"
                else:
                    # Get unique values for column (limited for performance)
                    conn = self._get_db_connection()
                    cursor = conn.cursor()
                    execute_query(f"SELECT DISTINCT {filter_col} FROM {self.table_name} LIMIT 50")
                    unique_vals = [row[0] for row in cursor.fetchall() if row[0] is not None]
                    conn.close()
                    
                    if len(unique_vals) <= 30:
                        # For small sets, use a dropdown
                        filter_val = st.selectbox(
                            f"Select value:", 
                            ["All"] + unique_vals, 
                            key=f"filter_val_sel_{self.table_name}"
                        )
                        if filter_val != "All":
                            if isinstance(filter_val, str):
                                where_clause = f"{filter_col} = '{filter_val}'"
                            else:
                                where_clause = f"{filter_col} = {filter_val}"
                    else:
                        # For larger sets, use text input
                        filter_val = st.text_input(
                            f"Filter value:", 
                            key=f"filter_val_txt_{self.table_name}",
                            placeholder="Enter value..."
                        )
                        
                        if filter_val:
                            filter_type = st.radio(
                                "Match type:", 
                                ["Contains", "Equals", "Starts with"], 
                                horizontal=True,
                                key=f"filter_type_{self.table_name}"
                            )
                            
                            col_type = next((col['type'] for col in self.column_info if col['name'] == filter_col), 'text')
                            is_numeric = any(t in col_type.lower() for t in ['int', 'real', 'float', 'double', 'numeric'])
                            
                            if is_numeric:
                                # For numeric columns, use direct comparison
                                if filter_type == "Equals":
                                    where_clause = f"{filter_col} = {filter_val}"
                                else:
                                    where_clause = f"{filter_col} LIKE '%{filter_val}%'"
                            else:
                                # For text columns
                                if filter_type == "Contains":
                                    where_clause = f"{filter_col} LIKE '%{filter_val}%'"
                                elif filter_type == "Equals":
                                    where_clause = f"{filter_col} = '{filter_val}'"
                                else:  # Starts with
                                    where_clause = f"{filter_col} LIKE '{filter_val}%'"
            
        with col2:
            # Order by selection
            order_col = st.selectbox(
                "Order by:", 
                ["None"] + column_names, 
                key=f"order_col_{self.table_name}"
            )
            
            order_by = ""
            if order_col != "None":
                order_dir = st.radio(
                    "Direction:", 
                    ["ASC", "DESC"], 
                    horizontal=True,
                    key=f"order_dir_{self.table_name}"
                )
                order_by = f"{order_col} {order_dir}"
            
        # Row limit slider
        limit = st.slider(
            "Max rows:", 
            min_value=10, 
            max_value=1000, 
            value=200, 
            step=10,
            key=f"limit_{self.table_name}"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        return where_clause, order_by, limit

    def render_table(self, where_clause="", order_by="", limit=200):
        """Render the table with the given filters"""
        with st.spinner("Loading data..."):
            df, total_rows = self._get_filtered_data(where_clause, order_by, limit)
            
        # Show record count with filter info
        showing = len(df)
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; margin:10px 0;">
                <div>Showing <b>{showing}</b> of <b>{total_rows:,}</b> records {f"(filtered)" if where_clause else ""}</div>
                <div>{f"Sorted by: {order_by}" if order_by else ""}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Add basic stats if numeric columns exist
        numeric_cols = df.select_dtypes(include=['number']).columns
        if not df.empty and len(numeric_cols) > 0:
            with st.expander("Quick Stats", expanded=False):
                # Calculate basic statistics for numeric columns
                stats_df = df[numeric_cols].describe().T.reset_index()
                stats_df.columns = ['Column', 'Count', 'Mean', 'Std', 'Min', '25%', '50%', '75%', 'Max']
                stats_df = stats_df.round(2)
                
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        # Check if empty
        if df.empty:
            st.info(f"No records found in {self.table_name}")
            return df
        
        # Replace foreign key values with display values if possible
        df_display = df.copy()
        for fk_col, fk_info in self.foreign_keys.items():
            if fk_col in df.columns:
                conn = self._get_db_connection()
                ref_table = fk_info['ref_table']
                ref_col = fk_info['ref_column']
                
                # Try to get a name column for better display
                try:
                    # Safe approach to handle potentially empty dataframes
                    if not df[fk_col].dropna().empty:
                        placeholders = ', '.join(['?' for _ in range(len(df[fk_col].dropna().unique()))])
                        query = f"SELECT DISTINCT {ref_col}, name FROM {ref_table} WHERE {ref_col} IN ({placeholders})"
                        cursor = conn.cursor()
                        execute_query(query, df[fk_col].dropna().unique().tolist())
                        fk_results = cursor.fetchall()
                        
                        if fk_results:
                            fk_map = {str(r[0]): r[1] for r in fk_results}
                            
                            # Create a new display column
                            new_col_name = f"{fk_col}_display"
                            df_display[new_col_name] = df[fk_col].apply(
                                lambda x: f"{x} - {fk_map.get(str(x), 'Unknown')}" if pd.notna(x) and str(x) in fk_map else x
                            )
                except Exception as e:
                    # If error, just skip this foreign key enhancement
                    st.warning(f"Error enhancing foreign key display: {e}")
                
                conn.close()

        # Render interactive table with Streamlit's data editor
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            height=min(400, len(df) * 35 + 38),
            hide_index=True,
            num_rows="fixed"
        )
        
        # Check for changes
        if not df_display.equals(edited_df):
            st.info("⚠️ Changes detected. Click 'Save Changes' to update the database.")
            
            # Find changes by comparing dataframes
            changes = []
            for i, (_, original_row) in enumerate(df.iterrows()):
                edited_row = edited_df.iloc[i]
                
                # Check if there are differences in this row
                row_changed = False
                row_changes = {}
                
                for col in df.columns:
                    if col not in edited_df.columns or col + '_display' in edited_df.columns:
                        continue
                        
                    if original_row[col] != edited_row[col]:
                        row_changed = True
                        row_changes[col] = {
                            'old': original_row[col],
                            'new': edited_row[col]
                        }
                
                if row_changed:
                    # Add the primary key if available
                    if self.primary_key:
                        pk_value = original_row[self.primary_key]
                        changes.append({
                            'pk_column': self.primary_key,
                            'pk_value': pk_value,
                            'changes': row_changes
                        })
                    else:
                        # Use row index if no primary key
                        changes.append({
                            'row_idx': i,
                            'changes': row_changes
                        })
            
            # Show save button if changes were detected
            if changes and st.button("Save Changes", type="primary"):
                with st.spinner("Updating database..."):
                    success_count = 0
                    error_count = 0
                    
                    conn = self._get_db_connection()
                    cursor = conn.cursor()
                    
                    for change in changes:
                        try:
                            if 'pk_column' in change:
                                # Update using primary key
                                pk_col = change['pk_column']
                                pk_val = change['pk_value']
                                
                                # Build SET clause
                                set_parts = []
                                values = []
                                
                                for col, val_change in change['changes'].items():
                                    set_parts.append(f"{col} = ?")
                                    values.append(val_change['new'])
                                
                                # Add primary key value at the end
                                values.append(pk_val)
                                
                                query = f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE {pk_col} = ?"
                                cursor.execute(query, values)
                                success_count += 1
                            else:
                                # Can't update without primary key
                                st.warning(f"Couldn't update row {change['row_idx']} - no primary key available")
                                error_count += 1
                                
                        except Exception as e:
                            st.error(f"Error updating record: {e}")
                            error_count += 1
                    
                    # Commit changes
                    conn.commit()
                    conn.close()
                    
                    if success_count > 0:
                        st.success(f"Updated {success_count} record(s)")
                    if error_count > 0:
                        st.error(f"Failed to update {error_count} record(s)")
                    
                    # Refresh the page
                    st.rerun()
        
        return df

    def render_visualization(self, df):
        """Render visualizations for the table data"""
        if df.empty or len(df) < 2:
            return
            
        st.subheader("Visualize Data")
        
        # Detect column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        date_cols = []
        
        # Try to identify date columns
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col])
                    date_cols.append(col)
                except:
                    pass
        
        # Choose visualization type
        viz_type = st.selectbox(
            "Select chart type:",
            options=[
                "Bar Chart (Categories)",
                "Line Chart (Time Series)",
                "Histogram (Distribution)",
                "Scatter Plot (Correlation)",
                "Pie Chart (Proportions)"
            ],
            key=f"viz_type_{self.table_name}"
        )
        
        # Render the selected visualization
        if viz_type == "Bar Chart (Categories)":
            self._render_bar_chart(df, categorical_cols, numeric_cols)
        elif viz_type == "Line Chart (Time Series)":
            self._render_line_chart(df, date_cols, numeric_cols)
        elif viz_type == "Histogram (Distribution)":
            self._render_histogram(df, numeric_cols)
        elif viz_type == "Scatter Plot (Correlation)":
            self._render_scatter_plot(df, numeric_cols, categorical_cols)
        elif viz_type == "Pie Chart (Proportions)":
            self._render_pie_chart(df, categorical_cols, numeric_cols)

    def _render_bar_chart(self, df, categorical_cols, numeric_cols):
        """Render a bar chart visualization"""
        if not categorical_cols:
            st.warning("No categorical columns available for bar chart")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            cat_col = st.selectbox("Category column:", categorical_cols, key=f"bar_cat_{self.table_name}")
        
        with col2:
            if numeric_cols:
                value_col = st.selectbox("Value column:", ["Count"] + numeric_cols, key=f"bar_val_{self.table_name}")
            else:
                value_col = "Count"
        
        # Process data for the chart
        if value_col == "Count":
            chart_data = df[cat_col].value_counts().reset_index()
            chart_data.columns = [cat_col, 'Count']
            y_col = 'Count'
            agg_func = "Count"
        else:
            # For numeric values, offer aggregation options
            agg_func = st.radio(
                "Aggregation:", 
                ["Mean", "Sum", "Count", "Min", "Max"], 
                horizontal=True,
                key=f"bar_agg_{self.table_name}"
            )
            
            agg_map = {
                "Mean": "mean", 
                "Sum": "sum", 
                "Count": "count",
                "Min": "min",
                "Max": "max"
            }
            
            selected_agg = agg_map[agg_func]
            chart_data = df.groupby(cat_col)[value_col].agg([selected_agg.lower()]).reset_index()
            y_col = selected_agg.lower()
        
        # Create the bar chart
        fig = px.bar(
            chart_data,
            x=cat_col,
            y=y_col,
            title=f"{agg_func} of {value_col if value_col != 'Count' else 'Records'} by {cat_col}",
            text=y_col,
            color=y_col,
            color_continuous_scale="Blues",
            template="plotly_white"
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title=cat_col,
            yaxis_title=f"{agg_func} of {value_col if value_col != 'Count' else 'Records'}",
            coloraxis_showscale=False
        )
        
        # Show the chart
        st.plotly_chart(fig, use_container_width=True)

    def _render_line_chart(self, df, date_cols, numeric_cols):
        """Render a line chart for time series data"""
        if not date_cols:
            st.warning("No date/time columns detected for time series chart")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            date_col = st.selectbox("Date column:", date_cols, key=f"line_date_{self.table_name}")
        
        with col2:
            if numeric_cols:
                value_col = st.selectbox("Value column:", ["Count"] + numeric_cols, key=f"line_val_{self.table_name}")
            else:
                value_col = "Count"
        
        # Process data for time series
        try:
            # Convert to datetime
            chart_df = df.copy()
            chart_df[date_col] = pd.to_datetime(chart_df[date_col])
            
            # Choose group frequency
            freq = st.radio(
                "Group by:", 
                ["Day", "Week", "Month", "Year"], 
                horizontal=True,
                key=f"line_freq_{self.table_name}"
            )
            
            freq_map = {
                "Day": "D", 
                "Week": "W", 
                "Month": "M", 
                "Year": "Y"
            }
            
            # Group by date with selected frequency
            if value_col == "Count":
                # Count records by date
                chart_data = chart_df.groupby(pd.Grouper(key=date_col, freq=freq_map[freq])).size().reset_index()
                chart_data.columns = [date_col, 'Count']
                y_col = 'Count'
                title = f"Count of Records Over Time (by {freq})"
            else:
                # Offer aggregation options
                agg_func = st.radio(
                    "Aggregation:", 
                    ["Mean", "Sum", "Min", "Max"], 
                    horizontal=True,
                    key=f"line_agg_{self.table_name}"
                )
                
                agg_map = {
                    "Mean": "mean", 
                    "Sum": "sum", 
                    "Min": "min", 
                    "Max": "max"
                }
                
                selected_agg = agg_map[agg_func]
                chart_data = chart_df.groupby(pd.Grouper(key=date_col, freq=freq_map[freq]))[value_col].agg(selected_agg).reset_index()
                y_col = value_col
                title = f"{agg_func} of {value_col} Over Time (by {freq})"
            
            # Create the line chart with markers
            fig = px.line(
                chart_data,
                x=date_col,
                y=y_col,
                title=title,
                markers=True,
                template="plotly_white"
            )
            
            # Format dates on x-axis based on frequency
            if freq == "Day":
                date_format = '%b %d'
            elif freq == "Week":
                date_format = '%b %d'
            elif freq == "Month":
                date_format = '%b %Y'
            else:
                date_format = '%Y'
                
            fig.update_xaxes(
                tickformat=date_format,
                title="Date"
            )
            
            # Update layout
            fig.update_layout(
                yaxis_title=y_col,
                xaxis_title="Date",
                hovermode="x unified"
            )
            
            # Show the chart
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating line chart: {str(e)}")

    def _render_histogram(self, df, numeric_cols):
        """Render a histogram visualization"""
        if not numeric_cols:
            st.warning("No numeric columns available for histogram")
            return
            
        col = st.selectbox("Select column:", numeric_cols, key=f"hist_col_{self.table_name}")
        
        # Allow user to set number of bins
        bins = st.slider("Number of bins:", min_value=5, max_value=50, value=20, key=f"hist_bins_{self.table_name}")
        
        # Create histogram with Plotly Express
        fig = px.histogram(
            df,
            x=col,
            nbins=bins,
            title=f"Distribution of {col}",
            template="plotly_white",
            color_discrete_sequence=['#3366CC']
        )
        
        # Add KDE (Kernel Density Estimate) if requested
        show_kde = st.checkbox("Show density curve", value=True, key=f"hist_kde_{self.table_name}")
        if show_kde:
            # Create histogram data with density curve normalized
            hist_data = np.histogram(df[col].dropna(), bins=bins)
            hist_x = [(hist_data[1][i] + hist_data[1][i+1])/2 for i in range(len(hist_data[1])-1)]
            
            # Use numpy to get a smooth curve using gaussian KDE
            from scipy import stats
            if len(df[col].dropna()) > 1:  # Need at least 2 points for KDE
                kde = stats.gaussian_kde(df[col].dropna())
                x_kde = np.linspace(df[col].min(), df[col].max(), 1000)
                y_kde = kde(x_kde)
                
                # Scale KDE to match histogram height
                scaling_factor = max(hist_data[0]) / max(y_kde) if max(y_kde) > 0 else 1
                
                # Add the density curve as a line
                fig.add_trace(go.Scatter(
                    x=x_kde,
                    y=y_kde * scaling_factor,
                    mode='lines',
                    name='Density',
                    line=dict(color='red', width=2)
                ))
        
        # Add mean and median lines
        show_stats = st.checkbox("Show mean and median", value=True, key=f"hist_stats_{self.table_name}")
        if show_stats:
            mean_val = df[col].mean()
            median_val = df[col].median()
            
            fig.add_vline(x=mean_val, line_dash="dash", line_color="green",
                         annotation_text="Mean", annotation_position="top right")
            fig.add_vline(x=median_val, line_dash="dash", line_color="orange",
                         annotation_text="Median", annotation_position="top left")
        
        # Update layout
        fig.update_layout(
            xaxis_title=col,
            yaxis_title="Count",
            bargap=0.05
        )
        
        # Show the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Show basic statistics
        with st.expander("View Statistics", expanded=False):
            stats_df = pd.DataFrame({
                'Statistic': ['Count', 'Mean', 'Median', 'Std Dev', 'Min', 'Max', 'Q1 (25%)', 'Q3 (75%)'],
                'Value': [
                    df[col].count(),
                    round(df[col].mean(), 2),
                    round(df[col].median(), 2),
                    round(df[col].std(), 2),
                    round(df[col].min(), 2),
                    round(df[col].max(), 2),
                    round(df[col].quantile(0.25), 2),
                    round(df[col].quantile(0.75), 2)
                ]
            })
            st.dataframe(stats_df, use_container_width=True, hide_index=True)

    def _render_scatter_plot(self, df, numeric_cols, categorical_cols):
        """Render a scatter plot visualization"""
        if len(numeric_cols) < 2:
            st.warning("Need at least 2 numeric columns for scatter plot")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_col = st.selectbox("X-Axis:", numeric_cols, key=f"scatter_x_{self.table_name}")
        
        with col2:
            y_col = st.selectbox("Y-Axis:", [col for col in numeric_cols if col != x_col], key=f"scatter_y_{self.table_name}")
        
        with col3:
            if categorical_cols:
                color_col = st.selectbox("Color by:", ["None"] + categorical_cols, key=f"scatter_color_{self.table_name}")
            else:
                color_col = "None"
        
        # Create scatter plot
        if color_col != "None":
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"{y_col} vs {x_col} by {color_col}",
                template="plotly_white"
            )
        else:
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                title=f"{y_col} vs {x_col}",
                template="plotly_white"
            )
        
        # Option to add trendline
        show_trendline = st.checkbox("Show trendline", value=True, key=f"scatter_trend_{self.table_name}")
        if show_trendline:
            if color_col != "None":
                fig = px.scatter(
                    df, 
                    x=x_col, 
                    y=y_col,
                    color=color_col,
                    trendline="ols",
                    title=f"{y_col} vs {x_col} by {color_col}",
                    template="plotly_white"
                )
            else:
                fig = px.scatter(
                    df, 
                    x=x_col, 
                    y=y_col,
                    trendline="ols",
                    title=f"{y_col} vs {x_col}",
                    template="plotly_white"
                )
                
                # Calculate correlation coefficient
                correlation = df[[x_col, y_col]].corr().iloc[0, 1]
                
                # Add correlation annotation
                fig.add_annotation(
                    x=0.5,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    text=f"Correlation: {correlation:.2f}",
                    showarrow=False,
                    font=dict(size=12),
                    bgcolor="white",
                    bordercolor="black",
                    borderwidth=1
                )
        
        # Update layout
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        # Show the chart
        st.plotly_chart(fig, use_container_width=True)

    def _render_pie_chart(self, df, categorical_cols, numeric_cols):
        """Render a pie chart visualization"""
        if not categorical_cols:
            st.warning("No categorical columns available for pie chart")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            cat_col = st.selectbox("Category column:", categorical_cols, key=f"pie_cat_{self.table_name}")
        
        with col2:
            if numeric_cols:
                value_col = st.selectbox("Value column:", ["Count"] + numeric_cols, key=f"pie_val_{self.table_name}")
            else:
                value_col = "Count"
        
        # Process data for the chart
        if value_col == "Count":
            # Get value counts
            chart_data = df[cat_col].value_counts().reset_index()
            chart_data.columns = [cat_col, 'Count']
            values = chart_data['Count']
            names = chart_data[cat_col]
            title = f"Distribution of {cat_col} by Count"
        else:
            # For numeric values, offer aggregation options
            agg_func = st.radio(
                "Aggregation:", 
                ["Sum", "Mean", "Max", "Min"], 
                horizontal=True,
                key=f"pie_agg_{self.table_name}"
            )
            
            agg_map = {
                "Sum": "sum",
                "Mean": "mean",
                "Max": "max",
                "Min": "min"
            }
            
            selected_agg = agg_map[agg_func]
            
            chart_data = df.groupby(cat_col)[value_col].agg(selected_agg).reset_index()
            values = chart_data[value_col]
            names = chart_data[cat_col]
            title = f"{agg_func} of {value_col} by {cat_col}"
        
        # Filter to top N categories if there are too many
        max_categories = st.slider("Max categories:", min_value=3, max_value=20, value=10, key=f"pie_max_{self.table_name}")
        
        if len(names) > max_categories:
            # Get top categories by value
            top_indices = values.nlargest(max_categories-1).index
            
            # Create "Other" category for the rest
            other_sum = values.drop(top_indices).sum()
            
            # Create new series with top categories and "Other"
            new_values = values.iloc[top_indices].append(pd.Series([other_sum], index=[len(values)]))
            new_names = names.iloc[top_indices].append(pd.Series(["Other"], index=[len(names)]))
            
            values = new_values
            names = new_names
        
        # Create pie chart
        fig = px.pie(
            values=values,
            names=names,
            title=title,
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        
        # Update layout
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate="%{label}<br>%{value:.2f}<br>%{percent}"
        )
        
        # Add option for donut chart
        donut = st.checkbox("Show as donut chart", value=False, key=f"pie_donut_{self.table_name}")
        if donut:
            fig.update_traces(hole=0.4)
        
        # Show the chart
        st.plotly_chart(fig, use_container_width=True)

    def show(self):
        """Main method to display the entire custom table view"""
        st.subheader(f"Table: {self.table_name}")
        
        # Add filter panel
        with st.expander("Filters & Sorting", expanded=False):
            where_clause, order_by, limit = self.render_filter_panel()
        
        # Render the table with chosen filters
        df = self.render_table(where_clause, order_by, limit)
        
        # Show visualizations if data exists
        if not df.empty and len(df) > 1:
            with st.expander("Data Visualization", expanded=False):
                self.render_visualization(df)
        
        return df