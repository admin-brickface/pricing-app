import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

st.set_page_config(page_title="Garden State Brickface & Siding Pricing Calculator", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
.stApp {
background-color: #FFFFFF;
color: #000000;
}
.stTextInput input, .stNumberInput input, .stSelectbox select {
background-color: #F0F2F6;
color: #000000;
}
.stDataFrame, [data-testid="stDataFrame"] {
background-color: #FFFFFF;
}
.stDataFrame table {
background-color: #F0F2F6 !important;
}
.stDataFrame thead tr th {
background-color: #E8EAF0 !important;
color: #000000 !important;
}
.stDataFrame tbody tr {
background-color: #F0F2F6 !important;
}
h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
color: #000000 !important;
}
.stTabs [data-baseweb="tab-list"] {
background-color: #F0F2F6;
}
.stTabs [data-baseweb="tab"] {
color: #000000;
}
.stButton button {
background-color: #FF4B4B;
color: #FFFFFF;
}
[data-testid="stMetricValue"] {
color: #000000;
}
p, span, label {
color: #000000 !important;
}
hr {
border-color: #E0E0E0;
}
</style>
""", unsafe_allow_html=True)

if 'current_service' not in st.session_state:
    st.session_state.current_service = 'gutters'

if 'measurements' not in st.session_state:
    st.session_state.measurements = {
        'gutters': pd.DataFrame(columns=['Location', 'Gutter Type', 'LF']),
        'leaders': pd.DataFrame(columns=['Location', 'Leader Type', 'LF']),
        'guards': pd.DataFrame(columns=['Location', 'Guard Type', 'LF'])
    }

if 'stone_measurements' not in st.session_state:
    st.session_state.stone_measurements = {
        'flats': pd.DataFrame([[''] * 4 for _ in range(12)], columns=['Location', 'Width', 'Height', 'Total SF']),
        'corners': pd.DataFrame([[''] * 2 for _ in range(12)], columns=['Location', 'LF']),
        'sills': pd.DataFrame([[''] * 2 for _ in range(12)], columns=['Location', 'LF']),
        'outs': pd.DataFrame([[''] * 4 for _ in range(8)], columns=['Location', 'Width', 'Height', 'Total'])
    }

if 'stucco_measurements' not in st.session_state:
    st.session_state.stucco_measurements = {
        'walls': pd.DataFrame([[''] * 5 for _ in range(28)], columns=['Location', 'Width', 'x', 'Height', 'Total SF']),
        'window_trim': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'LF']),
        'door_trim': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'LF']),
        'soffit': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'LF']),
        'fascia': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'LF']),
        'quions': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'Quantity']),
        'other_trim': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'Quantity'])
    }

if 'painting_measurements' not in st.session_state:
    st.session_state.painting_measurements = {
        'walls': pd.DataFrame([[''] * 5 for _ in range(28)], columns=['Location', 'Width', 'x', 'Height', 'Total SF']),
        'window_trim': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'Openings']),
        'door_trim': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'Openings']),
        'soffit': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'LF']),
        'fascia': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'LF']),
        'entry_doors': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'Openings']),
        'garage_doors': pd.DataFrame([[''] * 2 for _ in range(8)], columns=['Location', 'Openings'])
    }

if 'stone_pricing' not in st.session_state:
    st.session_state.stone_pricing = {
        'demolition': pd.DataFrame([['Remove vinyl or aluminum siding', '', 237], ['Remove wood siding (clapboard)', '', 267], ['Remove wood siding (wood shake)', '', 297], ['Remove EIFS up to 2" only', '', 400]], columns=['Description', 'Per Square', 'Price']),
        'debris': pd.DataFrame([['Debris removal under 4 squares (REQUIRED even if no demo)', '', 830], ['10 yard dumpster (removal from 4 to 10 squares)', '', 1542], ['20 yard dumpster (removal from 11 to 20 squares)', '', 1868]], columns=['Description', 'Quantity', 'Price']),
        'misc': pd.DataFrame([['Wrap Corner 4" (Wood or Vinyl Siding)', 'Per 8\' Corner', '', 297], ['Limestone Treads (up to 12" Deep)', 'LF', '', 128], ['Limestone Treads (up to 14" Deep)', 'LF', '', 144], ['Cement Pad (Up to 20sf) Demo/New', 'Per Item', '', 890], ['Chimney Scaffolding Fee', 'Full chimney or on roof', '', 741], ['Stainless Steel Chimney Cover', 'Per Item', '', 1605], ['1/2" Plywood Replacement', 'Per Item', '', 374]], columns=['Description', 'Unit', 'SF/LF/Q', 'Price'])
    }

if 'customer_info' not in st.session_state:
    st.session_state.customer_info = {'customer_name': '', 'project_address': '', 'sales_rep': ''}

SERVICE_DATA = {
    'gutters': {
        'name': 'Gutters and Leaders',
        'items': {
            'Gutter 5" white': {'price': 13, 'category': 'gutters'},
            'Gutter 5" all colors': {'price': 15, 'category': 'gutters'},
            'Gutter 6" white': {'price': 18, 'category': 'gutters'},
            'Gutter 6" all colors': {'price': 19, 'category': 'gutters'},
            'Extra Gauge (0.032 gauge)': {'price': 1, 'category': 'gutters'},
            'Leaders 2x3 white': {'price': 12, 'category': 'leaders'},
            'Leaders 2x3 all colors': {'price': 13, 'category': 'leaders'},
            'Leader 2x3 white - PVC': {'price': 18, 'category': 'leaders'},
            'Leaders 3x4 white': {'price': 15, 'category': 'leaders'},
            'Leaders 3x4 all colors': {'price': 16, 'category': 'leaders'},
            'Leader 3" Round Corrugated - White': {'price': 47, 'category': 'leaders'},
            'Extra Gauge (0.032 gauge) Leader': {'price': 1, 'category': 'leaders'},
            'Shur-flow 5" (white)': {'price': 15, 'category': 'guards'},
            'Shur-flow 5" (black or aluminum)': {'price': 16, 'category': 'guards'},
            'Shur-flow 6" (white)': {'price': 16, 'category': 'guards'},
            'Shur-flow 6" (black or aluminum)': {'price': 18, 'category': 'guards'},
            'Screen 5"': {'price': 10, 'category': 'guards'},
            'Screen 6"': {'price': 12, 'category': 'guards'},
            'Leafshelter 6" - White': {'price': 18, 'category': 'guards'},
            'Leafshelter 6" - All Colors': {'price': 21, 'category': 'guards'},
            'Strap Hangers per LF': {'price': 4, 'category': 'guards'}
        }
    }
}

def calc_totals_gutters():
    tots = {}
    for cat in ['gutters', 'leaders', 'guards']:
        for _, r in st.session_state.measurements[cat].iterrows():
            col = 'Gutter Type' if cat == 'gutters' else ('Leader Type' if cat == 'leaders' else 'Guard Type')
            if pd.notna(r[col]) and pd.notna(r['LF']):
                itm = r[col]
                if itm in SERVICE_DATA['gutters']['items'] and SERVICE_DATA['gutters']['items'][itm]['category'] == cat:
                    if itm not in tots:
                        tots[itm] = {'qty': 0, 'price': SERVICE_DATA['gutters']['items'][itm]['price'], 'total': 0}
                    tots[itm]['qty'] += float(r['LF'])
    for i in tots:
        tots[i]['total'] = tots[i]['qty'] * tots[i]['price']
    return tots, sum([t['total'] for t in tots.values()])

def calc_pricing(sub, rep=False, rig=False):
    y1 = sub
    d1 = y1 * 0.10
    d30 = y1 - d1
    d2 = d30 * 0.10
    dof = d30 - d2
    d3 = dof * 0.03
    fin = dof - d3
    if rep:
        fin += 2100
    if rig:
        fin += 1400
    return {'y1': y1, 'd1': d1, 'd30': d30, 'd2': d2, 'dof': dof, 'd3': d3, 'rep': 2100 if rep else 0, 'rig': 1400 if rig else 0, 'fin': fin}

st.title("🏗️ Garden State Brickface & Siding Pricing Calculator")
st.markdown("---")

tabs = st.tabs(["Gutters & Leaders", "Stone Veneer", "Stucco Painting", "House Painting"])

with tabs[0]:
    st.session_state.current_service = 'gutters'
    st.warning("⚠️ 50% deposit required | JOB MINIMUM: $650 (combined) / $1,150 (stand-alone)")
    st.subheader("Measurements")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**GUTTERS**")
        g_df = st.data_editor(st.session_state.measurements['gutters'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Gutter Type": st.column_config.SelectboxColumn(options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'gutters']), "LF": st.column_config.NumberColumn(format="%.2f")}, hide_index=True, key="g_ed")
        st.session_state.measurements['gutters'] = g_df
    with col2:
        st.markdown("**LEADERS**")
        l_df = st.data_editor(st.session_state.measurements['leaders'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Leader Type": st.column_config.SelectboxColumn(options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'leaders']), "LF": st.column_config.NumberColumn(format="%.2f")}, hide_index=True, key="l_ed")
        st.session_state.measurements['leaders'] = l_df
    with col3:
        st.markdown("**GUTTER GUARDS**")
        gg_df = st.data_editor(st.session_state.measurements['guards'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Guard Type": st.column_config.SelectboxColumn(options=[k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'guards']), "LF": st.column_config.NumberColumn(format="%.2f")}, hide_index=True, key="gg_ed")
        st.session_state.measurements['guards'] = gg_df
    st.markdown("### Pricing Tables")
    tots, sub = calc_totals_gutters()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Gutters (Standard) .27 Gauge**")
        g_price = pd.DataFrame([[k, tots.get(k, {'qty': 0})['qty'], f"${SERVICE_DATA['gutters']['items'][k]['price']:.2f}", f"${tots.get(k, {'total': 0})['total']:.2f}"] for k in [k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'gutters']], columns=['Item', 'Linear Ft', 'Price Per Ft', 'Price'])
        st.dataframe(g_price, hide_index=True, use_container_width=True)
    with col2:
        st.markdown("**Leaders (Standard) .19 Gauge**")
        l_price = pd.DataFrame([[k, tots.get(k, {'qty': 0})['qty'], f"${SERVICE_DATA['gutters']['items'][k]['price']:.2f}", f"${tots.get(k, {'total': 0})['total']:.2f}"] for k in [k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'leaders']], columns=['Item', 'Linear Ft', 'Price Per Ft', 'Price'])
        st.dataframe(l_price, hide_index=True, use_container_width=True)
    with col3:
        st.markdown("**Gutter Guards**")
        gg_price = pd.DataFrame([[k, tots.get(k, {'qty': 0})['qty'], f"${SERVICE_DATA['gutters']['items'][k]['price']:.2f}", f"${tots.get(k, {'total': 0})['total']:.2f}"] for k in [k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'guards']], columns=['Item', 'LF/Quantity', 'Price Per Ft', 'Price'])
        st.dataframe(gg_price, hide_index=True, use_container_width=True)
    if st.button("Calculate", key="calc_g"):
        st.markdown("### Project Calculation")
        prc = calc_pricing(sub)
        calc_df = pd.DataFrame([['1 Year Price', f"${prc['y1']:.2f}"], ['Deduct 10%', f"(${prc['d1']:.2f})"], ['30 Day Price', f"${prc['d30']:.2f}"], ['Deduct 10%', f"(${prc['d2']:.2f})"], ['Day of Price', f"${prc['dof']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${prc['d3']:.2f})"], ['**FINAL SELL PRICE**', f"**${prc['fin']:.2f}**"]], columns=['Description', 'Amount'])
        st.dataframe(calc_df, hide_index=True, use_container_width=True)

with tabs[1]:
    st.session_state.current_service = 'stone'
    st.subheader("Stone Veneer Measurements")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### STONE FLATS")
        flats_df = st.data_editor(st.session_state.stone_measurements['flats'], hide_index=True, use_container_width=True, key="flats_ed")
        st.session_state.stone_measurements['flats'] = flats_df
        st.text_input("Flats SF Subtotal", key="flats_subtotal")
        st.text_input("Deduct Outs (   )", key="deduct_outs")
        st.markdown("**Total Flats** (yellow highlight)")
    with col2:
        st.markdown("### STONE CORNERS")
        corners_df = st.data_editor(st.session_state.stone_measurements['corners'], hide_index=True, use_container_width=True, key="corners_ed")
        st.session_state.stone_measurements['corners'] = corners_df
        st.text_input("Subtotal", key="corners_subtotal")
        st.info("IF ODD # ROUND UP TO NEAREST EVEN FOOT")
        st.markdown("**Total Corners** (yellow highlight)")
    with col3:
        st.markdown("### STONE SILLS")
        sills_df = st.data_editor(st.session_state.stone_measurements['sills'], hide_index=True, use_container_width=True, key="sills_ed")
        st.session_state.stone_measurements['sills'] = sills_df
        st.text_input("Subtotal", key="sills_subtotal")
        st.info("IF ODD # ROUND UP TO NEAREST EVEN FOOT")
        st.markdown("**Total Sills** (yellow highlight)")
    
    st.markdown("### OUTS (TAKE 100% OUTS)")
    outs_df = st.data_editor(st.session_state.stone_measurements['outs'], hide_index=True, use_container_width=True, key="outs_ed")
    st.session_state.stone_measurements['outs'] = outs_df
    st.text_input("Total Outs (   )", key="total_outs")
    
    st.info("""**STONE VENEER GUIDELINES**
* Measurements must be tip to tip
* Brick returns at windows/doors, must include in SF & LF
* New treads/cap required if existing overhang is not a min of 2 1
* Charge wrap corner fee if turning into vinyl siding or wood sidin
* Chimney caps required when stone on chimneys
* Chimney scaffolding required if stone on chimney""")
    
    st.markdown("---")
    st.subheader("Stone Veneer Pricing")
    
    st.markdown("### DEMOLITION")
    demo_df = st.data_editor(st.session_state.stone_pricing['demolition'], hide_index=True, use_container_width=True, key="demo_ed")
    st.session_state.stone_pricing['demolition'] = demo_df
    
    st.markdown("### DEBRIS REMOVAL (REQUIRED ON ALL JOBS)")
    debris_df = st.data_editor(st.session_state.stone_pricing['debris'], hide_index=True, use_container_width=True, key="debris_ed")
    st.session_state.stone_pricing['debris'] = debris_df
    st.info("** Dumpsters can be provided by the customer at their own expense - they would soley be responsible for delivery, pick up and weight overage fees if applicable. Must be written that way on contract")
    
    st.markdown("### STONE ITEMS (REQUIRED ON ALL JOBS)")
    stone_items_data = [
        ['Stone Flats (1/2" joint only)', 'SF', '', 58],
        ['Stone Corners', 'LF', '', 32],
        ['Chiseled Stone Sills', 'LF', '', 26]
    ]
    stone_items_df = pd.DataFrame(stone_items_data, columns=['Description', 'SF/LF/Q', 'Price', 'Sub-Total'])
    st.dataframe(stone_items_df, hide_index=True, use_container_width=True)
    
    st.markdown("### MISCELLANEOUS")
    misc_df = st.data_editor(st.session_state.stone_pricing['misc'], hide_index=True, use_container_width=True, key="misc_ed")
    st.session_state.stone_pricing['misc'] = misc_df
    
    st.markdown("### JOB MINIMUMS")
    minimums_data = [
        ['All counties excluding below', '$7,500'],
        ['Zone (1): Sussex, Warren, Hunterdon, Mercer', '$8,500'],
        ['Zone (2): Ocean, Burlington, Camden', '$9,500']
    ]
    minimums_df = pd.DataFrame(minimums_data, columns=['Description', 'AMOUNT'])
    st.dataframe(minimums_df, hide_index=True, use_container_width=True)

with tabs[2]:
    st.session_state.current_service = 'stucco'
    st.subheader("Stucco Painting Measurements")
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown("### Walls")
        walls_df = st.data_editor(st.session_state.stucco_measurements['walls'], hide_index=True, use_container_width=True, key="stucco_walls_ed")
        st.session_state.stucco_measurements['walls'] = walls_df
        st.markdown("**Subtotal of Squares**")
        st.text_input("Front (Outs) (   )", key="stucco_front_outs")
        st.text_input("Front Right (Outs) (   )", key="stucco_front_right_outs")
        st.text_input("Rear (Outs) (   )", key="stucco_rear_outs")
        st.text_input("Front Left (Outs) (   )", key="stucco_front_left_outs")
        st.text_input("Squares (Subtotal)", key="stucco_squares_subtotal")
        st.markdown("**Round up to Nearest Full Square**")
    
    with col2:
        st.markdown("### Window Trim (up to 6\")")
        window_df = st.data_editor(st.session_state.stucco_measurements['window_trim'], hide_index=True, use_container_width=True, key="stucco_window_ed")
        st.session_state.stucco_measurements['window_trim'] = window_df
        
        st.markdown("### Soffit (up to 12\")")
        soffit_df = st.data_editor(st.session_state.stucco_measurements['soffit'], hide_index=True, use_container_width=True, key="stucco_soffit_ed")
        st.session_state.stucco_measurements['soffit'] = soffit_df
        
        st.markdown("### Quions (per 1 side only)")
        quions_df = st.data_editor(st.session_state.stucco_measurements['quions'], hide_index=True, use_container_width=True, key="stucco_quions_ed")
        st.session_state.stucco_measurements['quions'] = quions_df
    
    with col3:
        st.markdown("### Door Trim (up to 6\")")
        door_df = st.data_editor(st.session_state.stucco_measurements['door_trim'], hide_index=True, use_container_width=True, key="stucco_door_ed")
        st.session_state.stucco_measurements['door_trim'] = door_df
        
        st.markdown("### Fascia (up to 8\")")
        fascia_df = st.data_editor(st.session_state.stucco_measurements['fascia'], hide_index=True, use_container_width=True, key="stucco_fascia_ed")
        st.session_state.stucco_measurements['fascia'] = fascia_df
        
        st.markdown("### Other Trim if Any")
        other_df = st.data_editor(st.session_state.stucco_measurements['other_trim'], hide_index=True, use_container_width=True, key="stucco_other_ed")
        st.session_state.stucco_measurements['other_trim'] = other_df
    
    st.markdown("---")
    st.subheader("Stucco Painting Pricing")
    
    st.markdown("### LOXON XP (Above 8') - WALLS ONLY")
    loxon_above_data = [
        ['Includes ladders and access', '200 - 499', '', 14.27],
        ['Includes powerwash of all work areas', '500 - 999', '', 13.00],
        ['Crack repair up to 50 linear ft (1" or less)', '1000 - 1699', '', 12.45],
        ['Apply Two Coats of Loxon XP', '1700 - 2999', '', 11.78],
        ['Loxon will be rolled or sprayed at our discretion', '3000 - 4499', '', 11.38],
        ['Wall texture will remain the same', 'Above 4500', '', 11.09]
    ]
    loxon_above_df = pd.DataFrame(loxon_above_data, columns=['Description', 'SF RANGE', 'SF', 'PRICE'])
    st.dataframe(loxon_above_df, hide_index=True, use_container_width=True)
    
    st.markdown("### LOXON XP (Below 8') - WALLS ONLY")
    loxon_below_data = [
        ['Does not include ladders, all ground work', '200 - 499', '', 9.69],
        ['Includes powerwash of all work areas', '500 - 999', '', 9.11],
        ['Crack repair up to 50 linear ft (1" or less)', '1000 - 1699', '', 8.73],
        ['Apply Two Coats of Loxon XP', '1700 - 2999', '', 8.24],
        ['Loxon will be rolled or sprayed at our discretion', '3000 - 4499', '', 7.95],
        ['Wall texture will remain the same', 'Above 4500', '', 7.75]
    ]
    loxon_below_df = pd.DataFrame(loxon_below_data, columns=['Description', 'SF RANGE', 'SF', 'PRICE'])
    st.dataframe(loxon_below_df, hide_index=True, use_container_width=True)
    
    st.markdown("### LOXON XP (TRIM ONLY)")
    loxon_trim_data = [
        ['Two coats of Loxon XP over stucco window/door trim (up to 6")', 'Per LF', '', 7.25],
        ['Two coats of Loxon XP over stucco soffit (up to 12")', 'Per LF', '', 11.67],
        ['Two coats of Loxon XP over stucco fascia (up to 8")', 'Per LF', '', 8.15],
        ['Apply two coats of Loxon XP over single side quion', 'Per Side', '', 11.67]
    ]
    loxon_trim_df = pd.DataFrame(loxon_trim_data, columns=['Description', '', 'PRICE', 'TOTAL'])
    st.dataframe(loxon_trim_df, hide_index=True, use_container_width=True)
    
    st.markdown("### CAULKING (IN CONJUNCTION WITH LOXON PROJECT ONLY)")
    caulking_data = [
        ['Caulk only (no raking) - up to 3/4"', '', 8.36],
        ['Caulk and install backer rod (no raking) - up to 3/4"', '', 11.17],
        ['Rake out and caulk only - up to 3/4"', '', 12.54],
        ['Rake out and install backer rod - up to 3/4"', '', 15.32]
    ]
    caulking_df = pd.DataFrame(caulking_data, columns=['Description', 'LF', 'PRICE'])
    st.dataframe(caulking_df, hide_index=True, use_container_width=True)
    
    st.markdown("### MISCELLANEOUS ITEMS")
    misc_items_data = [
        ['EIFS Repair', 'Per SF', '', 60],
        ['BCMA (Fiberglass, Basecoat, Acrylic Stucco)', 'Per SF', '', 17.59],
        ['Remove and Re-Install Existing Shutters', 'Per Pair', '', 145],
        ['Remove, Paint and Re-Install Shutters (per pair)', 'Per Pair', '', 290],
        ['Stainless Steel Chimney Cover', 'Per Item', '', 1509],
        ['Plywood (demo, debris, install 1 sheet of plywood) 32 sf', 'Per Item', '', 439],
        ['Remove and Re-Install Existing Gutters', 'Per LF', '', 6],
        ['Additional Rigging (For Caulking Only Projects)', 'Per Side', '', 435],
        ['Clear Sealer, Ladders, Powerwash', 'Per SF', '', 7],
        ['Additional Heavy Duty Powerwash', 'Per SF', '', 2],
        ['Additional stucco crack repair above 50 lf (1" or less)', 'Per LF', '', 7],
        ['Spot Point Brick    (* See rules page)', 'Per SF', '', 29],
        ['Full Cut and Re-Point (Under 500sf)', 'Per SF', '', 29]
    ]
    misc_items_df = pd.DataFrame(misc_items_data, columns=['Description', 'Unit', 'Quantity', 'PRICE'])
    st.dataframe(misc_items_df, hide_index=True, use_container_width=True)
    
    st.markdown("### MINIMUMS (FOR WORK ON STANDARD 2 1/2 STORY HOMES LESS THAN 26\")")
    minimums_data = [
        ['LOXON', '$4,200'],
        ['CLEAR SEALER', '$3,500'],
        ['WOODPECKER HOLES (INCLUDES UP TO 6 HOLES) ADD $500 PER HOLE', '$3,500'],
        ['BCMA', '$4,200'],
        ['SPOT POINTING', '$4,900'],
        ['FULL POINTING', '$5,600'],
        ['CAULKING', '$5,600']
    ]
    minimums_df = pd.DataFrame(minimums_data, columns=['Service', 'Amount'])
    st.dataframe(minimums_df, hide_index=True, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        rep = st.checkbox("Add Repair - $2,100", key="st_rep")
    with col2:
        rig = st.checkbox("Add Rigging - $1,400", key="st_rig")
    
    if st.button("Calculate", key="calc_st"):
        st.info("Calculation based on measurements and pricing tables above")

with tabs[3]:
    st.session_state.current_service = 'painting'
    st.subheader("HOUSE PAINTING - 100% OUTS CAN BE TAKEN")
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown("### Walls")
        walls_df = st.data_editor(st.session_state.painting_measurements['walls'], hide_index=True, use_container_width=True, key="painting_walls_ed")
        st.session_state.painting_measurements['walls'] = walls_df
        st.markdown("**Subtotal of Squares**")
        st.text_input("Front (Outs) (   )", key="painting_front_outs")
        st.text_input("Front Right (Outs) (   )", key="painting_front_right_outs")
        st.text_input("Rear (Outs) (   )", key="painting_rear_outs")
        st.text_input("Front Left (Outs) (   )", key="painting_front_left_outs")
        st.text_input("Squares (Subtotal)", key="painting_squares_subtotal")
        st.markdown("**Round up to Nearest Full Square**")
    
    with col2:
        st.markdown("### Window Trim (up to 4\")")
        window_df = st.data_editor(st.session_state.painting_measurements['window_trim'], hide_index=True, use_container_width=True, key="painting_window_ed")
        st.session_state.painting_measurements['window_trim'] = window_df
        
        st.markdown("### Soffit (up to 12\")")
        soffit_df = st.data_editor(st.session_state.painting_measurements['soffit'], hide_index=True, use_container_width=True, key="painting_soffit_ed")
        st.session_state.painting_measurements['soffit'] = soffit_df
        
        st.markdown("### Entry Doors")
        entry_df = st.data_editor(st.session_state.painting_measurements['entry_doors'], hide_index=True, use_container_width=True, key="painting_entry_ed")
        st.session_state.painting_measurements['entry_doors'] = entry_df
    
    with col3:
        st.markdown("### Door Trim (up to 4\")")
        door_df = st.data_editor(st.session_state.painting_measurements['door_trim'], hide_index=True, use_container_width=True, key="painting_door_ed")
        st.session_state.painting_measurements['door_trim'] = door_df
        
        st.markdown("### Fascia (up to 6\")")
        fascia_df = st.data_editor(st.session_state.painting_measurements['fascia'], hide_index=True, use_container_width=True, key="painting_fascia_ed")
        st.session_state.painting_measurements['fascia'] = fascia_df
        
        st.markdown("### Garage Doors")
        garage_df = st.data_editor(st.session_state.painting_measurements['garage_doors'], hide_index=True, use_container_width=True, key="painting_garage_ed")
        st.session_state.painting_measurements['garage_doors'] = garage_df
    
    st.markdown("---")
    st.subheader("House Painting Pricing")
    
    st.markdown("### PAINTING (WALLS ONLY)")
    walls_pricing_data = [
        ['Vinyl and Aluminum ---- (Use vinyl safe colors for vinyl only)', '', 8.06, ''],
        ['Wood Clapboard ---- (20% sand and spot prime)', '', 9.28, ''],
        ['Wood Clapboard ---- (Full sanding only)', '', 11.5, ''],
        ['Wood Shake ---- (20% sand and spot prime)', '', 10.02, ''],
        ['Wood Shake ---- (Full sanding only)', '', 12.19, '']
    ]
    walls_pricing_df = pd.DataFrame(walls_pricing_data, columns=['Description', 'Total SF', 'Price Per SF', 'TOTAL'])
    st.dataframe(walls_pricing_df, hide_index=True, use_container_width=True)
    
    st.markdown("### PAINTING (TRIM ONLY)")
    trim_pricing_data = [
        ['Window trim ---- (up to 4in wide)', 'Per Opening', '', 61.48, ''],
        ['Door trim ---- (up to 4in wide)', 'Per Opening', '', 61.48, ''],
        ['Fascia for frieze board trim ---- (up to 6in wide)', 'Per LF', '', 6.36, ''],
        ['Soffit - Non Vented ---- (up to 12in deep)', 'Per LF', '', 8.48, ''],
        ['Remove and re-install existing shutters', 'Per Pair', '', 77.38, ''],
        ['Remove, paint and re-install existing shutters', 'Per Pair', '', 106.0, ''],
        ['Single front entry door ---- (wood surface only)', 'Per Opening', '', 242.0, ''],
        ['Garage doors ---- (wood surface only)', 'Per Opening', '', 530.0, '']
    ]
    trim_pricing_df = pd.DataFrame(trim_pricing_data, columns=['Description', '', 'Total Qty', 'Price Per Unit', 'TOTAL'])
    st.dataframe(trim_pricing_df, hide_index=True, use_container_width=True)
    
    st.markdown("### MISCELLANEOUS ITEMS")
    misc_painting_data = [
        ['Remove / replace (1) sheet of plywood ---- (up to 32sf)', '', '', 316.94, ''],
        ['Remove / replace wood siding ---- (up to 8 sq exposure)', 'Per 12ft Piece', '', 320.12, ''],
        ['Remove / replace aluminum siding ---- (up to 8in exposure)', 'Per 12ft Piece', '', 320.12, ''],
        ['Remove / replace wood trim ---- (2/4in x 3ft x 12ft)', 'Per 16ft Piece', '', 151.58, ''],
        ['Remove / replace wood clapboard ---- (1/2in x 8in x 16ft)', 'Per 16ft Piece', '', 338.14, ''],
        ['Remove / replace wood shake ---- (up to 12in Exposure)', 'Per 1/2 Square', '', 647.66, ''],
        ['Remove / re-install existing gutters', 'Per LF', '', 4.24, ''],
        ['Additional powerwash', 'Per SF', '', 1.59, ''],
        ['Caulk only (no raking) ---- (up to 1/2in)', 'Per LF', '', 8.48, ''],
        ['Rake out and caulk only ---- (up to 1/2in)', 'Per LF', '', 12.72, ''],
        ['Paint samples ---- (includes 1 color sample)', 'Per Item', '', 82.68, '']
    ]
    misc_painting_df = pd.DataFrame(misc_painting_data, columns=['Description', '', 'Quantity', 'Price Per Unit', 'TOTAL'])
    st.dataframe(misc_painting_df, hide_index=True, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        rep = st.checkbox("Add Repair - $2,100", key="p_rep")
    with col2:
        rig = st.checkbox("Add Rigging - $1,400", key="p_rig")
    
    if st.button("Calculate", key="calc_p"):
        st.info("Calculation based on measurements and pricing tables above")

st.markdown("---")
st.header("Generate PDF Estimate")

col1, col2, col3 = st.columns(3)

with col1:
    cname = st.text_input("Customer Name", value=st.session_state.customer_info['customer_name'])
    st.session_state.customer_info['customer_name'] = cname

with col2:
    addr = st.text_input("Project Address", value=st.session_state.customer_info['project_address'])
    st.session_state.customer_info['project_address'] = addr

with col3:
    srep = st.text_input("Sales Representative", value=st.session_state.customer_info['sales_rep'])
    st.session_state.customer_info['sales_rep'] = srep

if st.button("Generate PDF", type="primary"):
    if not cname or not addr or not srep:
        st.error("Fill in all fields")
    else:
        st.info("PDF generation functionality will be implemented with the measurements and pricing data entered above")
        st.info("📁 To save to Google Drive: Download the PDF, then upload it to https://drive.google.com/drive/folders/1i_Ka70_VlaucBYAwcfivChslVBKcoe57")

st.divider()
st.caption("Garden State Brickface & Siding Pricing Calculator v3.0")
