import streamlit as st
import pandas as pd
import fpl_api
import time

# --- PAGE CONFIG & CSS ---
st.set_page_config(page_title="FPL War Room", layout="centered", page_icon="⚽")

st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .block-container { padding: 1.5rem 1rem; max-width: 900px; }
    h1, h2, h3 { color: #38003c; }
    [data-testid="stSidebar"] { background-color: #38003c; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: white !important; }
    
    .podium-card { background-color: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #38003c; margin-bottom: 15px; }
    .podium-card h3 { margin: 0; font-size: 1.1rem; color: #38003c; }
    .podium-card p { margin: 5px 0; font-size: 0.9rem; color: #666; }
    .podium-card .points { font-size: 1.8rem; font-weight: bold; color: #00ff87; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
    .crown { font-size: 1.5rem; }
    
    .gw-banner { background: linear-gradient(90deg, #38003c, #00ff87); color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; font-size: 1.2rem; font-weight: bold;}
    .metric-positive { color: #008000; font-weight: bold; }
    .metric-negative { color: #ff0000; font-weight: bold; }
        /* Rival Radar Cards */
    .radar-card { 
        background-color: white; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 15px; 
        border-left: 5px solid #38003c; 
    }
    .radar-card.me { border-left-color: #00ff87; background: linear-gradient(135deg, #ffffff 0%, #f0fff4 100%); }
    .radar-card h3 { margin-top: 0; color: #38003c; font-size: 1.2rem; }
    .radar-stat { display: flex; justify-content: space-between; margin: 8px 0; font-size: 0.95rem; }
    .radar-stat span:last-child { font-weight: bold; color: #333; }
    .chip-used { color: #ccc; text-decoration: line-through; margin-right: 10px; }
    .chip-available { color: #00ff87; font-weight: bold; margin-right: 10px; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ League Settings")
    league_1_name = st.text_input("Group 1 Name", value="Group 1")
    league_1_id = st.text_input("Group 1 League ID", value="") 
    league_2_name = st.text_input("Group 2 Name", value="Group 2")
    league_2_id = st.text_input("Group 2 League ID", value="") 
    
    st.markdown("---")
    st.markdown("**My Manager Name:**")
    my_name = st.text_input("Your Name (for comparisons)", value="Filimon Kifle")
    
    if st.button("🔄 Force Refresh Data", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- DATA FETCHING (CACHED) ---
@st.cache_data(ttl=600) # Cache for 10 mins
def load_all_data(l1_id, l2_id):
    with st.spinner("Fetching master data..."):
        l1 = fpl_api.get_league_standings(l1_id) if l1_id else None
        l2 = fpl_api.get_league_standings(l2_id) if l2_id else None
        boot = fpl_api.get_bootstrap_data()
        fixtures = fpl_api.get_fixtures()
    return l1, l2, boot, fixtures

l1_data, l2_data, bootstrap, fixtures = load_all_data(league_1_id, league_2_id)

# --- HELPER FUNCTIONS ---
def get_current_and_next_gw(boot_data):
    current_gw, next_gw = 1, 1
    if not boot_data: return current_gw, next_gw
    for event in boot_data['events']:
        if event['is_current']: current_gw = event['id']
        if event['is_next']: next_gw = event['id']
    return current_gw, next_gw

def process_standings(data):
    if not data or 'standings' not in data or 'results' not in data['standings']: return pd.DataFrame()
    df = pd.DataFrame(data['standings']['results'])
    df = df[['entry_name', 'player_name', 'total', 'event_total', 'rank', 'last_rank', 'entry']]
    df.columns = ['Team Name', 'Manager', 'Total Points', 'GW Points', 'Overall Rank', 'Previous Rank', 'Entry ID']
    df['Rank Change'] = df['Previous Rank'] - df['Overall Rank']
    df['Rank Change'] = df['Rank Change'].apply(lambda x: f"▲ {x}" if x > 0 else (f"▼ {abs(x)}" if x < 0 else "-"))
    return df.sort_values(by='Overall Rank').reset_index(drop=True)

def calculate_fdr(standings_df, boot_data, fixtures_data):
    """Calculates average FDR for next 3 fixtures for each manager."""
    if not fixtures_data or not boot_data: return {}
    
    current_gw, _ = get_current_and_next_gw(boot_data)
    upcoming_fixtures = [f for f in fixtures_data if f['event'] and f['event'] >= current_gw and not f['started']]
    upcoming_fixtures.sort(key=lambda x: x['event'])
    
    # Map team to next 3 FDRs
    team_fdr = {i: [] for i in range(1, 21)}
    for fix in upcoming_fixtures:
        h_team, a_team = fix['team_h'], fix['team_a']
        if len(team_fdr[h_team]) < 3: team_fdr[h_team].append(fix['team_h_difficulty'])
        if len(team_fdr[a_team]) < 3: team_fdr[a_team].append(fix['team_a_difficulty'])
            
    team_avg_fdr = {t: round(sum(f)/len(f), 2) if f else 3.0 for t, f in team_fdr.items()}
    
    player_lookup = {p['id']: p for p in boot_data['elements']}
    manager_fdr = {}
    
    for _, row in standings_df.iterrows():
        picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
        if picks and 'picks' in picks:
            starting_11 = [p['element'] for p in picks['picks'] if p['position'] <= 11]
            fdrs = [team_avg_fdr.get(player_lookup[pid]['team'], 3.0) for pid in starting_11]
            manager_fdr[row['Entry ID']] = round(sum(fdrs)/len(fdrs), 2) if fdrs else 3.0
        time.sleep(0.1)
    return manager_fdr

def build_spy_data(standings_df, boot_data, my_name):
    """Builds the comprehensive spy data comparing everyone to 'my_name'."""
    if standings_df.empty or not boot_data: return [], None
    
    current_gw, next_gw = get_current_and_next_gw(boot_data)
    player_lookup = {p['id']: p for p in boot_data['elements']}
    
    # Find my entry ID
    my_entry_id = None
    for _, row in standings_df.iterrows():
        if my_name.lower() in row['Manager'].lower():
            my_entry_id = row['Entry ID']
            break
            
    if not my_entry_id: return [], None
    
    # Get my data using the LIVE endpoint
    my_picks = fpl_api.get_entry_picks(my_entry_id, current_gw)
    my_live = fpl_api.get_entry_live(my_entry_id)
    
    my_starting_ids = [p['element'] for p in my_picks['picks'] if p['position'] <= 11] if my_picks and 'picks' in my_picks else []
    
    # FIX: Extract value from 'entry_history' in the live data
    my_value = my_live['entry_history']['value'] / 10 if my_live and 'entry_history' in my_live else 0
    
    spy_data = []
    progress_bar = st.progress(0)
    
    for index, row in standings_df.iterrows():
        if row['Entry ID'] == my_entry_id: continue # Skip myself
        
        progress_bar.progress((index + 1) / len(standings_df))
        
        picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
        live_data = fpl_api.get_entry_live(row['Entry ID']) # Use the live endpoint
        
        if picks and 'picks' in picks:
            starting_11 = [p for p in picks['picks'] if p['position'] <= 11]
            friend_ids = [p['element'] for p in starting_11]
            
            captain = next((player_lookup[p['element']]['web_name'] for p in starting_11 if p['is_captain']), "None")
            overlap = len(set(my_starting_ids) & set(friend_ids))
            
            # FIX: Extract value and bank from 'entry_history'
            value = live_data['entry_history']['value'] / 10 if live_data and 'entry_history' in live_data else 0
            bank = live_data['entry_history']['bank'] / 10 if live_data and 'entry_history' in live_data else 0
            
            gw_diff = row['GW Points'] - standings_df[standings_df['Entry ID'] == my_entry_id]['GW Points'].values[0]
            total_diff = row['Total Points'] - standings_df[standings_df['Entry ID'] == my_entry_id]['Total Points'].values[0]
            
            # Next GW xPts
            next_xpts = sum(float(player_lookup[pid].get('xP', 0)) for pid in friend_ids)
            
            spy_data.append({
                'Manager': row['Manager'], 'Team': row['Team Name'],
                'Captain': captain, 'Overlap': overlap,
                'GW Diff': gw_diff, 'Total Diff': total_diff,
                'Value': f"£{value}m", 'Bank': f"£{bank}m",
                'Next xPts': round(next_xpts, 1)
            })
        time.sleep(0.2)
        
    progress_bar.empty()
    return spy_data, my_entry_id
    """Builds the comprehensive spy data comparing everyone to 'my_name'."""
    if standings_df.empty or not boot_data: return [], None
    
    current_gw, next_gw = get_current_and_next_gw(boot_data)
    player_lookup = {p['id']: p for p in boot_data['elements']}
    
    # Find my entry ID
    my_entry_id = None
    for _, row in standings_df.iterrows():
        if my_name.lower() in row['Manager'].lower():
            my_entry_id = row['Entry ID']
            break
            
    if not my_entry_id: return [], None
    
    # Get my data
    my_picks = fpl_api.get_entry_picks(my_entry_id, current_gw)
    my_details = fpl_api.get_entry_details(my_entry_id)
    my_starting_ids = [p['element'] for p in my_picks['picks'] if p['position'] <= 11] if my_picks and 'picks' in my_picks else []
    my_value = my_details['value'] / 10 if my_details else 0
    
    spy_data = []
    progress_bar = st.progress(0)
    
    for index, row in standings_df.iterrows():
        if row['Entry ID'] == my_entry_id: continue # Skip myself
        
        progress_bar.progress((index + 1) / len(standings_df))
        
        picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
        details = fpl_api.get_entry_details(row['Entry ID'])
        
        if picks and 'picks' in picks:
            starting_11 = [p for p in picks['picks'] if p['position'] <= 11]
            friend_ids = [p['element'] for p in starting_11]
            
            captain = next((player_lookup[p['element']]['web_name'] for p in starting_11 if p['is_captain']), "None")
            overlap = len(set(my_starting_ids) & set(friend_ids))
            
            value = details['value'] / 10 if details else 0
            bank = details['bank'] / 10 if details else 0
            
            gw_diff = row['GW Points'] - standings_df[standings_df['Entry ID'] == my_entry_id]['GW Points'].values[0]
            total_diff = row['Total Points'] - standings_df[standings_df['Entry ID'] == my_entry_id]['Total Points'].values[0]
            
            # Next GW xPts
            next_xpts = sum(float(player_lookup[pid].get('xP', 0)) for pid in friend_ids)
            
            spy_data.append({
                'Manager': row['Manager'], 'Team': row['Team Name'],
                'Captain': captain, 'Overlap': overlap,
                'GW Diff': gw_diff, 'Total Diff': total_diff,
                'Value': f"£{value}m", 'Bank': f"£{bank}m",
                'Next xPts': round(next_xpts, 1)
            })
        time.sleep(0.2)
        
    progress_bar.empty()
    return spy_data, my_entry_id

def build_rival_radar(standings_df, boot_data, my_name):
    """Calculates deep psychological and statistical data on your closest rivals."""
    if standings_df.empty or not boot_data: return None, []
    
    current_gw, _ = get_current_and_next_gw(boot_data)
    
    # 1. Find my index and identify closest rivals
    my_idx = -1
    for idx, row in standings_df.iterrows():
        if my_name.lower() in row['Manager'].lower():
            my_idx = idx
            break
            
    if my_idx == -1: return None, []
    
    # Get the rival above (lower index) and below (higher index)
    rival_indices = []
    if my_idx > 0: rival_indices.append(my_idx - 1) # Rival above
    if my_idx < len(standings_df) - 1: rival_indices.append(my_idx + 1) # Rival below
    
    targets = [my_idx] + rival_indices
    
    radar_data = []
    progress_bar = st.progress(0)
    
    for i, idx in enumerate(targets):
        row = standings_df.iloc[idx]
        entry_id = row['Entry ID']
        is_me = (idx == my_idx)
        
        progress_bar.progress((i + 1) / len(targets))
        
        # Fetch deep data
        history = fpl_api.get_entry_history(entry_id)
        picks = fpl_api.get_entry_picks(entry_id, current_gw)
        
        if not history or not picks: continue
        
        # --- CALCULATIONS ---
        
        # 1. Form (Last 3 GWs average)
        gw_history = sorted(history['current'], key=lambda x: x['event'], reverse=True)
        last_3 = gw_history[:3]
        form = round(sum(g['total_points'] for g in last_3) / len(last_3), 1) if last_3 else 0
        
        # 2. Transfer Hits (Total points lost)
        hits = sum(g.get('event_transfers_cost', 0) for g in history['current'])
        
        # 3. Chips Remaining
        all_chips = {'wildcard': 'WC', 'bboost': 'BB', '3xc': 'TC', 'freehit': 'FH'}
        used_chips = [c['name'] for c in history.get('chips', [])]
        remaining_chips = {k: v for k, v in all_chips.items() if k not in used_chips}
        
        # 4. Current Threat (Captain & Active Chip)
        starting_11 = [p for p in picks['picks'] if p['position'] <= 11]
        captain = next((p['element'] for p in starting_11 if p['is_captain']), None)
        captain_name = "None"
        if captain:
            captain_name = next((p['web_name'] for p in boot_data['elements'] if p['id'] == captain), "Unknown")
            
        active_chip_raw = picks.get('active_chip', None)
        active_chip = all_chips.get(active_chip_raw, "None") if active_chip_raw else "None"
        
        radar_data.append({
            'Manager': row['Manager'],
            'Team': row['Team Name'],
            'Is Me': is_me,
            'Total Pts': row['Total Points'],
            'Form (Last 3)': form,
            'Hits Taken': hits,
            'Remaining Chips': remaining_chips,
            'Captain': captain_name,
            'Active Chip': active_chip,
            'GW History': gw_history # Keep for H2H calculation
        })
        time.sleep(0.2)
        
    progress_bar.empty()
    
    # 5. Calculate Head-to-Head (H2H) for rivals against ME
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
# --- UI LAYOUT ---
st.markdown("<h1 style='text-align: center;'>⚽ FPL War Room</h1>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"🏆 {league_1_name}", f"🏆 {league_2_name}", "🕵️ Spy vs Me", "🧠 Strategy", "🎯 Radar"
])

# --- TAB 1 & 2: LEADERBOARDS ---
def render_leaderboard_tab(data, group_name):
    df = process_standings(data)
    if df.empty:
        st.warning("Enter a valid League ID in the sidebar.")
        return

    gw_winner = df.sort_values(by='GW Points', ascending=False).iloc[0]
    st.markdown(f'<div class="gw-banner">🏆 GW Winner: {gw_winner["Manager"]} ({gw_winner["GW Points"]} pts) | Overall Leader: {df.iloc[0]["Manager"]} ({df.iloc[0]["Total Points"]} pts)</div>', unsafe_allow_html=True)
    
    st.subheader(f"Top 3")
    top3 = df.head(3)
    cols = st.columns(3)
    for i, col in enumerate(cols):
        if i < len(top3):
            row = top3.iloc[i]
            crown = "👑" if i == 0 else ("🥈" if i == 1 else "🥉")
            with col:
                st.markdown(f"""
                <div class="podium-card">
                    <span class="crown">{crown}</span>
                    <h3>{row['Manager']}</h3>
                    <p>{row['Team Name']}</p>
                    <div class="points">{row['Total Points']}</div>
                    <p>GW: {row['GW Points']} pts ({row['Rank Change']})</p>
                </div>
                """, unsafe_allow_html=True)

    with st.expander("📊 View Full Table", expanded=False):
        st.dataframe(df.drop(columns=['Entry ID']), use_container_width=True, hide_index=True)

with tab1: render_leaderboard_tab(l1_data, league_1_name)
with tab2: render_leaderboard_tab(l2_data, league_2_name)

# --- TAB 3: SPY VS ME (FILIMON) ---
with tab3:
    st.subheader(f"🕵️ Spy Mode: Comparing to {my_name}")
    st.markdown("See who is beating you, who shares your players, and who has the budget to make moves.")
    
    group_to_spy = st.radio("Select Group:", [league_1_name, league_2_name], horizontal=True, label_visibility="collapsed")
    
    if st.button("🔍 Execute Spy Mission", use_container_width=True, type="primary"):
        standings_df = process_standings(l1_data) if group_to_spy == league_1_name else process_standings(l2_data)
        
        if not standings_df.empty and bootstrap:
            with st.spinner("Spying and calculating..."):
                spy_list, my_id = build_spy_data(standings_df, bootstrap, my_name)
                
            if not my_id:
                st.error(f"Could not find '{my_name}' in this group. Check the spelling in the sidebar.")
            else:
                st.success(f"Found your team! Analyzing {len(spy_list)} opponents...")
                for spy in spy_list:
                    with st.expander(f"**{spy['Manager']}** ({spy['Team']})"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Captain", spy['Captain'])
                        c2.metric("Shared Players", f"{spy['Overlap']}/11")
                        c3.metric("Squad Value", spy['Value'])
                        
                        c4, c5 = st.columns(2)
                        gw_class = "metric-positive" if spy['GW Diff'] > 0 else ("metric-negative" if spy['GW Diff'] < 0 else "")
                        tot_class = "metric-positive" if spy['Total Diff'] > 0 else ("metric-negative" if spy['Total Diff'] < 0 else "")
                        
                        c4.markdown(f"**GW Point Diff:** <span class='{gw_class}'>{spy['GW Diff']:+d}</span>", unsafe_allow_html=True)
                        c5.markdown(f"**Overall Diff:** <span class='{tot_class}'>{spy['Total Diff']:+d}</span>", unsafe_allow_html=True)
                        
                        st.caption(f"Bank: {spy['Bank']} | Next GW xPts: {spy['Next xPts']}")

# --- TAB 4: STRATEGY LAB (THE 4 OPTIONS) ---
with tab4:
    st.subheader("🧠 Strategy Lab")
    st.markdown("Data-driven insights to help you win.")
    
    group_for_strategy = st.radio("Select Group for Analysis:", [league_1_name, league_2_name], horizontal=True, key="strat_group", label_visibility="collapsed")
    
    if st.button("🚀 Generate Insights", use_container_width=True, type="primary"):
        standings_df = process_standings(l1_data) if group_for_strategy == league_1_name else process_standings(l2_data)
        
        if not standings_df.empty and bootstrap and fixtures:
            current_gw, next_gw = get_current_and_next_gw(bootstrap)
            player_lookup = {p['id']: p for p in bootstrap['elements']}
            
            with st.spinner("Calculating deep insights..."):
                # 1. Bandwagon (Group Ownership)
                all_owned = []
                # 2. xPts for next GW
                next_xpts_data = []
                
                for _, row in standings_df.iterrows():
                    picks = fpl_api.get_entry_picks(row['Entry ID'], current_gw)
                    if picks and 'picks' in picks:
                        starting_11 = [p['element'] for p in picks['picks'] if p['position'] <= 11]
                        all_owned.extend(starting_11)
                        
                        xpts = sum(float(player_lookup[pid].get('xP', 0)) for pid in starting_11)
                        next_xpts_data.append({'Manager': row['Manager'], 'xPts': round(xpts, 1)})
                    time.sleep(0.1)
                
                # 3. FDR
                fdr_data = calculate_fdr(standings_df, bootstrap, fixtures)
                
                # 4. Summary
                gw_winner = standings_df.sort_values(by='GW Points', ascending=False).iloc[0]
                overall_leader = standings_df.iloc[0]
                
            st.markdown("---")
            
            # Display Option 1: Bandwagon
            st.markdown("### 🚌 The Bandwagon Tracker")
            st.caption("Players most owned by your friends. If you don't own them, you're risking falling behind.")
            from collections import Counter
            ownership_counts = Counter(all_owned)
            top_bandwagon = ownership_counts.most_common(5)
            bandwagon_df = pd.DataFrame([
                {'Player': player_lookup[pid]['web_name'], 'Owned by': f"{count}/{len(standings_df)} managers", 'Overall Own.': f"{player_lookup[pid]['selected_by_percent']}%"}
                for pid, count in top_bandwagon
            ])
            st.dataframe(bandwagon_df, use_container_width=True, hide_index=True)
            
            # Display Option 2: xPts
            st.markdown(f"### 🔮 Expected Points (xPts) for GW{next_gw}")
            st.caption("Who has the best mathematical chance of scoring big next week?")
            xpts_df = pd.DataFrame(next_xpts_data).sort_values(by='xPts', ascending=False).reset_index(drop=True)
            st.dataframe(xpts_df, use_container_width=True, hide_index=True)
            
            # Display Option 3: FDR
            st.markdown("### 🗓️ Fixture Difficulty (Next 3 GWs)")
            st.caption("Lower score = Easier fixtures. (1.0 is easiest, 5.0 is hardest)")
            fdr_list = [{'Manager': standings_df[standings_df['Entry ID'] == eid]['Manager'].values[0], 'Avg FDR': fdr} for eid, fdr in fdr_data.items()]
            fdr_df = pd.DataFrame(fdr_list).sort_values(by='Avg FDR').reset_index(drop=True)
            st.dataframe(fdr_df, use_container_width=True, hide_index=True)
            
            # Display Option 4: Auto Summary
            st.markdown("### 📋 Commissioner Auto-Summary")
            st.caption("Copy and paste this directly into your WhatsApp/Discord group!")
            summary_text = f"""🚨 *FPL GW{current_gw} UPDATE!* 🚨

🏆 *GW Winner:* {gw_winner['Manager']} ({gw_winner['GW Points']} pts)
👑 *Overall Leader:* {overall_leader['Manager']} ({overall_leader['Total Points']} pts)

🔥 *Bandwagon Alert:* {player_lookup[top_bandwagon[0][0]]['web_name']} is owned by {top_bandwagon[0][1]}/{len(standings_df)} of you!

🔮 *Best xPts for GW{next_gw}:* {xpts_df.iloc[0]['Manager']} ({xpts_df.iloc[0]['xPts']} xPts)

Make your transfers and may the best team win! ⚽"""
            st.code(summary_text, language="markdown")
# --- TAB 5: RIVAL RADAR ---
with tab5:
    st.subheader("🎯 Rival Radar")
    st.markdown("Deep psychological and statistical analysis of the managers directly above and below you.")
    
    group_for_radar = st.radio("Select Group:", [league_1_name, league_2_name], horizontal=True, key="radar_group", label_visibility="collapsed")
    
    if st.button("📡 Scan Rivals", use_container_width=True, type="primary"):
        standings_df = process_standings(l1_data) if group_for_radar == league_1_name else process_standings(l2_data)
        
        if not standings_df.empty and bootstrap:
            with st.spinner("Analyzing rival DNA..."):
                my_radar, rivals_radar = build_rival_radar(standings_df, bootstrap, my_name)
                
            if not my_radar:
                st.error(f"Could not find '{my_name}' in this group.")
            else:
                # Render My Card
                st.markdown(f"### 👤 Your Profile ({my_name})")
                chips_html = " ".join([f"<span class='chip-available'>{v}</span>" for k, v in my_radar['Remaining Chips'].items()] + 
                                      [f"<span class='chip-used'>{v}</span>" for k, v in {'wildcard': 'WC', 'bboost': 'BB', '3xc': 'TC', 'freehit': 'FH'}.items() if k not in my_radar['Remaining Chips']])
                
                st.markdown(f"""
                <div class="radar-card me">
                    <h3>{my_radar['Manager']} <span style="color:#00ff87;">(YOU)</span></h3>
                    <div class="radar-stat"><span>Total Points:</span> <span>{my_radar['Total Pts']}</span></div>
                    <div class="radar-stat"><span>Form (Last 3 GW Avg):</span> <span>{my_radar['Form (Last 3)']}</span></div>
                    <div class="radar-stat"><span>Transfer Hits Taken:</span> <span style="color:{'red' if my_radar['Hits Taken'] > 0 else 'green'};">-{my_radar['Hits Taken']} pts</span></div>
                    <div class="radar-stat"><span>This Week Captain:</span> <span>{my_radar['Captain']}</span></div>
                    <div class="radar-stat"><span>Chips Remaining:</span> <span>{chips_html}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render Rivals Cards
                for rival in rivals_radar:
                    chips_html_r = " ".join([f"<span class='chip-available'>{v}</span>" for k, v in rival['Remaining Chips'].items()] + 
                                            [f"<span class='chip-used'>{v}</span>" for k, v in {'wildcard': 'WC', 'bboost': 'BB', '3xc': 'TC', 'freehit': 'FH'}.items() if k not in rival['Remaining Chips']])
                    
                    threat_level = "🔥 HIGH" if rival['Active Chip'] != "None" or rival['Form (Last 3)'] > my_radar['Form (Last 3)'] + 10 else "🟢 NORMAL"
                    
                    st.markdown(f"### ⚔️ Rival Profile")
                    st.markdown(f"""
                    <div class="radar-card">
                        <h3>{rival['Manager']} ({rival['Team']})</h3>
                        <div class="radar-stat"><span>Total Points:</span> <span>{rival['Total Pts']} ({rival['Total Pts'] - my_radar['Total Pts']:+d} vs you)</span></div>
                        <div class="radar-stat"><span>Form (Last 3 GW Avg):</span> <span>{rival['Form (Last 3)']}</span></div>
                        <div class="radar-stat"><span>Transfer Hits Taken:</span> <span style="color:{'red' if rival['Hits Taken'] > 0 else 'green'};">-{rival['Hits Taken']} pts</span></div>
                        <div class="radar-stat"><span>Head-to-Head Record:</span> <span>{rival['H2H']}</span></div>
                        <div class="radar-stat"><span>This Week Captain:</span> <span>{rival['Captain']}</span></div>
                        <div class="radar-stat"><span>Active Chip:</span> <span style="color:{'red' if rival['Active Chip'] != 'None' else 'inherit'};">{rival['Active Chip']}</span></div>
                        <div class="radar-stat"><span>Chips Remaining:</span> <span>{chips_html_r}</span></div>
                        <div class="radar-stat"><span>Threat Level:</span> <span>{threat_level}</span></div>
                    </div>
                    """, unsafe_allow_html=True)