import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Page configuration
st.set_page_config(
    page_title="Construction Pricing Calculator",
    page_icon="🏗️",
    layout="wide"
)

# Initialize session state
if 'current_service' not in st.session_state:
    st.session_state.current_service = 'gutters'

if 'measurements' not in st.session_state:
    st.session_state.measurements = {
        'gutters': pd.DataFrame(columns=['Location', 'Gutter Type', 'Measurements', 'LF']),
        'leaders': pd.DataFrame(columns=['Location', 'Leader Type', 'Measurements', 'LF']),
        'guards': pd.DataFrame(columns=['Location', 'Guard Type', 'Measurements', 'LF']),
        'stone_flats': pd.DataFrame(columns=['Location', 'Width', 'Height', 'Total SF']),
        'stone_corners': pd.DataFrame(columns=['Location', 'Width', 'Height', 'LF']),
        'stone_sills': pd.DataFrame(columns=['Location', 'Width', 'Height', 'LF']),
        'stucco': pd.DataFrame(columns=['Location', 'Item Type', 'Measurements', 'SF']),
        'painting': pd.DataFrame(columns=['Location', 'Item Type', 'Measurements', 'SF'])
    }

if 'misc_quantities' not in st.session_state:
    st.session_state.misc_quantities = {}

if 'customer_info' not in st.session_state:
    st.session_state.customer_info = {
        'customer_name': '',
        'project_address': '',
        'sales_rep': ''
    }

# Service data configuration
SERVICE_DATA = {
    'gutters': {
        'name': 'Gutters and Leaders',
        'items': {
            'Gutter 5" white': {'price': 13, 'unit': 'LF', 'category': 'gutters'},
            'Gutter 5" all colors': {'price': 15, 'unit': 'LF', 'category': 'gutters'},
            'Gutter 6" white': {'price': 18, 'unit': 'LF', 'category': 'gutters'},
            'Gutter 6" all colors': {'price': 19, 'unit': 'LF', 'category': 'gutters'},
            'Extra Gauge (0.032 gauge)': {'price': 1, 'unit': 'LF', 'category': 'gutters'},
            'Leaders 2x3 white': {'price': 12, 'unit': 'LF', 'category': 'leaders'},
            'Leaders 2x3 all colors': {'price': 13, 'unit': 'LF', 'category': 'leaders'},
            'Leader 2x3 white - PVC': {'price': 18, 'unit': 'LF', 'category': 'leaders'},
            'Leaders 3x4 white': {'price': 15, 'unit': 'LF', 'category': 'leaders'},
            'Leaders 3x4 all colors': {'price': 16, 'unit': 'LF', 'category': 'leaders'},
            'Leader 3" Round Corrugated': {'price': 47, 'unit': 'LF', 'category': 'leaders'},
            'Shur-flow 5" (white)': {'price': 15, 'unit': 'LF', 'category': 'guards'},
            'Shur-flow 5" (black or aluminum)': {'price': 16, 'unit': 'LF', 'category': 'guards'},
            'Shur-flow 6" (white)': {'price': 16, 'unit': 'LF', 'category': 'guards'},
            'Shur-flow 6" (black or aluminum)': {'price': 18, 'unit': 'LF', 'category': 'guards'},
            'Screen 5"': {'price': 10, 'unit': 'LF', 'category': 'guards'},
            'Screen 6"': {'price': 12, 'unit': 'LF', 'category': 'guards'}
        }
    },
    'stone': {
        'name': 'Stone Veneer',
        'items': {
            'Remove vinyl or aluminum siding': {'price': 2.37, 'unit': 'SF', 'category': 'demolition'},
            'Remove wood siding (simple)': {'price': 2.67, 'unit': 'SF', 'category': 'demolition'},
            'Remove wood siding (complex)': {'price': 2.97, 'unit': 'SF', 'category': 'demolition'},
            'Remove EIFS up to 8ft': {'price': 4.00, 'unit': 'SF', 'category': 'demolition'},
            'Natural Stone Installation': {'price': 45, 'unit': 'SF', 'category': 'installation'},
            'Cultured Stone Installation': {'price': 35, 'unit': 'SF', 'category': 'installation'},
            'Corner Trim Installation': {'price': 25, 'unit': 'LF', 'category': 'trim'}
        },
        'delivery_fee': 222
    },
    'stucco': {
        'name': 'Stucco Painting',
        'items': {
            'LOXON XP (200-499 SF)': {'price': 14.27, 'unit': 'SF'},
            'LOXON XP (500-999 SF)': {'price': 13.0, 'unit': 'SF'},
            'LOXON XP (1000-1699 SF)': {'price': 12.45, 'unit': 'SF'},
            'LOXON XP (1700-2999 SF)': {'price': 11.78, 'unit': 'SF'},
            'LOXON XP (3000-4499 SF)': {'price': 11.38, 'unit': 'SF'}
        },
        'miscellaneous': {
            'Remove, Paint and Re-Install Shutters (per pair)': {'price': 290, 'unit': 'Per Pair'},
            'Stainless Steel Chimney Cover': {'price': 1509, 'unit': 'Per Item'},
            'Plywood (demo, debris, install 1 sheet) 32 sf': {'price': 439, 'unit': 'Per Item'},
            'Remove and Re-Install Existing Gutters': {'price': 6, 'unit': 'Per LF'},
            'Additional Rigging (For Caulking Only Projects)': {'price': 435, 'unit': 'Per Side'},
            'Clear Sealer, Ladders, Powerwash': {'price': 7, 'unit': 'Per SF'},
            'Additional Heavy Duty Powerwash': {'price': 2, 'unit': 'Per SF'},
            'Additional stucco crack repair above 50 lf (1" or less)': {'price': 7, 'unit': 'Per LF'},
            'Spot Point Brick (* See rules page)': {'price': 29, 'unit': 'Per SF'},
            'Full Cut and Re-Point (Under 500sf)': {'price': 29, 'unit': 'Per SF'},
            'Full Cut and Re-Point (Over 500sf)': {'price': 24, 'unit': 'Per SF'},
            'Full Coping over Parapet Wall up to 12"': {'price': 85, 'unit': 'Per LF'},
            'Paint Samples (Includes 1 Color Sample)': {'price': 108, 'unit': 'Per Item'}
        }
    },
    'painting': {
        'name': 'House Painting',
        'items': {
            'Vinyl and Aluminum Siding': {'price': 8.06, 'unit': 'SF'},
            'Wood Clapboard (simple)': {'price': 9.28, 'unit': 'SF'},
            'Wood Clapboard (complex)': {'price': 11.5, 'unit': 'SF'},
            'Wood Shake (simple)': {'price': 10.02, 'unit': 'SF'},
            'Wood Shake (complex)': {'price': 12.19, 'unit': 'SF'},
            'Window Trim': {'price': 15.50, 'unit': 'LF'},
            'Door Trim': {'price': 18.75, 'unit': 'LF'}
        }
    }
}

def calculate_stone_sf_or_lf(width, height, table_type):
    """Calculate SF for flats, LF for corners and sills"""
    if pd.isna(width) or pd.isna(height) or width == 0 or height == 0:
        return 0
    
    if table_type == 'flats':
        # Square footage
        return (width * height) / 144  # Convert square inches to square feet
    else:
        # Linear footage (for corners and sills)
        return width / 12  # Convert inches to feet

def calculate_totals(service_key):
    """Calculate totals for current service"""
    totals = {}
    category_totals = {}
    
    if service_key == 'gutters':
        # Calculate gutters
        gutters_df = st.session_state.measurements['gutters']
        leaders_df = st.session_state.measurements['leaders']
        guards_df = st.session_state.measurements['guards']
        
        for item_name, item_data in SERVICE_DATA['gutters']['items'].items():
            if item_data['category'] == 'gutters':
                qty = gutters_df[gutters_df['Gutter Type'] == item_name]['LF'].sum()
            elif item_data['category'] == 'leaders':
                qty = leaders_df[leaders_df['Leader Type'] == item_name]['LF'].sum()
            else:  # guards
                qty = guards_df[guards_df['Guard Type'] == item_name]['LF'].sum()
            
            totals[item_name] = {
                'quantity': qty,
                'unit_price': item_data['price'],
                'total': qty * item_data['price'],
                'category': item_data['category']
            }
        
        # Category subtotals
        category_totals['gutters'] = sum([v['total'] for k, v in totals.items() if v['category'] == 'gutters'])
        category_totals['leaders'] = sum([v['total'] for k, v in totals.items() if v['category'] == 'leaders'])
        category_totals['guards'] = sum([v['total'] for k, v in totals.items() if v['category'] == 'guards'])
        
    elif service_key == 'stone':
        # Calculate stone flats (SF)
        flats_df = st.session_state.measurements['stone_flats']
        total_flats_sf = flats_df['Total SF'].sum()
        
        # Calculate stone corners (LF)
        corners_df = st.session_state.measurements['stone_corners']
        total_corners_lf = corners_df['LF'].sum()
        
        # Calculate stone sills (LF)
        sills_df = st.session_state.measurements['stone_sills']
        total_sills_lf = sills_df['LF'].sum()
        
        for item_name, item_data in SERVICE_DATA['stone']['items'].items():
            qty = 0
            if 'Installation' in item_name and 'Stone' in item_name:
                qty = total_flats_sf
            elif 'Corner' in item_name:
                qty = total_corners_lf
            # Add other item matching logic as needed
            
            totals[item_name] = {
                'quantity': qty,
                'unit_price': item_data['price'],
                'total': qty * item_data['price']
            }
    
    elif service_key in ['stucco', 'painting']:
        df = st.session_state.measurements[service_key]
        
        for item_name, item_data in SERVICE_DATA[service_key]['items'].items():
            qty = df[df['Item Type'] == item_name]['SF'].sum()
            totals[item_name] = {
                'quantity': qty,
                'unit_price': item_data['price'],
                'total': qty * item_data['price']
            }
        
        # Add miscellaneous items for stucco
        if service_key == 'stucco':
            for misc_name, misc_data in SERVICE_DATA['stucco']['miscellaneous'].items():
                qty = st.session_state.misc_quantities.get(misc_name, 0)
                totals[misc_name] = {
                    'quantity': qty,
                    'unit_price': misc_data['price'],
                    'total': qty * misc_data['price']
                }
    
    return totals, category_totals

def calculate_pricing_tiers(subtotal, repair=False, rigging=False):
    """Calculate cascading discount pricing"""
    # 1 Year Price: -10%
    one_year_price = subtotal * 0.9
    deduct_10_1 = subtotal * 0.1
    
    # 30 Day Price: -10% from 1 Year
    thirty_day_price = one_year_price * 0.9
    deduct_10_2 = one_year_price * 0.1
    
    # Day of Price: -3% from 30 Day
    day_of_price = thirty_day_price * 0.97
    deduct_3 = thirty_day_price * 0.03
    
    # Final Sell Price
    final_sell_price = day_of_price
    
    # Add optional add-ons
    if repair:
        final_sell_price += 2100
    if rigging:
        final_sell_price += 1400
    
    return {
        'subtotal': subtotal,
        'one_year_price': one_year_price,
        'deduct_10_1': deduct_10_1,
        'thirty_day_price': thirty_day_price,
        'deduct_10_2': deduct_10_2,
        'day_of_price': day_of_price,
        'deduct_3': deduct_3,
        'final_sell_price': final_sell_price,
        'repair_added': 2100 if repair else 0,
        'rigging_added': 1400 if rigging else 0
    }

def generate_pdf_estimate(totals, pricing, service_name):
    """Generate PDF estimate document"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1  # Center
    )
    elements.append(Paragraph('CONSTRUCTION ESTIMATE', title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Customer info
    info = st.session_state.customer_info
    elements.append(Paragraph(f"<b>Customer Name:</b> {info['customer_name']}", styles['Normal']))
    elements.append(Paragraph(f"<b>Project Address:</b> {info['project_address']}", styles['Normal']))
    elements.append(Paragraph(f"<b>Sales Representative:</b> {info['sales_rep']}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Service name
    elements.append(Paragraph(f"<b>{service_name}</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Items table
    table_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
    for item_name, item_data in totals.items():
        if item_data['quantity'] > 0:
            table_data.append([
                item_name,
                f"{item_data['quantity']:.2f}",
                f"${item_data['unit_price']:.2f}",
                f"${item_data['total']:.2f}"
            ])
    
    table = Table(table_data, colWidths=[3.5*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Pricing tiers
    elements.append(Paragraph('<b>PROJECT CALCULATION</b>', styles['Heading3']))
    pricing_data = [
        ['1 Year Price', f"${pricing['one_year_price']:.2f}"],
        ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"],
        ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"],
        ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"],
        ['Day of Price', f"${pricing['day_of_price']:.2f}"],
        ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"],
    ]
    
    if pricing['repair_added'] > 0:
        pricing_data.append(['Add: Repair', f"${pricing['repair_added']:.2f}"])
    if pricing['rigging_added'] > 0:
        pricing_data.append(['Add: Rigging', f"${pricing['rigging_added']:.2f}"])
    
    pricing_data.append(['FINAL SELL PRICE', f"${pricing['final_sell_price']:.2f}"])
    
    pricing_table = Table(pricing_data, colWidths=[4*inch, 2*inch])
    pricing_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(pricing_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Main UI
st.title("🏗️ Construction Pricing Calculator")

# Service tabs
tabs = st.tabs(["Gutters & Leaders", "Stone Veneer", "Stucco Painting", "House Painting"])

# Gutters & Leaders Tab
with tabs[0]:
    st.session_state.current_service = 'gutters'
    
    st.warning("**50% deposit required for all gutter and leader projects**")
    st.error("**JOB MINIMUM IS $650 IF COMBINED WITH OTHER WORK - STAND ALONE JOB MINIMUM IS $2800**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Gutters Measurements")
        gutters_df = st.data_editor(
            st.session_state.measurements['gutters'],
            num_rows="dynamic",
            column_config={
                "Location": st.column_config.SelectboxColumn(
                    "Location",
                    options=["FRONT", "RIGHT", "BACK", "LEFT"]
                ),
                "Gutter Type": st.column_config.SelectboxColumn(
                    "Gutter Type",
                    options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'gutters']
                ),
                "LF": st.column_config.NumberColumn("LF", min_value=0, format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
        st.session_state.measurements['gutters'] = gutters_df
    
    with col2:
        st.subheader("Leaders Measurements")
        leaders_df = st.data_editor(
            st.session_state.measurements['leaders'],
            num_rows="dynamic",
            column_config={
                "Location": st.column_config.SelectboxColumn(
                    "Location",
                    options=["FRONT", "RIGHT", "BACK", "LEFT"]
                ),
                "Leader Type": st.column_config.SelectboxColumn(
                    "Leader Type",
                    options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'leaders']
                ),
                "LF": st.column_config.NumberColumn("LF", min_value=0, format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
        st.session_state.measurements['leaders'] = leaders_df
    
    with col3:
        st.subheader("Gutter Guards Measurements")
        guards_df = st.data_editor(
            st.session_state.measurements['guards'],
            num_rows="dynamic",
            column_config={
                "Location": st.column_config.SelectboxColumn(
                    "Location",
                    options=["FRONT", "RIGHT", "BACK", "LEFT"]
                ),
                "Guard Type": st.column_config.SelectboxColumn(
                    "Guard Type",
                    options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'guards']
                ),
                "LF": st.column_config.NumberColumn("LF", min_value=0, format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
        st.session_state.measurements['guards'] = guards_df
    
    # Calculate and display totals
    if st.button("Calculate Gutters & Leaders", key="calc_gutters"):
        totals, category_totals = calculate_totals('gutters')
        
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([
            {'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 
             'Total': f"${v['total']:.2f}"} 
            for k, v in totals.items() if v['quantity'] > 0
        ])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        
        st.subheader("Project Calculation")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            subtotal = category_totals['gutters'] + category_totals['leaders'] + category_totals['guards']
            pricing = calculate_pricing_tiers(subtotal)
            
            calc_df = pd.DataFrame([
                ['Gutters', f"${category_totals['gutters']:.2f}"],
                ['Leaders', f"${category_totals['leaders']:.2f}"],
                ['Gutter Guards', f"${category_totals['guards']:.2f}"],
                ['1 Year Price', f"${pricing['one_year_price']:.2f}"],
                ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"],
                ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"],
                ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"],
                ['Day of Price', f"${pricing['day_of_price']:.2f}"],
                ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"],
                ['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]
            ], columns=['Description', 'Amount'])
            
            st.dataframe(calc_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.info("### Contract Specifications\n\n"
                   "○ Work area and Location\n\n"
                   "○ Type of removal (if any)\n\n"
                   "• Install gutters and leaders on entire home\n\n"
                   "• 5\" gutters @ .27 gauge\n\n"
                   "• 2x3 leaders @ .19 gauge\n\n"
                   "• Install metal gutter screens (if any)\n\n"
                   "• Color is White")

# Stone Veneer Tab
with tabs[1]:
    st.session_state.current_service = 'stone'
    
    st.subheader("Stone Veneer Measurements")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### STONE FLATS")
        
        # Initialize with default rows if empty
        if st.session_state.measurements['stone_flats'].empty:
            st.session_state.measurements['stone_flats'] = pd.DataFrame({
                'Location': [''] * 5,
                'Width': [0.0] * 5,
                'Height': [0.0] * 5,
                'Total SF': [0.0] * 5
            })
        
        stone_flats_df = st.data_editor(
            st.session_state.measurements['stone_flats'],
            num_rows="dynamic",
            column_config={
                "Location": st.column_config.TextColumn("Location"),
                "Width": st.column_config.NumberColumn("Width", min_value=0, format="%.2f"),
                "Height": st.column_config.NumberColumn("Height", min_value=0, format="%.2f"),
                "Total SF": st.column_config.NumberColumn("Total SF", disabled=True, format="%.2f")
            },
            hide_index=True,
            use_container_width=True,
            key="stone_flats_editor"
        )
        
        # Calculate Total SF for each row
        for idx, row in stone_flats_df.iterrows():
            stone_flats_df.at[idx, 'Total SF'] = calculate_stone_sf_or_lf(row['Width'], row['Height'], 'flats')
        
        st.session_state.measurements['stone_flats'] = stone_flats_df
        st.metric("Flats SF Subtotal", f"{stone_flats_df['Total SF'].sum():.2f}")
    
    with col2:
        st.markdown("### STONE CORNERS")
        
        if st.session_state.measurements['stone_corners'].empty:
            st.session_state.measurements['stone_corners'] = pd.DataFrame({
                'Location': [''] * 5,
                'Width': [0.0] * 5,
                'Height': [0.0] * 5,
                'LF': [0.0] * 5
            })
        
        stone_corners_df = st.data_editor(
            st.session_state.measurements['stone_corners'],
            num_rows="dynamic",
            column_config={
                "Location": st.column_config.TextColumn("Location"),
                "Width": st.column_config.NumberColumn("Width", min_value=0, format="%.2f"),
                "Height": st.column_config.NumberColumn("Height", min_value=0, format="%.2f"),
                "LF": st.column_config.NumberColumn("LF", disabled=True, format="%.2f")
            },
            hide_index=True,
            use_container_width=True,
            key="stone_corners_editor"
        )
        
        # Calculate LF for each row
        for idx, row in stone_corners_df.iterrows():
            stone_corners_df.at[idx, 'LF'] = calculate_stone_sf_or_lf(row['Width'], row['Height'], 'corners')
        
        st.session_state.measurements['stone_corners'] = stone_corners_df
        st.metric("Total Corners LF", f"{stone_corners_df['LF'].sum():.2f}")
    
    with col3:
        st.markdown("### STONE SILLS")
        
        if st.session_state.measurements['stone_sills'].empty:
            st.session_state.measurements['stone_sills'] = pd.DataFrame({
                'Location': [''] * 5,
                'Width': [0.0] * 5,
                'Height': [0.0] * 5,
                'LF': [0.0] * 5
            })
        
        stone_sills_df = st.data_editor(
            st.session_state.measurements['stone_sills'],
            num_rows="dynamic",
            column_config={
                "Location": st.column_config.TextColumn("Location"),
                "Width": st.column_config.NumberColumn("Width", min_value=0, format="%.2f"),
                "Height": st.column_config.NumberColumn("Height", min_value=0, format="%.2f"),
                "LF": st.column_config.NumberColumn("LF", disabled=True, format="%.2f")
            },
            hide_index=True,
            use_container_width=True,
            key="stone_sills_editor"
        )
        
        # Calculate LF for each row
        for idx, row in stone_sills_df.iterrows():
            stone_sills_df.at[idx, 'LF'] = calculate_stone_sf_or_lf(row['Width'], row['Height'], 'sills')
        
        st.session_state.measurements['stone_sills'] = stone_sills_df
        st.metric("Total Sills LF", f"{stone_sills_df['LF'].sum():.2f}")
    
    # Stone Veneer Calculations
    if st.button("Calculate Stone Veneer", key="calc_stone"):
        totals, _ = calculate_totals('stone')
        
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([
            {'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 
             'Total': f"${v['total']:.2f}"} 
            for k, v in totals.items() if v['quantity'] > 0
        ])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        
        st.subheader("Project Calculation")
        subtotal = sum([v['total'] for v in totals.values()])
        subtotal_with_delivery = subtotal + SERVICE_DATA['stone']['delivery_fee']
        pricing = calculate_pricing_tiers(subtotal_with_delivery)
        
        calc_df = pd.DataFrame([
            ['Subtotal', f"${subtotal:.2f}"],
            ['Delivery Fee', f"${SERVICE_DATA['stone']['delivery_fee']:.2f}"],
            ['1 Year Price', f"${pricing['one_year_price']:.2f}"],
            ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"],
            ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"],
            ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"],
            ['Day of Price', f"${pricing['day_of_price']:.2f}"],
            ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"],
            ['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]
        ], columns=['Description', 'Amount'])
        
        st.dataframe(calc_df, use_container_width=True, hide_index=True)
        
        st.info("### Contract Specifications\n\n"
               "○ Work area and Location\n\n"
               "○ Type of removal (if any)\n\n"
               "○ Layers of removal (if any)\n\n"
               "○ Any other special requirements\n\n"
               "• Install two layers of jumbo tex felt paper (only if over plywood)\n\n"
               "• Install wire lathe\n\n"
               "• Install metal j-channel where required\n\n"
               "• Install cement scratch coat\n\n"
               "• Install stone flats\n\n"
               "• Install stone corners (only when required)\n\n"
               "• Install stone sill (only when required)\n\n"
               "• Stone to be installed as \"1/2\" joint\n\n"
               "• Caulk where required\n\n"
               "• Install mortar into joints as required\n\n"
               "• Dispose of debris\n\n"
               "**Additional Requirements:**\n\n"
               "• Stone Selection\n\n"
               "• Sill Color\n\n"
               "• Joint Color")

# Stucco Painting Tab
with tabs[2]:
    st.session_state.current_service = 'stucco'
    
    st.subheader("Stucco Painting Measurements")
    stucco_df = st.data_editor(
        st.session_state.measurements['stucco'],
        num_rows="dynamic",
        column_config={
            "Location": st.column_config.SelectboxColumn(
                "Location",
                options=["FRONT", "RIGHT", "BACK", "LEFT"]
            ),
            "Item Type": st.column_config.SelectboxColumn(
                "Item Type",
                options=list(SERVICE_DATA['stucco']['items'].keys())
            ),
            "SF": st.column_config.NumberColumn("SF", min_value=0, format="%.2f")
        },
        hide_index=True,
        use_container_width=True
    )
    st.session_state.measurements['stucco'] = stucco_df
    
    st.subheader("Miscellaneous Items")
    misc_cols = st.columns(2)
    
    for idx, (misc_name, misc_data) in enumerate(SERVICE_DATA['stucco']['miscellaneous'].items()):
        col = misc_cols[idx % 2]
        with col:
            qty = st.number_input(
                f"{misc_name} ({misc_data['unit']}) - ${misc_data['price']}",
                min_value=0.0,
                value=st.session_state.misc_quantities.get(misc_name, 0.0),
                step=0.1,
                key=f"misc_{misc_name}"
            )
            st.session_state.misc_quantities[misc_name] = qty
    
    st.subheader("Minimums (FOR WORK ON STANDARD 2 1/2 STORY HOMES LESS THAN 26')")
    minimums_df = pd.DataFrame([
        ['LOXON', '$4,200'],
        ['CLEAR SEALER', '$3,500'],
        ['WOODPECKER HOLES (INCLUDES UP TO 6 HOLES) ADD $500 PER HOLE', '$3,500'],
        ['BCMA', '$4,200'],
        ['SPOT POINTING', '$4,900'],
        ['FULL POINTING', '$5,600'],
        ['CAULKING', '$5,600']
    ], columns=['Service', 'Amount'])
    st.dataframe(minimums_df, use_container_width=True, hide_index=True)
    
    col1, col2 = st.columns(2)
    with col1:
        repair_addon = st.checkbox("Add Repair - $2,100", key="stucco_repair")
    with col2:
        rigging_addon = st.checkbox("Add Rigging - $1,400", key="stucco_rigging")
    
    if st.button("Calculate Stucco Painting", key="calc_stucco"):
        totals, _ = calculate_totals('stucco')
        
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([
            {'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 
             'Total': f"${v['total']:.2f}"} 
            for k, v in totals.items() if v['quantity'] > 0
        ])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        
        st.subheader("Project Calculation")
        subtotal = sum([v['total'] for v in totals.values()])
        pricing = calculate_pricing_tiers(subtotal, repair_addon, rigging_addon)
        
        calc_df = pd.DataFrame([
            ['1 Year Price', f"${pricing['one_year_price']:.2f}"],
            ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"],
            ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"],
            ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"],
            ['Day of Price', f"${pricing['day_of_price']:.2f}"],
            ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"],
        ], columns=['Description', 'Amount'])
        
        if repair_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Repair', f"${pricing['repair_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        if rigging_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Rigging', f"${pricing['rigging_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        
        calc_df = pd.concat([calc_df, pd.DataFrame([['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]], columns=['Description', 'Amount'])], ignore_index=True)
        
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

# House Painting Tab
with tabs[3]:
    st.session_state.current_service = 'painting'
    
    st.subheader("House Painting Measurements")
    painting_df = st.data_editor(
        st.session_state.measurements['painting'],
        num_rows="dynamic",
        column_config={
            "Location": st.column_config.SelectboxColumn(
                "Location",
                options=["FRONT", "RIGHT", "BACK", "LEFT"]
            ),
            "Item Type": st.column_config.SelectboxColumn(
                "Item Type",
                options=list(SERVICE_DATA['painting']['items'].keys())
            ),
            "SF": st.column_config.NumberColumn("SF", min_value=0, format="%.2f")
        },
        hide_index=True,
        use_container_width=True
    )
    st.session_state.measurements['painting'] = painting_df
    
    st.subheader("Minimums (FOR WORK ON STANDARD 2 1/2 STORY HOMES LESS THAN 26')")
    minimums_df = pd.DataFrame([
        ['LOXON', '$4,200'],
        ['CLEAR SEALER', '$3,500'],
        ['WOODPECKER HOLES (INCLUDES UP TO 6 HOLES) ADD $500 PER HOLE', '$3,500'],
        ['BCMA', '$4,200'],
        ['SPOT POINTING', '$4,900'],
        ['FULL POINTING', '$5,600'],
        ['CAULKING', '$5,600']
    ], columns=['Service', 'Amount'])
    st.dataframe(minimums_df, use_container_width=True, hide_index=True)
    
    col1, col2 = st.columns(2)
    with col1:
        repair_addon = st.checkbox("Add Repair - $2,100", key="painting_repair")
    with col2:
        rigging_addon = st.checkbox("Add Rigging - $1,400", key="painting_rigging")
    
    if st.button("Calculate House Painting", key="calc_painting"):
        totals, _ = calculate_totals('painting')
        
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([
            {'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 
             'Total': f"${v['total']:.2f}"} 
            for k, v in totals.items() if v['quantity'] > 0
        ])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        
        st.subheader("Project Calculation")
        subtotal = sum([v['total'] for v in totals.values()])
        pricing = calculate_pricing_tiers(subtotal, repair_addon, rigging_addon)
        
        calc_df = pd.DataFrame([
            ['1 Year Price', f"${pricing['one_year_price']:.2f}"],
            ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"],
            ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"],
            ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"],
            ['Day of Price', f"${pricing['day_of_price']:.2f}"],
            ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"],
        ], columns=['Description', 'Amount'])
        
        if repair_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Repair', f"${pricing['repair_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        if rigging_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Rigging', f"${pricing['rigging_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        
        calc_df = pd.concat([calc_df, pd.DataFrame([['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]], columns=['Description', 'Amount'])], ignore_index=True)
        
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

# Generate Document Section
st.divider()
st.header("Generate Estimate Document")

col1, col2, col3 = st.columns(3)

with col1:
    customer_name = st.text_input("Customer Name *", value=st.session_state.customer_info['customer_name'])
    st.session_state.customer_info['customer_name'] = customer_name

with col2:
    project_address = st.text_input("Project Address *", value=st.session_state.customer_info['project_address'])
    st.session_state.customer_info['project_address'] = project_address

with col3:
    sales_rep = st.text_input("Sales Representative *", value=st.session_state.customer_info['sales_rep'])
    st.session_state.customer_info['sales_rep'] = sales_rep

if st.button("Generate PDF Estimate", type="primary", use_container_width=True):
    if not customer_name or not project_address or not sales_rep:
        st.error("Please fill in all required fields (Customer Name, Project Address, Sales Representative)")
    else:
        with st.spinner("Generating PDF estimate..."):
            # Get current service totals
            totals, category_totals = calculate_totals(st.session_state.current_service)
            
            # Calculate pricing
            subtotal = sum([v['total'] for v in totals.values()])
            
            # Add delivery fee for stone
            if st.session_state.current_service == 'stone':
                subtotal += SERVICE_DATA['stone']['delivery_fee']
            
            # Check for add-ons
            repair = False
            rigging = False
            if st.session_state.current_service == 'stucco':
                repair = st.session_state.get('stucco_repair', False)
                rigging = st.session_state.get('stucco_rigging', False)
            elif st.session_state.current_service == 'painting':
                repair = st.session_state.get('painting_repair', False)
                rigging = st.session_state.get('painting_rigging', False)
            
            pricing = calculate_pricing_tiers(subtotal, repair, rigging)
            
            # Generate PDF
            service_name = SERVICE_DATA[st.session_state.current_service]['name']
            pdf_buffer = generate_pdf_estimate(totals, pricing, service_name)
            
            # Create filename
            filename = f"{customer_name}_{sales_rep}_{datetime.now().strftime('%Y%m%d')}.pdf".replace(" ", "_")
            
            st.success("PDF generated successfully!")
            st.download_button(
                label="Download PDF Estimate",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

# Footer
st.divider()
st.caption("Construction Pricing Calculator v3.0 | Powered by Streamlit")