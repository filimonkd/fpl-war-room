import streamlit as st
import pandas as pd
import fpl_api
import time
from collections import Counter

# ==========================================
# 1. PAGE CONFIG & MASTER CSS DESIGN SYSTEM
# ==========================================
st.set_page_config(page_title="FPL War Room", layout="centered", page_icon="⚽")

MASTER_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* --- GLOBAL & DARK THEME OVERRIDES --- */
    html, body, .stApp { background: #0b0e14 !important; color: #e5e7eb !important; font-family: 'Inter', sans-serif !important; }
    [data-testid="stHeader"] { background: #0b0e14 !important; }
    #MainMenu, footer, header { visibility: hidden; height: 0; }
    .block-container { padding: 1.5rem 1rem !important; max-width: 1000px; }

    /* --- TYPOGRAPHY --- */
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700 !important; letter-spacing: -0.02em; }
    p, span, label, .stMarkdown { color: #9ca3af !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #ffffff !important; }

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] { background: #0b0e14 !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #ffffff !important; }
    [data-testid="stSidebar"] .stTextInput input, [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background: #15151f !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #fff !important; border-radius: 8px !important;
    }

    /* --- NAVIGATION TABS (SEGMENTED CONTROL) --- */
    .stTabs [data-baseweb="tab-list"] {
        background: #15151f !important; padding: 6px !important; border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.05) !important; gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; border-radius: 8px !important; color: #9ca3af !important;
        padding: 10px 16px !important; font-size: 0.9rem !important; font-weight: 600 !important;
    }
    .stTabs [aria-selected="true"] { background: #38003c !important; color: #00ff87 !important; }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

    /* --- BUTTONS & INPUTS --- */
    .stButton button {
        background: #38003c !important; color: #00ff87 !important; border: 1px solid rgba(0, 255, 135, 0.3) !important;
        border-radius: 10px !important; font-weight: 600 !important; transition: all 0.2s !important;
    }
    .stButton button:hover { box-shadow: 0 4px 15px rgba(0, 255, 135, 0.2) !important; background: #4a0050 !important; }
    .stSelectbox div[data-baseweb="select"] { background: #15151f !important; border-radius: 8px !important; border: 1px solid rgba(255,255,255,0.1) !important;}
    .stRadio label { color: #9ca3af !important; }
    .stRadio div[data-baseweb="radio"] > div:first-child { border-color: #38003c !important; }
    .stRadio div[data-baseweb="radio"] > div:first-child[aria-checked="true"] { background: #00ff87 !important; border-color: #00ff87 !important; }

    /* --- EXPANDERS --- */
    .stExpander { border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 12px !important; background: #15151f !important;}
    .stExpander summary { color: #fff !important; font-weight: 600 !important; }
    .stExpander summary::before { border-color: transparent transparent transparent #9ca3af !important; }

    /* --- MOBILE RESPONSIVENESS --- */
    @media (max-width: 768px) {
        .block-container { padding: 1rem !important; }
        .stTabs [data-baseweb="tab"] { font-size: 0.75rem !important; padding: 8px 4px !important; }
    }
</style>
"""
st.markdown(MASTER_CSS, unsafe_allow_html=True)

# ==========================================
# 2. MODULAR UI COMPONENTS
# ==========================================
def render_hero(my_name, current_gw, gw_pts, total_pts, overall_rank):
    html = f"""
    <div style="background: linear-gradient(135deg, #15151f 0%, #1c1c27 100%); border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; padding: 24px; margin-bottom: 24px; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: #38003c; border-radius: 50%; opacity: 0.1; filter: blur(40px);"></div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; position: relative; z-index: 1;">
            <div>
                <div style="font-size: 0.8rem; color: #00ff87; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;">Gameweek {current_gw}</div>
                <h1 style="margin: 4px 0; font-size: 1.8rem; color: #ffffff;">FPL WAR ROOM</h1>
                <p style="margin: 0; color: #9ca3af; font-size: 1rem;">Commander: <span style="color: #ffffff; font-weight: 600;">{my_name}</span></p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.8rem; color: #9ca3af;">Overall Rank</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #ffffff;">#{overall_rank}</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px;">
            <div style="background: rgba(0, 255, 135, 0.05); border: 1px solid rgba(0, 255, 135, 0.1); border-radius: 12px; padding: 16px; text-align: center;">
                <div style="font-size: 0.75rem; color: #00ff87; font-weight: 600; text-transform: uppercase;">GW Points</div>
                <div style="font-size: 2rem; font-weight: 800; color: #ffffff; margin-top: 4px;">{gw_pts}</div>
            </div>
            <div style="background: rgba(56, 0, 60, 0.2); border: 1px solid rgba(56, 0, 60, 0.3); border-radius: 12px; padding: 16px; text-align: center;">
                <div style="font-size: 0.75rem; color: #d946ef; font-weight: 600; text-transform: uppercase;">Total Points</div>
                <div style="font-size: 2rem; font-weight: 800; color: #ffffff; margin-top: 4px;">{total_pts}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_podium(df):
    if len(df) < 3: return
    top3 = df.head(3)
    order = [1, 0, 2]
    medals = ['🥈', '👑', '🥉']
    colors = ['#c0c0c0', '#ffd700', '#cd7f32']
    
    html = '<div style="display: flex; gap: 12px; align-items: flex-end; margin-bottom: 24px; flex-wrap: wrap;">'
    for i, idx in enumerate(order):
        row = top3.iloc[idx]
        height = '160px' if idx == 0 else '130px'
        border_color = colors[i]
        bg_opacity = '0.1' if idx == 0 else '0.05'
        
        # NO LEADING SPACES in the f-string to prevent Markdown code-block formatting
        html += f"""<div style="flex: 1; min-width: 120px; background: rgba(255,255,255,{bg_opacity}); border: 1px solid {border_color}; border-radius: 16px; padding: 16px; text-align: center; height: {height}; display: flex; flex-direction: column; justify-content: center;">
<div style="font-size: 2rem;">{medals[i]}</div>
<div style="font-size: 1rem; font-weight: 700; color: #ffffff; margin: 8px 0 4px;">{row['Manager']}</div>
<div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 8px;">{row['Team Name']}</div>
<div style="font-size: 1.5rem; font-weight: 800; color: {border_color};">{row['Total Points']}</div>
<div style="font-size: 0.75rem; color: #9ca3af;">GW: {row['GW Points']}</div>
</div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_leaderboard(df, my_name):
    html = '<div style="background: #15151f; border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; overflow: hidden;">'
    for idx, row in df.iterrows():
        is_me = my_name.lower() in row['Manager'].lower()
        bg = "rgba(0, 255, 135, 0.05)" if is_me else "transparent"
        border_left = "3px solid #00ff87" if is_me else "3px solid transparent"
        text_color = "#00ff87" if is_me else "#ffffff"
        
        # NO LEADING SPACES in the f-string
        html += f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: {bg}; border-left: {border_left}; border-bottom: 1px solid rgba(255,255,255,0.03);">
<div style="display: flex; align-items: center; gap: 12px; flex: 1;">
<div style="font-size: 0.9rem; font-weight: 700; color: #9ca3af; width: 24px;">#{row['Overall Rank']}</div>
<div>
<div style="font-size: 0.95rem; font-weight: 600; color: {text_color};">{row['Manager']}</div>
<div style="font-size: 0.75rem; color: #9ca3af;">{row['Team Name']}</div>
</div>
</div>
<div style="text-align: right;">
<div style="font-size: 1.1rem; font-weight: 800; color: #ffffff;">{row['Total Points']}</div>
<div style="font-size: 0.75rem; color: #9ca3af;">GW: {row['GW Points']} ({row['Rank Change']})</div>
</div>
</div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_spy_card(rival):
    gw_diff = rival['GW Diff']
    tot_diff = rival['Total Diff']
    gw_color = "#00ff87" if gw_diff > 0 else ("#ff2e63" if gw_diff < 0 else "#9ca3af")
    tot_color = "#00ff87" if tot_diff > 0 else ("#ff2e63" if tot_diff < 0 else "#9ca3af")
    overlap_pct = (rival['Overlap'] / 11) * 100
    
    html = f"""
    <div style="background: #15151f; border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">{rival['Manager']}</div>
                <div style="font-size: 0.8rem; color: #9ca3af;">{rival['Team']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.75rem; color: #9ca3af;">Captain</div>
                <div style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">{rival['Captain']}</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
            <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 12px; text-align: center;">
                <div style="font-size: 0.7rem; color: #9ca3af; text-transform: uppercase;">GW Diff</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: {gw_color};">{gw_diff:+d}</div>
            </div>
            <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 12px; text-align: center;">
                <div style="font-size: 0.7rem; color: #9ca3af; text-transform: uppercase;">Total Diff</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: {tot_color};">{tot_diff:+d}</div>
            </div>
        </div>
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 0.8rem; color: #9ca3af;">Squad Overlap</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: #ffffff;">{rival['Overlap']} / 11</span>
            </div>
            <div style="background: rgba(255,255,255,0.05); border-radius: 6px; height: 8px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #38003c, #00ff87); height: 100%; width: {overlap_pct}%; border-radius: 6px;"></div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
            <div><span style="color: #9ca3af;">Value:</span> <span style="color: #ffffff; font-weight: 600;">{rival['Value']}</span></div>
            <div><span style="color: #9ca3af;">Bank:</span> <span style="color: #ffffff; font-weight: 600;">{rival['Bank']}</span></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_radar_card(rival, my_form, my_total):
    if rival['Active Chip'] != "None" or rival['Form'] > my_form + 15:
        threat_text, threat_color, badge_bg = "HIGH THREAT", "#ff2e63", "rgba(255, 46, 99, 0.1)"
    elif rival['Form'] > my_form + 5 or rival['Hits'] > 8:
        threat_text, threat_color, badge_bg = "MEDIUM", "#ffa500", "rgba(255, 165, 0, 0.1)"
    else:
        threat_text, threat_color, badge_bg = "LOW", "#00ff87", "rgba(0, 255, 135, 0.1)"
        
    diff = rival['Total Pts'] - my_total
    all_chips = {'wildcard': 'WC', 'bboost': 'BB', '3xc': 'TC', 'freehit': 'FH'}
    chips_html = ""
    for k, v in all_chips.items():
        if k in rival['Remaining Chips']:
            chips_html += f"<span style='display: inline-block; padding: 4px 10px; background: rgba(0,255,135,0.1); color: #00ff87; border: 1px solid rgba(0,255,135,0.2); border-radius: 6px; font-size: 0.75rem; font-weight: 600; margin-right: 6px; margin-bottom: 6px;'>{v}</span>"
        else:
            chips_html += f"<span style='display: inline-block; padding: 4px 10px; background: rgba(255,255,255,0.03); color: #555; border: 1px solid rgba(255,255,255,0.05); border-radius: 6px; font-size: 0.75rem; font-weight: 600; margin-right: 6px; margin-bottom: 6px; text-decoration: line-through;'>{v}</span>"

    form_pct = min((rival['Form'] / 100) * 100, 100)

    html = f"""
    <div style="background: #15151f; border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; margin-bottom: 16px; border-left: 4px solid {threat_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">{rival['Manager']}</div>
                <div style="font-size: 0.8rem; color: #9ca3af;">{rival['Team']} • {diff:+d} pts</div>
            </div>
            <div style="background: {badge_bg}; color: {threat_color}; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; border: 1px solid {threat_color};">
                {threat_text}
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px; text-align: center;">
            <div>
                <div style="font-size: 0.7rem; color: #9ca3af; text-transform: uppercase;">Form</div>
                <div style="font-size: 1.2rem; font-weight: 800; color: #ffffff;">{rival['Form']}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #9ca3af; text-transform: uppercase;">Hits</div>
                <div style="font-size: 1.2rem; font-weight: 800; color: {'#ff2e63' if rival['Hits'] > 0 else '#00ff87'};">-{rival['Hits']}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #9ca3af; text-transform: uppercase;">H2H</div>
                <div style="font-size: 1rem; font-weight: 700; color: #ffffff;">{rival['H2H']}</div>
            </div>
        </div>
        <div style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 0.8rem; color: #9ca3af;">Recent Form Momentum</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: #ffffff;">{rival['Form']} pts</span>
            </div>
            <div style="background: rgba(255,255,255,0.05); border-radius: 6px; height: 8px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #38003c, #00ff87); height: 100%; width: {form_pct}%; border-radius: 6px;"></div>
            </div>
        </div>
        <div>
            <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 8px;">Chip Inventory</div>
            <div>{chips_html}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR & DATA FETCHING
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    league_1_name = st.text_input("Group 1 Name", value="FFM300")
    league_1_id = st.text_input("Group 1 League ID", value="1141295") 
    league_2_name = st.text_input("Group 2 Name", value="Fantasy250")
    league_2_id = st.text_input("Group 2 League ID", value="1137538") 
    my_name = st.text_input("Your Manager Name", value="Filimon Kifle")
    
    if st.button("🔄 Force Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=600)
def load_all_data(l1_id, l2_id):
    with st.spinner("Syncing with FPL API..."):
        l1 = fpl_api.get_league_standings(l1_id) if l1_id else None
        l2 = fpl_api.get_league_standings(l2_id) if l2_id else None
        boot = fpl_api.get_bootstrap_data()
        fixtures = fpl_api.get_fixtures()
    return l1, l2, boot, fixtures

l1_data, l2_data, bootstrap, fixtures = load_all_data(league_1_id, league_2_id)

# ==========================================
# 4. BACKEND LOGIC (PRESERVED EXACTLY)
# ==========================================
def get_current_and_next_gw(boot_data):
    current_gw, next_gw = 1, 1
    if not boot_data: return current_gw, next_gw
    for event in boot_data['events']:
        if event['is_current']: current_gw = event['id']
        if event['is_next']: next_gw = event['id']
    return current_gw, next_gw

# Initialize current_gw safely after function definition
current_gw, next_gw = get_current_and_next_gw(bootstrap) if bootstrap else (1, 1)

def process_standings(data):
    if not data or 'standings' not in data or 'results' not in data['standings']: return pd.DataFrame()
    df = pd.DataFrame(data['standings']['results'])
    df = df[['entry_name', 'player_name', 'total', 'event_total', 'rank', 'last_rank', 'entry']]
    df.columns = ['Team Name', 'Manager', 'Total Points', 'GW Points', 'Overall Rank', 'Previous Rank', 'Entry ID']
    df['Rank Change'] = df['Previous Rank'] - df['Overall Rank']
    df['Rank Change'] = df['Rank Change'].apply(lambda x: f"▲ {x}" if x > 0 else (f"▼ {abs(x)}" if x < 0 else "-"))
    return df.sort_values(by='Overall Rank').reset_index(drop=True)

def get_my_data(df, name):
    for _, row in df.iterrows():
        if name.lower() in row['Manager'].lower(): return row
    return None

def build_spy_data(standings_df, boot_data, my_name):
    if standings_df.empty or not boot_data: return [], None
    current_gw, _ = get_current_and_next_gw(boot_data)
    player_lookup = {p['id']: p for p in boot_data['elements']}
    my_entry_id = next((row['Entry ID'] for _, row in standings_df.iterrows() if my_name.lower() in row['Manager'].lower()), None)
    if not my_entry_id: return [], None
    
    my_picks = fpl_api.get_entry_picks(my_entry_id, current_gw)
    my_live = fpl_api.get_entry_live(my_entry_id)
    my_starting_ids = [p['element'] for p in my_picks['picks'] if p['position'] <= 11] if my_picks and 'picks' in my_picks else []
    
    spy_data = []
    for _, row in standings_df.iterrows():
        if row['Entry ID'] == my_entry_id: continue
        picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
        live_data = fpl_api.get_entry_live(row['Entry ID'])
        if picks and 'picks' in picks:
            starting_11 = [p for p in picks['picks'] if p['position'] <= 11]
            captain = next((player_lookup[p['element']]['web_name'] for p in starting_11 if p['is_captain']), "None")
            overlap = len(set(my_starting_ids) & set([p['element'] for p in starting_11]))
            value = live_data['entry_history']['value'] / 10 if live_data and 'entry_history' in live_data else 0
            bank = live_data['entry_history']['bank'] / 10 if live_data and 'entry_history' in live_data else 0
            gw_diff = row['GW Points'] - standings_df[standings_df['Entry ID'] == my_entry_id]['GW Points'].values[0]
            total_diff = row['Total Points'] - standings_df[standings_df['Entry ID'] == my_entry_id]['Total Points'].values[0]
            spy_data.append({
                'Manager': row['Manager'], 'Team': row['Team Name'], 'Captain': captain, 
                'Overlap': overlap, 'GW Diff': gw_diff, 'Total Diff': total_diff,
                'Value': f"£{value}m", 'Bank': f"£{bank}m"
            })
        time.sleep(0.1)
    return spy_data, my_entry_id

def build_rival_radar(standings_df, boot_data, my_name):
    if standings_df.empty or not boot_data: return None, []
    current_gw, _ = get_current_and_next_gw(boot_data)
    my_idx = next((idx for idx, row in standings_df.iterrows() if my_name.lower() in row['Manager'].lower()), -1)
    if my_idx == -1: return None, []
    
    rival_indices = []
    if my_idx > 0: rival_indices.append(my_idx - 1)
    if my_idx < len(standings_df) - 1: rival_indices.append(my_idx + 1)
    targets = [my_idx] + rival_indices
    
    radar_data = []
    all_chips = {'wildcard': 'WC', 'bboost': 'BB', '3xc': 'TC', 'freehit': 'FH'}
    
    for idx in targets:
        row = standings_df.iloc[idx]
        history = fpl_api.get_entry_history(row['Entry ID'])
        picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
        if not history or not picks: continue
        
        gw_history = sorted(history['current'], key=lambda x: x['event'], reverse=True)
        form = round(sum(g['total_points'] for g in gw_history[:3]) / len(gw_history[:3]), 1) if gw_history else 0
        hits = sum(g.get('event_transfers_cost', 0) for g in history['current'])
        used_chips = [c['name'] for c in history.get('chips', [])]
        remaining_chips = {k: v for k, v in all_chips.items() if k not in used_chips}
        
        starting_11 = [p for p in picks['picks'] if p['position'] <= 11]
        captain_id = next((p['element'] for p in starting_11 if p['is_captain']), None)
        captain_name = next((p['web_name'] for p in boot_data['elements'] if p['id'] == captain_id), "None") if captain_id else "None"
        active_chip_raw = picks.get('active_chip', None)
        active_chip = all_chips.get(active_chip_raw, "None") if active_chip_raw else "None"
        
        radar_data.append({
            'Manager': row['Manager'], 'Team': row['Team Name'], 'Is Me': (idx == my_idx),
            'Total Pts': row['Total Points'], 'Form': form, 'Hits': hits,
            'Remaining Chips': remaining_chips, 'Captain': captain_name, 'Active Chip': active_chip,
            'GW History': gw_history
        })
        time.sleep(0.1)
        
    my_data = next((r for r in radar_data if r['Is Me']), None)
    if my_data:
        for rival in radar_data:
            if not rival['Is Me']:
                wins, losses, draws = 0, 0, 0
                for my_gw in my_data['GW History']:
                    rival_gw = next((r for r in rival['GW History'] if r['event'] == my_gw['event']), None)
                    if rival_gw:
                        if my_gw['total_points'] > rival_gw['total_points']: wins += 1
                        elif my_gw['total_points'] < rival_gw['total_points']: losses += 1
                        else: draws += 1
                rival['H2H'] = f"{wins}W - {losses}L - {draws}D"
            else:
                rival['H2H'] = "—"
    return my_data, [r for r in radar_data if not r['Is Me']]

def calculate_fdr(standings_df, boot_data, fixtures_data):
    if not fixtures_data or not boot_data: return {}
    current_gw, _ = get_current_and_next_gw(boot_data)
    upcoming = sorted([f for f in fixtures_data if f['event'] and f['event'] >= current_gw and not f['started']], key=lambda x: x['event'])
    team_fdr = {i: [] for i in range(1, 21)}
    for fix in upcoming:
        if len(team_fdr[fix['team_h']]) < 3: team_fdr[fix['team_h']].append(fix['team_h_difficulty'])
        if len(team_fdr[fix['team_a']]) < 3: team_fdr[fix['team_a']].append(fix['team_a_difficulty'])
    team_avg = {t: round(sum(f)/len(f), 2) if f else 3.0 for t, f in team_fdr.items()}
    player_lookup = {p['id']: p for p in boot_data['elements']}
    manager_fdr = {}
    for _, row in standings_df.iterrows():
        picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
        if picks and 'picks' in picks:
            starting_11 = [p['element'] for p in picks['picks'] if p['position'] <= 11]
            fdrs = [team_avg.get(player_lookup[pid]['team'], 3.0) for pid in starting_11]
            manager_fdr[row['Manager']] = round(sum(fdrs)/len(fdrs), 2) if fdrs else 3.0
        time.sleep(0.05)
    return manager_fdr

# ==========================================
# 5. MAIN APP LAYOUT & TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"🏆 {league_1_name}", f"🏆 {league_2_name}", "🕵️ Spy", "🧠 Strategy", "📡 Radar"
])

# --- TAB 1 & 2: LEAGUES ---
def render_league_tab(data, group_name):
    df = process_standings(data)
    if df.empty:
        st.warning("Enter a valid League ID in the sidebar.")
        return
        
    my_data = get_my_data(df, my_name)
    if my_data is not None:
        render_hero(my_data['Manager'], current_gw, my_data['GW Points'], my_data['Total Points'], my_data['Overall Rank'])
    else:
        st.warning(f"Could not find '{my_name}' in this group.")
        
    render_podium(df)
    
    with st.expander("📊 Full Leaderboard", expanded=False):
        render_leaderboard(df, my_name)

with tab1: render_league_tab(l1_data, league_1_name)
with tab2: render_league_tab(l2_data, league_2_name)

# --- TAB 3: SPY VS ME ---
with tab3:
    st.markdown("### 🕵️ SPY VS ME")
    st.markdown("<p style='color:#9ca3af; margin-top:-10px;'>Know exactly where your rivals are gaining ground.</p>", unsafe_allow_html=True)
    
    group_to_spy = st.radio("Group:", [league_1_name, league_2_name], horizontal=True, label_visibility="collapsed", key="spy_grp")
    
    if st.button("🔍 Scan Opponents", use_container_width=True):
        standings_df = process_standings(l1_data) if group_to_spy == league_1_name else process_standings(l2_data)
        if not standings_df.empty and bootstrap:
            with st.spinner("Intercepting signals..."):
                spy_list, my_id = build_spy_data(standings_df, bootstrap, my_name)
                st.session_state['spy_list'] = spy_list

    if 'spy_list' in st.session_state and st.session_state['spy_list']:
        spy_list = st.session_state['spy_list']
        rival_names = [f"{s['Manager']} ({s['Team']})" for s in spy_list]
        selected_rival = st.selectbox("Select Rival to Profile:", rival_names)
        rival_data = next(s for s in spy_list if f"{s['Manager']} ({s['Team']})" == selected_rival)
        render_spy_card(rival_data)

# --- TAB 4: STRATEGY LAB ---
with tab4:
    st.markdown("### 🧠 STRATEGY LAB")
    st.markdown("<p style='color:#9ca3af; margin-top:-10px;'>Advanced analytics terminal for tactical decisions.</p>", unsafe_allow_html=True)
    
    group_for_strat = st.radio("Group:", [league_1_name, league_2_name], horizontal=True, label_visibility="collapsed", key="strat_grp")
    
    if st.button("🚀 Generate Insights", use_container_width=True):
        standings_df = process_standings(l1_data) if group_for_strat == league_1_name else process_standings(l2_data)
        if not standings_df.empty and bootstrap and fixtures:
            with st.spinner("Crunching numbers..."):
                player_lookup = {p['id']: p for p in bootstrap['elements']}
                all_owned, xpts_data = [], []
                
                for _, row in standings_df.iterrows():
                    picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
                    if picks and 'picks' in picks:
                        starting_11 = [p['element'] for p in picks['picks'] if p['position'] <= 11]
                        all_owned.extend(starting_11)
                        xpts = sum(float(player_lookup[pid].get('xP', 0)) for pid in starting_11)
                        xpts_data.append({'Manager': row['Manager'], 'xPts': round(xpts, 1)})
                    time.sleep(0.05)
                
                st.session_state['strat_data'] = {
                    'bandwagon': Counter(all_owned).most_common(5), 
                    'xpts': xpts_data,
                    'fdr': calculate_fdr(standings_df, bootstrap, fixtures),
                    'player_lookup': player_lookup, 'total_managers': len(standings_df),
                    'gw_winner': standings_df.sort_values(by='GW Points', ascending=False).iloc[0],
                    'overall_leader': standings_df.iloc[0]
                }

    if 'strat_data' in st.session_state:
        sd = st.session_state['strat_data']
        
        st.markdown("#### 🚌 Bandwagon Tracker")
        bw_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 24px;">'
        for pid, count in sd['bandwagon']:
            p = sd['player_lookup'][pid]
            # NO LEADING SPACES inside the f-string
            bw_html += f"""<div style="background: #15151f; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; text-align: center;">
<div style="font-size: 0.95rem; font-weight: 700; color: #ffffff; margin-bottom: 8px;">{p['web_name']}</div>
<div style="font-size: 1.8rem; font-weight: 800; color: #00ff87;">{count}/{sd['total_managers']}</div>
<div style="font-size: 0.75rem; color: #9ca3af;">Global: {p['selected_by_percent']}%</div>
</div>"""
        bw_html += '</div>'
        st.markdown(bw_html, unsafe_allow_html=True)

        st.markdown("#### 🔮 Expected Points (xPts)")
        xpts_html = '<div style="background: #15151f; border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; overflow: hidden; margin-bottom: 24px;">'
        sd['xpts'].sort(key=lambda x: x['xPts'], reverse=True)
        
        # FIX: Ensure max_xpts is at least 1 to prevent ZeroDivisionError
        max_xpts = sd['xpts'][0]['xPts'] if sd['xpts'] else 1
        if max_xpts == 0:
            max_xpts = 1
            
            for item in sd['xpts']:
                is_me = my_name.lower() in item['Manager'].lower()
                bg = "rgba(0, 255, 135, 0.05)" if is_me else "transparent"
                bar_width = (item['xPts'] / max_xpts) * 100
                
                # FIX: NO LEADING SPACES inside the f-string to prevent Markdown code-block formatting
                xpts_html += f"""<div style="display: flex; align-items: center; padding: 12px 16px; background: {bg}; border-bottom: 1px solid rgba(255,255,255,0.03);">
    <div style="flex: 1;">
    <div style="font-size: 0.95rem; font-weight: 600; color: {'#00ff87' if is_me else '#ffffff'};">{item['Manager']}</div>
    <div style="background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; margin-top: 6px; overflow: hidden;">
    <div style="background: #38003c; height: 100%; width: {bar_width}%; border-radius: 4px;"></div>
    </div>
    </div>
    <div style="font-size: 1.1rem; font-weight: 800; color: #ffffff; margin-left: 16px;">{item['xPts']}</div>
    </div>"""
        xpts_html += '</div>'
        st.markdown(xpts_html, unsafe_allow_html=True)

        st.markdown("#### 🗓️ Fixture Difficulty (Next 3 GWs)")
        fdr_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 24px;">'
        for manager, fdr in sorted(sd['fdr'].items(), key=lambda x: x[1])[:5]:
            color = "#00ff87" if fdr <= 2.5 else ("#ffa500" if fdr <= 3.5 else "#ff2e63")
            # NO LEADING SPACES inside the f-string
            fdr_html += f"""<div style="background: #15151f; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; text-align: center; border-top: 3px solid {color};">
<div style="font-size: 0.9rem; font-weight: 600; color: #ffffff; margin-bottom: 8px;">{manager}</div>
<div style="font-size: 1.8rem; font-weight: 800; color: {color};">{fdr}</div>
<div style="font-size: 0.75rem; color: #9ca3af;">Avg FDR</div>
</div>"""
        fdr_html += '</div>'
        st.markdown(fdr_html, unsafe_allow_html=True)

        st.markdown("#### 📱 Social Summary")
        top_bw_p = sd['player_lookup'][sd['bandwagon'][0][0]]['web_name']
        summary_text = f"""🚨 *FPL GW{current_gw} UPDATE!* 🚨\n\n🏆 *GW Winner:* {sd['gw_winner']['Manager']} ({sd['gw_winner']['GW Points']} pts)\n👑 *Overall Leader:* {sd['overall_leader']['Manager']} ({sd['overall_leader']['Total Points']} pts)\n\n🔥 *Bandwagon Alert:* {top_bw_p} is owned by {sd['bandwagon'][0][1]}/{sd['total_managers']} of you!\n\nMake your transfers and may the best team win! ⚽"""
        st.code(summary_text, language="markdown")

# --- TAB 5: RIVAL RADAR ---
with tab5:
    st.markdown("### 📡 RIVAL RADAR")
    st.markdown("<p style='color:#9ca3af; margin-top:-10px;'>Tactical intelligence on your closest threats.</p>", unsafe_allow_html=True)
    
    group_for_radar = st.radio("Group:", [league_1_name, league_2_name], horizontal=True, label_visibility="collapsed", key="radar_grp")
    
    if st.button("📡 Scan Rivals", use_container_width=True):
        standings_df = process_standings(l1_data) if group_for_radar == league_1_name else process_standings(l2_data)
        if not standings_df.empty and bootstrap:
            with st.spinner("Profiling targets..."):
                my_radar, rivals_radar = build_rival_radar(standings_df, bootstrap, my_name)
                st.session_state['my_radar'] = my_radar
                st.session_state['rivals_radar'] = rivals_radar

    if 'my_radar' in st.session_state and st.session_state['my_radar']:
        my_r = st.session_state['my_radar']
        st.markdown("#### 👤 Your Profile")
        # Reusing render_radar_card for consistency, but passing dummy high values for threat logic so it doesn't flag myself
        my_r_display = my_r.copy()
        my_r_display['Active Chip'] = "None" 
        my_r_display['Form'] = 0 # Force LOW threat visually for self
        render_radar_card(my_r_display, 100, 9999) 
        
        st.markdown("#### ⚔️ Closest Rivals")
        for rival in st.session_state['rivals_radar']:
            render_radar_card(rival, my_r['Form'], my_r['Total Pts'])