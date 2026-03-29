import pandas as pd
import streamlit as st
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))
from app.services.approval_service import load_approvals, update_approval_status

st.set_page_config(page_title="AI Email Agent Approvals", layout="wide")
st.title("AI Email Agent - Approval Dashboard")

approvals = load_approvals()
pending = [item for item in approvals if item.get("status") == "pending"]

if not pending:
    st.success("No pending approvals.")
    st.stop()

rows = []
for item in pending:
    rows.append(
        {
            "approval_id": item.get("approval_id", ""),
            "to_email": item.get("to_email", ""),
            "proposed_action": item.get("proposed_action", ""),
            "proposed_purpose": item.get("proposed_purpose", ""),
            "status": item.get("status", ""),
        }
    )

df = pd.DataFrame(rows)

st.subheader("Pending approvals")
st.dataframe(df, use_container_width=True)

approval_ids = [item["approval_id"] for item in pending]
selected_id = st.selectbox("Select approval", approval_ids)

selected_item = next(item for item in pending if item["approval_id"] == selected_id)

st.subheader("Details")
st.write("**To:**", selected_item.get("to_email", ""))
st.write("**Action:**", selected_item.get("proposed_action", ""))
st.write("**Purpose:**", selected_item.get("proposed_purpose", ""))

st.write("**Draft message:**")
st.text_area("Draft", value=selected_item.get("proposed_message", ""), height=220, disabled=True)

st.write("**Original input:**")
st.text_area("Original email", value=selected_item.get("input_text", ""), height=220, disabled=True)

st.write("**Reasoning result:**")
st.json(selected_item.get("reasoning_result", {}))

col1, col2 = st.columns(2)

with col1:
    if st.button("Approve", use_container_width=True):
        update_approval_status(selected_id, "approved")
        st.success(f"{selected_id} approved")
        st.rerun()

with col2:
    if st.button("Reject", use_container_width=True):
        update_approval_status(selected_id, "rejected")
        st.warning(f"{selected_id} rejected")
        st.rerun()