import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Student Score Processing System", page_icon="📊", layout="wide")

st.title("📊 Student Score Processing System")
st.write("Upload an Excel file to calculate Top N students per classroom, Top 50 of the whole grade, and absent students.")

# Sidebar Settings
st.sidebar.header("⚙️ Settings")
col_score = st.sidebar.text_input("Score Column Name", value="Sum")
col_name = st.sidebar.text_input("Student Name Column Name", value="Name")
round_to_int = st.sidebar.checkbox("Round scores to integer (like Excel)", value=False)
show_scores = st.sidebar.checkbox("Show Scores in Results", value=True)
top_n_room = st.sidebar.number_input("Top N per Classroom", min_value=1, max_value=10, value=3)

# File Uploader
uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        
        # Select sheets to process
        selected_sheets = st.multiselect("Select Classroom Sheets to Process", sheet_names, default=sheet_names[:11])
        
        if selected_sheets:
            records = []
            for i, sheet in enumerate(selected_sheets):
                room_label = f"Room {i + 1} ({sheet})"
                df = pd.read_excel(uploaded_file, sheet_name=sheet)
                df.columns = df.columns.str.strip()

                if col_score not in df.columns:
                    st.warning(f"⚠️ Column '{col_score}' not found in sheet '{sheet}'")
                    continue
                if col_name not in df.columns:
                    df[col_name] = '-'

                raw = df[col_score].dropna()
                if round_to_int:
                    scores = np.floor(raw + 0.5 + 1e-9).astype(int)
                else:
                    scores = raw.astype(float).round(6)

                for idx, s in scores.items():
                    name = df.loc[idx, col_name]
                    name = '-' if pd.isna(name) else str(name).strip()
                    records.append({
                        'room': room_label,
                        'no': idx + 1,
                        'name': name,
                        'score': s
                    })

            all_df = pd.DataFrame(records)

            if not all_df.empty:
                st.success("✅ File loaded and processed successfully!")
                
                # Tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    f"🥇 Top {top_n_room} Per Room", 
                    "🏆 Grade Top 50", 
                    "⚠️ Absent Students (Score 0)", 
                    "📋 All Data"
                ])

                # Helper function for student formatting
                def fmt_student(row, include_score=True):
                    txt = f"No. {row['no']:02d} {row['name']}"
                    if include_score:
                        txt += f" ({row['score']} pts)"
                    return txt

                # Tab 1: Top N per Room
                with tab1:
                    st.subheader(f"🥇 Top {top_n_room} per Classroom")
                    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                    for room in all_df['room'].unique():
                        room_df = all_df[all_df['room'] == room].copy()
                        room_df['room_rank'] = room_df['score'].rank(method='dense', ascending=False).astype(int)
                        room_top = room_df[room_df['room_rank'] <= top_n_room].sort_values(['room_rank', 'no'])
                        
                        with st.expander(f"📌 {room}", expanded=True):
                            for rank, grp in room_top.groupby('room_rank'):
                                medal = medals.get(rank, f"Rank {rank}:")
                                students = " / ".join([fmt_student(r, show_scores) for _, r in grp.iterrows()])
                                st.write(f"**{medal} {f'Rank {rank}' if rank in medals else ''}:** {students}")

                # Tab 2: Top 50 Whole Grade
                with tab2:
                    all_df['rank'] = all_df['score'].rank(method='min', ascending=False).astype(int)
                    top50 = all_df[all_df['rank'] <= 50].sort_values(['rank', 'room', 'no'])
                    cutoff = top50['score'].min()
                    
                    st.subheader(f"🏆 Top 50 of the Whole Grade (Cutoff ≥ {cutoff:g}, Total {len(top50)} students)")
                    
                    cols_to_show = ['rank', 'room', 'no', 'name']
                    rename_map = {
                        'rank': 'Rank',
                        'room': 'Room',
                        'no': 'No.',
                        'name': 'Name'
                    }
                    if show_scores:
                        cols_to_show.append('score')
                        rename_map['score'] = 'Score'
                        
                    st.dataframe(
                        top50[cols_to_show].rename(columns=rename_map), 
                        use_container_width=True, 
                        hide_index=True
                    )

                # Tab 3: Absent / Score 0
                with tab3:
                    zero_df = all_df[all_df['score'] == 0].sort_values(['room', 'no'])
                    st.subheader(f"⚠️️ Absent / Score 0 (Total {len(zero_df)} students)")
                    if zero_df.empty:
                        st.info("No students received a score of 0.")
                    else:
                        st.dataframe(
                            zero_df[['room', 'no', 'name']].rename(columns={
                                'room': 'Room',
                                'no': 'No.',
                                'name': 'Name'
                            }), 
                            use_container_width=True, 
                            hide_index=True
                        )

                # Tab 4: All Data
                with tab4:
                    st.subheader("📋 All Student Records")
                    all_cols = ['rank', 'room', 'no', 'name']
                    all_map = {
                        'rank': 'Grade Rank',
                        'room': 'Room',
                        'no': 'No.',
                        'name': 'Name'
                    }
                    if show_scores:
                        all_cols.append('score')
                        all_map['score'] = 'Score'
                        
                    st.dataframe(
                        all_df[all_cols].rename(columns=all_map), 
                        use_container_width=True, 
                        hide_index=True
                    )

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")