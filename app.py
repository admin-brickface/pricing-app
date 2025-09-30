import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

st.set_page_config(
    page_title="Construction Pricing Calculator",
    page_icon="🏗️",
    layout="wide"
)

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
            'Leader 3" Round Corrugated - White': {'price': 47, 'unit': 'LF', 'category': 'leaders'},
            'Extra Gauge (0.032 gauge) Leader': {'price': 1, 'unit': 'LF', 'category': 'leaders'},
            'Shur-flow 5" (white)': {'price': 15, 'unit': 'LF', 'category': 'guards'},
            'Shur-flow 5" (black or aluminum)': {'price': 16, 'unit': 'LF', 'category': 'guards'},
            'Shur-flow 6" (white)': {'price': 16, 'unit': 'LF', 'category': 'guards'},
            'Shur-flow 6" (black or aluminum)': {'price': 18, 'unit': 'LF', 'category': 'guards'},
            'Screen 5"': {'price': 10, 'unit': 'LF', 'category': 'guards'},
            'Screen 6"': {'price': 12, 'unit': 'LF', 'category': 'guards'},
            'Leafshelter 6" - White': {'price': 18, 'unit': 'LF', 'category': 'guards'},
            'Leafshelter 6" - All Colors': {'price': 21, 'unit': 'LF', 'category': 'guards'},
            'Strap Hangers per LF': {'price': 4, 'unit': 'LF', 'category': 'guards'}
        },
        'notices': [
            '50% deposit required for all gutter and leader projects',
            'JOB MINIMUM IS $650 IF COMBINED WITH OTHER WORK - STAND ALONE JOB MINIMUM IS $1,150'
        ],
        'contract_specs': [
            'Work area and Location',
            'Final location for the leaders',
            'Color',
            'Existing splash block(s) or extension(s)',
            'Final price, payment schedule, and how to pay'
        ]
    },
    'stone': {
        'name': 'Stone Veneer',
        'items': {
            'Stone Flats': {'price': 28, 'unit': 'SF'},
            'Stone Corners': {'price': 28, 'unit': 'LF'},
            'Stone Sills': {'price': 28, 'unit': 'LF'}
        },
        'delivery_fee': 1100,
        'contract_specs': [
            'Work area and location',
            'Color & Style',
            'Mortar Color',
            'Payment schedule and how to pay'
        ]
    },
    'stucco': {
        'name': 'Stucco Painting',
        'items': {
            'Wall': {'price': 8.36, 'unit': 'SF'},
            'Soffit': {'price': 8.36, 'unit': 'SF'},
            'Column': {'price': 8.36, 'unit': 'SF'},
            'Beam': {'price': 8.36, 'unit': 'SF'}
        },
        'misc_items': {
            'EIFS Repair': {'price': 60, 'unit': 'SF'},
            'BCMA (Fiberglass, Basecoat, Acrylic Stucco)': {'price': 17.59, 'unit': 'SF'},
            'Remove and Re-Install Existing Shutters': {'price': 145, 'unit': 'Pair'},
            'Remove, Paint and Re-Install Shutters': {'price': 290, 'unit': 'Pair'},
            'Stainless Steel Chimney Cover': {'price': 1509, 'unit': 'Item'},
            'Plywood (demo, debris, install 1 sheet) 32sf': {'price': 439, 'unit': 'Item'},
            'Remove and Re-Install Existing Gutters': {'price': 6, 'unit': 'LF'},
            'Additional Rigging (Caulking Only)': {'price': 435, 'unit': 'Side'},
            'Clear Sealer, Ladders, Powerwash': {'price': 7, 'unit': 'SF'},
            'Additional Heavy Duty Powerwash': {'price': 2, 'unit': 'SF'},
            'Additional stucco crack repair above 50lf': {'price': 7, 'unit': 'LF'},
            'Spot Point Brick': {'price': 29, 'unit': 'SF'},
            'Full Cut and Re-Point (Under 500sf)': {'price': 29, 'unit': 'SF'}
        },
        'minimums': {
            'LOXON PAINTING': 5600,
            'CAULKING': 5600
        }
    },
    'painting': {
        'name': 'House Painting',
        'items': {
            'Exterior Wall': {'price': 4.18, 'unit': 'SF'},
            'Trim': {'price': 4.18, 'unit': 'LF'},
            'Door': {'price': 125, 'unit': 'Each'},
            'Window': {'price': 75, 'unit': 'Each'}
        },
        'minimums': {
            'HOUSE PAINTING': 5600
        }
    }
}

def calculate_stone_sf_or_lf(width, height, item_type='flats'):
    if pd.isna(width) or pd.isna(height):
        return 0
    width = float(width)
    height = float(height)
    if item_type == 'flats':
        return (width * height) / 144
    else:
        return width / 12

def calculate_totals(service):
    totals = {}
    service_items = SERVICE_DATA[service]['items']
    
    if service == 'gutters':
        for idx, row in st.session_state.measurements['gutters'].iterrows():
            if pd.notna(row['Gutter Type']) and pd.notna(row['LF']):
                item = row['Gutter Type']
                if item in service_items and service_items[item]['category'] == 'gutters':
                    if item not in totals:
                        totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                    totals[item]['quantity'] += float(row['LF'])
        
        for idx, row in st.session_state.measurements['leaders'].iterrows():
            if pd.notna(row['Leader Type']) and pd.notna(row['LF']):
                item = row['Leader Type']
                if item in service_items and service_items[item]['category'] == 'leaders':
                    if item not in totals:
                        totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                    totals[item]['quantity'] += float(row['LF'])
        
        for idx, row in st.session_state.measurements['guards'].iterrows():
            if pd.notna(row['Guard Type']) and pd.notna(row['LF']):
                item = row['Guard Type']
                if item in service_items and service_items[item]['category'] == 'guards':
                    if item not in totals:
                        totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                    totals[item]['quantity'] += float(row['LF'])
    
    elif service == 'stone':
        for idx, row in st.session_state.measurements['stone_flats'].iterrows():
            if pd.notna(row['Total SF']):
                item = 'Stone Flats'
                if item not in totals:
                    totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                totals[item]['quantity'] += float(row['Total SF'])
        
        for idx, row in st.session_state.measurements['stone_corners'].iterrows():
            if pd.notna(row['LF']):
                item = 'Stone Corners'
                if item not in totals:
                    totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                totals[item]['quantity'] += float(row['LF'])
        
        for idx, row in st.session_state.measurements['stone_sills'].iterrows():
            if pd.notna(row['LF']):
                item = 'Stone Sills'
                if item not in totals:
                    totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                totals[item]['quantity'] += float(row['LF'])
    
    elif service == 'stucco':
        for idx, row in st.session_state.measurements['stucco'].iterrows():
            if pd.notna(row['Item Type']) and pd.notna(row['SF']):
                item = row['Item Type']
                if item in service_items:
                    if item not in totals:
                        totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                    totals[item]['quantity'] += float(row['SF'])
    
    elif service == 'painting':
        for idx, row in st.session_state.measurements['painting'].iterrows():
            if pd.notna(row['Item Type']) and pd.notna(row['SF']):
                item = row['Item Type']
                if item in service_items:
                    if item not in totals:
                        totals[item] = {'quantity': 0, 'unit_price': service_items[item]['price'], 'total': 0}
                    totals[item]['quantity'] += float(row['SF'])
    
    for item in totals:
        totals[item]['total'] = totals[item]['quantity'] * totals[item]['unit_price']
    
    return totals, sum([t['total'] for t in totals.values()])

def calculate_pricing_tiers(subtotal, add_repair=False, add_rigging=False):
    one_year_price = subtotal
    deduct_10_1 = one_year_price * 0.10
    thirty_day_price = one_year_price - deduct_10_1
    deduct_10_2 = thirty_day_price * 0.10
    day_of_price = thirty_day_price - deduct_10_2
    deduct_3 = day_of_price * 0.03
    final_price = day_of_price - deduct_3
    if add_repair:
        final_price += 2100
    if add_rigging:
        final_price += 1400
    return {
        'one_year_price': one_year_price,
        'deduct_10_1': deduct_10_1,
        'thirty_day_price': thirty_day_price,
        'deduct_10_2': deduct_10_2,
        'day_of_price': day_of_price,
        'deduct_3': deduct_3,
        'repair_added': 2100 if add_repair else 0,
        'rigging_added': 1400 if add_rigging else 0,
        'final_sell_price': final_price
    }

def generate_pdf(service, totals, pricing, customer_info):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2E5CB8'), spaceAfter=30, alignment=1)
    story.append(Paragraph(f"{SERVICE_DATA[service]['name']} Estimate", title_style))
    info_data = [['Customer:', customer_info['customer_name']], ['Address:', customer_info['project_address']], ['Sales Rep:', customer_info['sales_rep']], ['Date:', datetime.now().strftime('%B %d, %Y')]]
    info_table = Table(info_data, colWidths=[1.5*inch, 4.5*inch])
    info_table.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 10), ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2E5CB8')), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 12)]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Items", styles['Heading2']))
    items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
    for item, values in totals.items():
        if values['quantity'] > 0:
            items_data.append([item, f"{values['quantity']:.2f}", f"${values['unit_price']:.2f}", f"${values['total']:.2f}"])
    items_table = Table(items_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    items_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5CB8')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('ALIGN', (1, 0), (-1, -1), 'RIGHT'), ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11), ('FONT', (0, 1), (-1, -1), 'Helvetica', 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Pricing Calculation", styles['Heading2']))
    pricing_data = [['1 Year Price', f"${pricing['one_year_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"], ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"], ['Day of Price', f"${pricing['day_of_price']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"]]
    if pricing['repair_added'] > 0:
        pricing_data.append(['Add: Repair', f"${pricing['repair_added']:.2f}"])
    if pricing['rigging_added'] > 0:
        pricing_data.append(['Add: Rigging', f"${pricing['rigging_added']:.2f}"])
    pricing_data.append(['FINAL SELL PRICE', f"${pricing['final_sell_price']:.2f}"])
    pricing_table = Table(pricing_data, colWidths=[4*inch, 2*inch])
    pricing_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONT', (0, 0), (-1, -2), 'Helvetica', 10), ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 12), ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2E5CB8')), ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2E5CB8')), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
    story.append(pricing_table)
    if service in ['gutters', 'stone']:
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Contract Specifications", styles['Heading2']))
        for spec in SERVICE_DATA[service]['contract_specs']:
            story.append(Paragraph(f"○ {spec}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    doc.build(story)
    buffer.seek(0)
    return buffer

st.title("🏗️ Construction Pricing Calculator")
st.markdown("---")

tabs = st.tabs(["Gutters & Leaders", "Stone Veneer", "Stucco Painting", "House Painting"])

with tabs[0]:
    st.session_state.current_service = 'gutters'
    st.subheader("Gutter Measurements")
    gutters_df = st.data_editor(st.session_state.measurements['gutters'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Gutter Type": st.column_config.SelectboxColumn("Gutter Type", options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'gutters']), "LF": st.column_config.NumberColumn("LF", format="%.2f")}, hide_index=True, use_container_width=True, key="gutters_editor")
    st.session_state.measurements['gutters'] = gutters_df
    st.subheader("Leader Measurements")
    leaders_df = st.data_editor(st.session_state.measurements['leaders'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Leader Type": st.column_config.SelectboxColumn("Leader Type", options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'leaders']), "LF": st.column_config.NumberColumn("LF", format="%.2f")}, hide_index=True, use_container_width=True, key="leaders_editor")
    st.session_state.measurements['leaders'] = leaders_df
    st.subheader("Gutter Guard Measurements")
    guards_df = st.data_editor(st.session_state.measurements['guards'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Guard Type": st.column_config.SelectboxColumn("Guard Type", options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'guards']), "LF": st.column_config.NumberColumn("LF", format="%.2f")}, hide_index=True, use_container_width=True, key="guards_editor")
    st.session_state.measurements['guards'] = guards_df
    st.info("\n\n".join([f"**{notice}**" for notice in SERVICE_DATA['gutters']['notices']]))
    if st.button("Calculate Gutters & Leaders", key="calc_gutters"):
        totals, subtotal = calculate_totals('gutters')
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([{'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 'Total': f"${v['total']:.2f}"} for k, v in totals.items() if v['quantity'] > 0])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        st.subheader("Project Calculation")
        pricing = calculate_pricing_tiers(subtotal)
        calc_df = pd.DataFrame([['1 Year Price', f"${pricing['one_year_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"], ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"], ['Day of Price', f"${pricing['day_of_price']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"], ['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]], columns=['Description', 'Amount'])
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

with tabs[1]:
    st.session_state.current_service = 'stone'
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Stone Flats")
        stone_flats_df = st.data_editor(st.session_state.measurements['stone_flats'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Width": st.column_config.NumberColumn("Width (in)", format="%.2f"), "Height": st.column_config.NumberColumn("Height (in)", format="%.2f"), "Total SF": st.column_config.NumberColumn("Total SF", disabled=True, format="%.2f")}, hide_index=True, use_container_width=True, key="stone_flats_editor")
        for idx, row in stone_flats_df.iterrows():
            stone_flats_df.at[idx, 'Total SF'] = calculate_stone_sf_or_lf(row['Width'], row['Height'], 'flats')
        st.session_state.measurements['stone_flats'] = stone_flats_df
        st.metric("Total Flats SF", f"{stone_flats_df['Total SF'].sum():.2f}")
    with col2:
        st.subheader("Stone Corners")
        stone_corners_df = st.data_editor(st.session_state.measurements['stone_corners'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Width": st.column_config.NumberColumn("Width (in)", format="%.2f"), "Height": st.column_config.NumberColumn("Height (in)", format="%.2f"), "LF": st.column_config.NumberColumn("LF", disabled=True, format="%.2f")}, hide_index=True, use_container_width=True, key="stone_corners_editor")
        for idx, row in stone_corners_df.iterrows():
            stone_corners_df.at[idx, 'LF'] = calculate_stone_sf_or_lf(row['Width'], row['Height'], 'corners')
        st.session_state.measurements['stone_corners'] = stone_corners_df
        st.metric("Total Corners LF", f"{stone_corners_df['LF'].sum():.2f}")
    with col3:
        st.subheader("Stone Sills")
        stone_sills_df = st.data_editor(st.session_state.measurements['stone_sills'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Width": st.column_config.NumberColumn("Width (in)", format="%.2f"), "Height": st.column_config.NumberColumn("Height (in)", format="%.2f"), "LF": st.column_config.NumberColumn("LF", disabled=True, format="%.2f")}, hide_index=True, use_container_width=True, key="stone_sills_editor")
        for idx, row in stone_sills_df.iterrows():
            stone_sills_df.at[idx, 'LF'] = calculate_stone_sf_or_lf(row['Width'], row['Height'], 'sills')
        st.session_state.measurements['stone_sills'] = stone_sills_df
        st.metric("Total Sills LF", f"{stone_sills_df['LF'].sum():.2f}")
    if st.button("Calculate Stone Veneer", key="calc_stone"):
        totals, subtotal = calculate_totals('stone')
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([{'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 'Total': f"${v['total']:.2f}"} for k, v in totals.items() if v['quantity'] > 0])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        st.subheader("Project Calculation")
        subtotal_with_delivery = subtotal + SERVICE_DATA['stone']['delivery_fee']
        pricing = calculate_pricing_tiers(subtotal_with_delivery)
        calc_df = pd.DataFrame([['Subtotal', f"${subtotal:.2f}"], ['Delivery Fee', f"${SERVICE_DATA['stone']['delivery_fee']:.2f}"], ['1 Year Price', f"${pricing['one_year_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"], ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"], ['Day of Price', f"${pricing['day_of_price']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"], ['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]], columns=['Description', 'Amount'])
        st.dataframe(calc_df, use_container_width=True, hide_index=True)
        st.info("### Contract Specifications\n\n" + "\n\n".join([f"○ {spec}" for spec in SERVICE_DATA['stone']['contract_specs']]))

with tabs[2]:
    st.session_state.current_service = 'stucco'
    st.subheader("Stucco Painting Measurements")
    stucco_df = st.data_editor(st.session_state.measurements['stucco'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Item Type": st.column_config.SelectboxColumn("Item Type", options=list(SERVICE_DATA['stucco']['items'].keys())), "SF": st.column_config.NumberColumn("SF", format="%.2f")}, hide_index=True, use_container_width=True, key="stucco_editor")
    st.session_state.measurements['stucco'] = stucco_df
    st.subheader("Miscellaneous Items")
    misc_cols = st.columns(2)
    misc_index = 0
    for item, details in SERVICE_DATA['stucco']['misc_items'].items():
        with misc_cols[misc_index % 2]:
            quantity = st.number_input(f"{item} ({details['unit']}) - ${details['price']:.2f}", min_value=0.0, value=st.session_state.misc_quantities.get(item, 0.0), step=1.0, key=f"misc_{item}")
            st.session_state.misc_quantities[item] = quantity
        misc_index += 1
    st.subheader("Service Minimums")
    minimums_df = pd.DataFrame([['LOXON PAINTING', f"${SERVICE_DATA['stucco']['minimums']['LOXON PAINTING']:,}"], ['CAULKING', f"${SERVICE_DATA['stucco']['minimums']['CAULKING']:,}"]], columns=['Service', 'Minimum Amount'])
    st.dataframe(minimums_df, use_container_width=True, hide_index=True)
    col1, col2 = st.columns(2)
    with col1:
        repair_addon = st.checkbox("Add Repair - $2,100", key="stucco_repair")
    with col2:
        rigging_addon = st.checkbox("Add Rigging - $1,400", key="stucco_rigging")
    if st.button("Calculate Stucco Painting", key="calc_stucco"):
        totals, subtotal = calculate_totals('stucco')
        for item, quantity in st.session_state.misc_quantities.items():
            if quantity > 0:
                price = SERVICE_DATA['stucco']['misc_items'][item]['price']
                totals[item] = {'quantity': quantity, 'unit_price': price, 'total': quantity * price}
                subtotal += quantity * price
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([{'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 'Total': f"${v['total']:.2f}"} for k, v in totals.items() if v['quantity'] > 0])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        st.subheader("Project Calculation")
        pricing = calculate_pricing_tiers(subtotal, repair_addon, rigging_addon)
        calc_df = pd.DataFrame([['1 Year Price', f"${pricing['one_year_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"], ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"], ['Day of Price', f"${pricing['day_of_price']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"]], columns=['Description', 'Amount'])
        if repair_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Repair', f"${pricing['repair_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        if rigging_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Rigging', f"${pricing['rigging_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        calc_df = pd.concat([calc_df, pd.DataFrame([['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]], columns=['Description', 'Amount'])], ignore_index=True)
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

with tabs[3]:
    st.session_state.current_service = 'painting'
    st.subheader("House Painting Measurements")
    painting_df = st.data_editor(st.session_state.measurements['painting'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn("Location", options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Item Type": st.column_config.SelectboxColumn("Item Type", options=list(SERVICE_DATA['painting']['items'].keys())), "SF": st.column_config.NumberColumn("Quantity/SF", format="%.2f")}, hide_index=True, use_container_width=True, key="painting_editor")
    st.session_state.measurements['painting'] = painting_df
    st.subheader("Service Minimums")
    minimums_df = pd.DataFrame([['HOUSE PAINTING', f"${SERVICE_DATA['painting']['minimums']['HOUSE PAINTING']:,}"]], columns=['Service', 'Minimum Amount'])
    st.dataframe(minimums_df, use_container_width=True, hide_index=True)
    col1, col2 = st.columns(2)
    with col1:
        repair_addon = st.checkbox("Add Repair - $2,100", key="painting_repair")
    with col2:
        rigging_addon = st.checkbox("Add Rigging - $1,400", key="painting_rigging")
    if st.button("Calculate House Painting", key="calc_painting"):
        totals, subtotal = calculate_totals('painting')
        st.subheader("Pricing Summary")
        pricing_df = pd.DataFrame([{'Item': k, 'Quantity': f"{v['quantity']:.2f}", 'Unit Price': f"${v['unit_price']:.2f}", 'Total': f"${v['total']:.2f}"} for k, v in totals.items() if v['quantity'] > 0])
        st.dataframe(pricing_df, use_container_width=True, hide_index=True)
        st.subheader("Project Calculation")
        pricing = calculate_pricing_tiers(subtotal, repair_addon, rigging_addon)
        calc_df = pd.DataFrame([['1 Year Price', f"${pricing['one_year_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_1']:.2f})"], ['30 Day Price', f"${pricing['thirty_day_price']:.2f}"], ['Deduct 10%', f"(${pricing['deduct_10_2']:.2f})"], ['Day of Price', f"${pricing['day_of_price']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${pricing['deduct_3']:.2f})"]], columns=['Description', 'Amount'])
        if repair_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Repair', f"${pricing['repair_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        if rigging_addon:
            calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Rigging', f"${pricing['rigging_added']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        calc_df = pd.concat([calc_df, pd.DataFrame([['**FINAL SELL PRICE**', f"**${pricing['final_sell_price']:.2f}**"]], columns=['Description', 'Amount'])], ignore_index=True)
        st.dataframe(calc_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.header("Generate PDF Estimate")
col1, col2, col3 = st.columns(3)
with col1:
    customer_name = st.text_input("Customer Name", value=st.session_state.customer_info['customer_name'])
    st.session_state.customer_info['customer_name'] = customer_name
with col2:
    project_address = st.text_input("Project Address", value=st.session_state.customer_info['project_address'])
    st.session_state.customer_info['project_address'] = project_address
with col3:
    sales_rep = st.text_input("Sales Representative", value=st.session_state.customer_info['sales_rep'])
    st.session_state.customer_info['sales_rep'] = sales_rep

if st.button("Generate PDF Estimate", type="primary", use_container_width=True):
    if not customer_name or not project_address or not sales_rep:
        st.error("Please fill in all customer information fields.")
    else:
        with st.spinner("Generating PDF..."):
            service = st.session_state.current_service
            totals, subtotal = calculate_totals(service)
            if service == 'stucco':
                for item, quantity in st.session_state.misc_quantities.items():
                    if quantity > 0:
                        price = SERVICE_DATA['stucco']['misc_items'][item]['price']
                        totals[item] = {'quantity': quantity, 'unit_price': price, 'total': quantity * price}
                        subtotal += quantity * price
            repair = st.session_state.get(f'{service}_repair', False)
            rigging = st.session_state.get(f'{service}_rigging', False)
            if service == 'stone':
                subtotal += SERVICE_DATA['stone']['delivery_fee']
            pricing = calculate_pricing_tiers(subtotal, repair, rigging)
            pdf_buffer = generate_pdf(service, totals, pricing, st.session_state.customer_info)
            filename = f"{customer_name.replace(' ', '_')}_{SERVICE_DATA[service]['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.success("PDF generated successfully!")
            st.download_button(label="Download PDF Estimate", data=pdf_buffer, file_name=filename, mime="application/pdf", type="primary", use_container_width=True)

st.divider()
st.caption("Construction Pricing Calculator v3.0 | Powered by Streamlit")
