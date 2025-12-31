import streamlit as st
import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Page config
st.set_page_config(page_title="Matchmaking Admin", page_icon="💘")
st.title("Admin: University Matchmaking 💘")

# DB Connection
DB_FILE = "matchmaking.db"

def load_users():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    return df

# Load Data
if st.button("Load/Refresh Users"):
    st.session_state.users_df = load_users()
    st.success(f"Loaded {len(st.session_state.users_df)} users.")

if 'users_df' in st.session_state and not st.session_state.users_df.empty:
    df = st.session_state.users_df
    st.subheader("Registered Users")
    st.dataframe(df)

    if st.button("Generate Matches"):
        with st.spinner("Generating embeddings and matching..."):
            # Combine looking_for and about_me for embedding
            df['text_for_matching'] = df['looking_for'] + " " + df['about_me']
            
            # Generate Embeddings
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(df['text_for_matching'].tolist())
            
            # Compute Cosine Similarity
            sim_matrix = cosine_similarity(embeddings)
            
            # Greedy Matching
            # Set diagonal to -1 to avoid self-matching
            np.fill_diagonal(sim_matrix, -1)
            
            users = df.to_dict('records')
            matched_indices = set()
            pairs = []
            
            # Matchmaking with Gender Preference
            for i in range(len(users)):
                if i in matched_indices:
                    continue
                    
                u1 = users[i]
                best_match_idx = -1
                best_score = -1
                
                for j in range(i + 1, len(users)):
                    if j in matched_indices:
                        continue
                        
                    u2 = users[j]
                    
                    # Mutual Gender Preference Check
                    # Does u1's preference match u2's gender AND does u2's preference match u1's gender?
                    gender_match = (u1['interested_in'] == u2['gender']) and (u2['interested_in'] == u1['gender'])
                    
                    if gender_match:
                        score = sim_matrix[i][j]
                        if score > best_score:
                            best_score = score
                            best_match_idx = j
                
                if best_match_idx != -1:
                    pairs.append({
                        'user1': users[i],
                        'user2': users[best_match_idx],
                        'score': best_score
                    })
                    matched_indices.add(i)
                    matched_indices.add(best_match_idx)
            
            # Display Matches
            st.divider()
            st.subheader("Generated Pairs (Gender-Filtered)")
            
            for p in pairs:
                score_display = f"{p['score']:.2f}"
                st.markdown(f"**{p['user1']['name']}** ❤️ **{p['user2']['name']}** (Score: {score_display})")
                
                with st.expander(f"Details for {p['user1']['name']} & {p['user2']['name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**{p['user1']['name']}** ({p['user1']['gender']})")
                        st.write(f"*WhatsApp:* {p['user1']['whatsapp']}")
                        st.write(f"*About:* {p['user1']['about_me']}")
                        st.write(f"*Looking For:* {p['user1']['looking_for']}")
                    with col2:
                        st.write(f"**{p['user2']['name']}** ({p['user2']['gender']})")
                        st.write(f"*WhatsApp:* {p['user2']['whatsapp']}")
                        st.write(f"*About:* {p['user2']['about_me']}")
                        st.write(f"*Looking For:* {p['user2']['looking_for']}")

            # Show unmatched users
            unmatched = [i for i in range(len(users)) if i not in matched_indices]
            if unmatched:
                st.warning("Unmatched Users (Odd number of participants or leftovers):")
                for i in unmatched:
                    st.write(f"- {users[i]['name']}")

else:
    st.info("Click 'Load/Refresh Users' to start.")
