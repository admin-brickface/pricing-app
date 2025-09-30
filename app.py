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

if 'measurements' not in st.session_state:
    st.session_state.measurements = {
        'gutters': pd.DataFrame(columns=['Location', 'Gutter Type', 'LF']),
        'leaders': pd.DataFrame(columns=['Location', 'Leader Type', 'LF']),
        'guards': pd.DataFrame(columns=['Location', 'Guard Type', 'LF']),
        'stone_flats': pd.DataFrame(columns=['Location', 'Width', 'Height', 'Total SF']),
        'stone_corners': pd.DataFrame(columns=['Location', 'Width', 'Height', 'LF']),
        'stone_sills': pd.DataFrame(columns=['Location', 'Width', 'Height', 'LF']),
        'stucco': pd.DataFrame(columns=['Location', 'Item Type', 'SF']),
        'painting': pd.DataFrame(columns=['Location', 'Item Type', 'SF'])
    }

if 'misc_quantities' not in st.session_state:
    st.session_state.misc_quantities = {}

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
    },
    'stone': {
        'name': 'Stone Veneer',
        'items': {'Stone Flats': {'price': 28}, 'Stone Corners': {'price': 28}, 'Stone Sills': {'price': 28}},
        'delivery_fee': 222
    },
    'stucco': {
        'name': 'Stucco Painting',
        'items': {'Wall': {'price': 8.36}, 'Soffit': {'price': 8.36}, 'Column': {'price': 8.36}, 'Beam': {'price': 8.36}},
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
        }
    },
    'painting': {
        'name': 'House Painting',
        'items': {'Exterior Wall': {'price': 4.18}, 'Trim': {'price': 4.18}, 'Door': {'price': 125}, 'Window': {'price': 75}}
    }
}

def calc_stone(w, h, t='flats'):
    if pd.isna(w) or pd.isna(h): return 0
    return (float(w) * float(h)) / 144 if t == 'flats' else float(w) / 12

def calc_totals(svc):
    tots = {}
    if svc == 'gutters':
        for cat in ['gutters', 'leaders', 'guards']:
            for _, r in st.session_state.measurements[cat].iterrows():
                col = 'Gutter Type' if cat == 'gutters' else ('Leader Type' if cat == 'leaders' else 'Guard Type')
                if pd.notna(r[col]) and pd.notna(r['LF']):
                    itm = r[col]
                    if itm in SERVICE_DATA['gutters']['items'] and SERVICE_DATA['gutters']['items'][itm]['category'] == cat:
                        if itm not in tots: tots[itm] = {'qty': 0, 'price': SERVICE_DATA['gutters']['items'][itm]['price'], 'total': 0}
                        tots[itm]['qty'] += float(r['LF'])
    elif svc == 'stone':
        for k, df_key in [('Stone Flats', 'stone_flats'), ('Stone Corners', 'stone_corners'), ('Stone Sills', 'stone_sills')]:
            col = 'Total SF' if k == 'Stone Flats' else 'LF'
            for _, r in st.session_state.measurements[df_key].iterrows():
                if pd.notna(r[col]):
                    if k not in tots: tots[k] = {'qty': 0, 'price': SERVICE_DATA['stone']['items'][k]['price'], 'total': 0}
                    tots[k]['qty'] += float(r[col])
    else:
        for _, r in st.session_state.measurements[svc].iterrows():
            if pd.notna(r['Item Type']) and pd.notna(r['SF']):
                itm = r['Item Type']
                if itm in SERVICE_DATA[svc]['items']:
                    if itm not in tots: tots[itm] = {'qty': 0, 'price': SERVICE_DATA[svc]['items'][itm]['price'], 'total': 0}
                    tots[itm]['qty'] += float(r['SF'])
    for i in tots: tots[i]['total'] = tots[i]['qty'] * tots[i]['price']
    return tots, sum([t['total'] for t in tots.values()])

def calc_pricing(sub, rep=False, rig=False):
    y1 = sub
    d1 = y1 * 0.10
    d30 = y1 - d1
    d2 = d30 * 0.10
    dof = d30 - d2
    d3 = dof * 0.03
    fin = dof - d3
    if rep: fin += 2100
    if rig: fin += 1400
    return {'y1': y1, 'd1': d1, 'd30': d30, 'd2': d2, 'dof': dof, 'd3': d3, 'rep': 2100 if rep else 0, 'rig': 1400 if rig else 0, 'fin': fin}

def gen_pdf(svc, tots, prc, cust):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    story.append(Paragraph(f"{SERVICE_DATA[svc]['name']} Estimate", styles['Title']))
    story.append(Spacer(1, 0.2*inch))
    info_data = [['Customer:', cust['customer_name']], ['Address:', cust['project_address']], ['Sales Rep:', cust['sales_rep']], ['Date:', datetime.now().strftime('%B %d, %Y')]]
    info_t = Table(info_data, colWidths=[1.5*inch, 4.5*inch])
    info_t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 10), ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10)]))
    story.append(info_t)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Items", styles['Heading2']))
    items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
    for i, v in tots.items():
        if v['qty'] > 0: items_data.append([i, f"{v['qty']:.2f}", f"${v['price']:.2f}", f"${v['total']:.2f}"])
    items_t = Table(items_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    items_t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
    story.append(items_t)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Pricing", styles['Heading2']))
    prc_data = [['1 Year Price', f"${prc['y1']:.2f}"], ['Deduct 10%', f"(${prc['d1']:.2f})"], ['30 Day Price', f"${prc['d30']:.2f}"], ['Deduct 10%', f"(${prc['d2']:.2f})"], ['Day of Price', f"${prc['dof']:.2f}"], ['Deduct 3%', f"(${prc['d3']:.2f})"]]
    if prc['rep'] > 0: prc_data.append(['Add: Repair', f"${prc['rep']:.2f}"])
    if prc['rig'] > 0: prc_data.append(['Add: Rigging', f"${prc['rig']:.2f}"])
    prc_data.append(['FINAL PRICE', f"${prc['fin']:.2f}"])
    prc_t = Table(prc_data, colWidths=[4*inch, 2*inch])
    prc_t.setStyle(TableStyle([('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 12), ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black)]))
    story.append(prc_t)
    doc.build(story)
    buf.seek(0)
    return buf

st.title("🏗️ Garden State Brickface & Siding Pricing Calculator")
st.markdown("---")

tabs = st.tabs(["Gutters & Leaders", "Stone Veneer", "Stucco Painting", "House Painting"])

with tabs[0]:
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
    
    if st.button("Calculate", key="calc_g"):
        tots, sub = calc_totals('gutters')
        st.markdown("### Pricing Tables")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Gutters (Standard) .27 Gauge**")
            g_price = pd.DataFrame([[k, tots.get(k, {'qty': 0})['qty'], SERVICE_DATA['gutters']['items'][k]['price'], tots.get(k, {'total': 0})['total']] for k in [k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'gutters']], columns=['Item', 'Linear Ft', 'Price Per Ft', 'Price'])
            st.dataframe(g_price, hide_index=True)
        with col2:
            st.markdown("**Leaders (Standard) .19 Gauge**")
            l_price = pd.DataFrame([[k, tots.get(k, {'qty': 0})['qty'], SERVICE_DATA['gutters']['items'][k]['price'], tots.get(k, {'total': 0})['total']] for k in [k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'leaders']], columns=['Item', 'Linear Ft', 'Price Per Ft', 'Price'])
            st.dataframe(l_price, hide_index=True)
        with col3:
            st.markdown("**Gutter Guards**")
            gg_price = pd.DataFrame([[k, tots.get(k, {'qty': 0})['qty'], SERVICE_DATA['gutters']['items'][k]['price'], tots.get(k, {'total': 0})['total']] for k in [k for k, v in SERVICE_DATA['gutters']['items'].items() if v['category'] == 'guards']], columns=['Item', 'LF/Quantity', 'Price Per Ft', 'Price'])
            st.dataframe(gg_price, hide_index=True)
        st.markdown("### Project Calculation")
        prc = calc_pricing(sub)
        calc_df = pd.DataFrame([['1 Year Price', f"${prc['y1']:.2f}"], ['Deduct 10%', f"(${prc['d1']:.2f})"], ['30 Day Price', f"${prc['d30']:.2f}"], ['Deduct 10%', f"(${prc['d2']:.2f})"], ['Day of Price', f"${prc['dof']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${prc['d3']:.2f})"], ['**FINAL SELL PRICE**', f"**${prc['fin']:.2f}**"]], columns=['Description', 'Amount'])
        st.dataframe(calc_df, hide_index=True)

with tabs[1]:
    st.subheader("Stone Veneer Measurements")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Stone Flats**")
        sf_df = st.data_editor(st.session_state.measurements['stone_flats'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Width": st.column_config.NumberColumn("Width (in)", format="%.2f"), "Height": st.column_config.NumberColumn("Height (in)", format="%.2f"), "Total SF": st.column_config.NumberColumn(disabled=True, format="%.2f")}, hide_index=True, key="sf_ed")
        for idx, r in sf_df.iterrows():
            sf_df.at[idx, 'Total SF'] = calc_stone(r['Width'], r['Height'], 'flats')
        st.session_state.measurements['stone_flats'] = sf_df
        st.metric("Total SF", f"{sf_df['Total SF'].sum():.2f}")
    with col2:
        st.markdown("**Stone Corners**")
        sc_df = st.data_editor(st.session_state.measurements['stone_corners'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Width": st.column_config.NumberColumn("Width (in)", format="%.2f"), "Height": st.column_config.NumberColumn("Height (in)", format="%.2f"), "LF": st.column_config.NumberColumn(disabled=True, format="%.2f")}, hide_index=True, key="sc_ed")
        for idx, r in sc_df.iterrows():
            sc_df.at[idx, 'LF'] = calc_stone(r['Width'], r['Height'], 'corners')
        st.session_state.measurements['stone_corners'] = sc_df
        st.metric("Total LF", f"{sc_df['LF'].sum():.2f}")
    with col3:
        st.markdown("**Stone Sills**")
        ss_df = st.data_editor(st.session_state.measurements['stone_sills'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Width": st.column_config.NumberColumn("Width (in)", format="%.2f"), "Height": st.column_config.NumberColumn("Height (in)", format="%.2f"), "LF": st.column_config.NumberColumn(disabled=True, format="%.2f")}, hide_index=True, key="ss_ed")
        for idx, r in ss_df.iterrows():
            ss_df.at[idx, 'LF'] = calc_stone(r['Width'], r['Height'], 'sills')
        st.session_state.measurements['stone_sills'] = ss_df
        st.metric("Total LF", f"{ss_df['LF'].sum():.2f}")
    
    if st.button("Calculate", key="calc_s"):
        tots, sub = calc_totals('stone')
        st.markdown("### Pricing Table")
        stone_price = pd.DataFrame([[k, tots[k]['qty'], tots[k]['price'], tots[k]['total']] for k in tots.keys()], columns=['Item', 'Quantity', 'Price Per Unit', 'Total'])
        st.dataframe(stone_price, hide_index=True)
        st.markdown("### Project Calculation")
        sub_del = sub + SERVICE_DATA['stone']['delivery_fee']
        prc = calc_pricing(sub_del)
        calc_df = pd.DataFrame([['Subtotal', f"${sub:.2f}"], ['Delivery Fee', f"${SERVICE_DATA['stone']['delivery_fee']:.2f}"], ['1 Year Price', f"${prc['y1']:.2f}"], ['Deduct 10%', f"(${prc['d1']:.2f})"], ['30 Day Price', f"${prc['d30']:.2f}"], ['Deduct 10%', f"(${prc['d2']:.2f})"], ['Day of Price', f"${prc['dof']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${prc['d3']:.2f})"], ['**FINAL SELL PRICE**', f"**${prc['fin']:.2f}**"]], columns=['Description', 'Amount'])
        st.dataframe(calc_df, hide_index=True)

with tabs[2]:
    st.subheader("Stucco Painting Measurements")
    st_df = st.data_editor(st.session_state.measurements['stucco'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Item Type": st.column_config.SelectboxColumn(options=list(SERVICE_DATA['stucco']['items'].keys())), "SF": st.column_config.NumberColumn(format="%.2f")}, hide_index=True, key="st_ed")
    st.session_state.measurements['stucco'] = st_df
    st.subheader("Miscellaneous Items")
    misc_cols = st.columns(2)
    idx = 0
    for itm, det in SERVICE_DATA['stucco']['misc_items'].items():
        with misc_cols[idx % 2]:
            q = st.number_input(f"{itm} ({det['unit']}) - ${det['price']:.2f}", min_value=0.0, value=st.session_state.misc_quantities.get(itm, 0.0), step=1.0, key=f"misc_{itm}")
            st.session_state.misc_quantities[itm] = q
        idx += 1
    col1, col2 = st.columns(2)
    with col1:
        rep = st.checkbox("Add Repair - $2,100", key="st_rep")
    with col2:
        rig = st.checkbox("Add Rigging - $1,400", key="st_rig")
    
    if st.button("Calculate", key="calc_st"):
        tots, sub = calc_totals('stucco')
        for itm, q in st.session_state.misc_quantities.items():
            if q > 0:
                p = SERVICE_DATA['stucco']['misc_items'][itm]['price']
                tots[itm] = {'qty': q, 'price': p, 'total': q * p}
                sub += q * p
        st.markdown("### Pricing Table")
        stucco_price = pd.DataFrame([[k, tots[k]['qty'], tots[k]['price'], tots[k]['total']] for k in tots.keys()], columns=['Item', 'Quantity', 'Unit Price', 'Total'])
        st.dataframe(stucco_price, hide_index=True)
        st.markdown("### Project Calculation")
        prc = calc_pricing(sub, rep, rig)
        calc_df = pd.DataFrame([['1 Year Price', f"${prc['y1']:.2f}"], ['Deduct 10%', f"(${prc['d1']:.2f})"], ['30 Day Price', f"${prc['d30']:.2f}"], ['Deduct 10%', f"(${prc['d2']:.2f})"], ['Day of Price', f"${prc['dof']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${prc['d3']:.2f})"]], columns=['Description', 'Amount'])
        if rep: calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Repair', f"${prc['rep']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        if rig: calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Rigging', f"${prc['rig']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        calc_df = pd.concat([calc_df, pd.DataFrame([['**FINAL SELL PRICE**', f"**${prc['fin']:.2f}**"]], columns=['Description', 'Amount'])], ignore_index=True)
        st.dataframe(calc_df, hide_index=True)

with tabs[3]:
    st.subheader("House Painting Measurements")
    p_df = st.data_editor(st.session_state.measurements['painting'], num_rows="dynamic", column_config={"Location": st.column_config.SelectboxColumn(options=["FRONT", "RIGHT", "BACK", "LEFT"]), "Item Type": st.column_config.SelectboxColumn(options=list(SERVICE_DATA['painting']['items'].keys())), "SF": st.column_config.NumberColumn(format="%.2f")}, hide_index=True, key="p_ed")
    st.session_state.measurements['painting'] = p_df
    col1, col2 = st.columns(2)
    with col1:
        rep = st.checkbox("Add Repair - $2,100", key="p_rep")
    with col2:
        rig = st.checkbox("Add Rigging - $1,400", key="p_rig")
    
    if st.button("Calculate", key="calc_p"):
        tots, sub = calc_totals('painting')
        st.markdown("### Pricing Table")
        paint_price = pd.DataFrame([[k, tots[k]['qty'], tots[k]['price'], tots[k]['total']] for k in tots.keys()], columns=['Item', 'Quantity', 'Unit Price', 'Total'])
        st.dataframe(paint_price, hide_index=True)
        st.markdown("### Project Calculation")
        prc = calc_pricing(sub, rep, rig)
        calc_df = pd.DataFrame([['1 Year Price', f"${prc['y1']:.2f}"], ['Deduct 10%', f"(${prc['d1']:.2f})"], ['30 Day Price', f"${prc['d30']:.2f}"], ['Deduct 10%', f"(${prc['d2']:.2f})"], ['Day of Price', f"${prc['dof']:.2f}"], ['Deduct 3% for 33% Deposit', f"(${prc['d3']:.2f})"]], columns=['Description', 'Amount'])
        if rep: calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Repair', f"${prc['rep']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        if rig: calc_df = pd.concat([calc_df, pd.DataFrame([['Add: Rigging', f"${prc['rig']:.2f}"]], columns=['Description', 'Amount'])], ignore_index=True)
        calc_df = pd.concat([calc_df, pd.DataFrame([['**FINAL SELL PRICE**', f"**${prc['fin']:.2f}**"]], columns=['Description', 'Amount'])], ignore_index=True)
        st.dataframe(calc_df, hide_index=True)

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

svc_sel = st.selectbox("Select Service for PDF", ["gutters", "stone", "stucco", "painting"], format_func=lambda x: SERVICE_DATA[x]['name'])

if st.button("Generate PDF", type="primary"):
    if not cname or not addr or not srep:
        st.error("Fill in all fields")
    else:
        with st.spinner("Generating..."):
            tots, sub = calc_totals(svc_sel)
            if svc_sel == 'stucco':
                for itm, q in st.session_state.misc_quantities.items():
                    if q > 0:
                        p = SERVICE_DATA['stucco']['misc_items'][itm]['price']
                        tots[itm] = {'qty': q, 'price': p, 'total': q * p}
                        sub += q * p
            rep = st.session_state.get(f'{svc_sel}_rep', False)
            rig = st.session_state.get(f'{svc_sel}_rig', False)
            if svc_sel == 'stone':
                sub += SERVICE_DATA['stone']['delivery_fee']
            prc = calc_pricing(sub, rep, rig)
            pdf = gen_pdf(svc_sel, tots, prc, st.session_state.customer_info)
            fname = f"{cname.replace(' ', '_')}_{srep.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.success("PDF generated!")
            st.download_button("Download PDF", pdf, fname, "application/pdf", type="primary")

st.divider()
st.caption("Garden State Brickface & Siding Pricing Calculator v3.0")
