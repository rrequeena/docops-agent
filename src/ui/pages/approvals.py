"""
Streamlit page for approval requests.
"""
import streamlit as st
from datetime import datetime


def render_approvals_page():
    """Render the approval interface page."""
    st.header("Approval Requests")

    # Pending approvals summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pending", "3", delta=-1)
    with col2:
        st.metric("Approved Today", "5")
    with col3:
        st.metric("Rejected Today", "1")

    st.divider()

    # Approval requests
    st.subheader("Pending Approvals")

    approval_requests = [
        {
            "id": "apr_001",
            "type": "high_value_invoice",
            "document": "contract_cloud_001.pdf",
            "vendor": "CloudServices LLC",
            "requested_by": "System",
            "requested_at": "2026-02-13 14:30",
            "amount": 15000.00,
            "description": "Annual cloud services contract renewal",
            "risk": "medium",
            "details": {
                "contract_term": "12 months",
                "payment_schedule": "Monthly",
                "previous_vendor": "OldCloud Inc"
            }
        },
        {
            "id": "apr_002",
            "type": "anomaly_review",
            "document": "invoice_acme_002.pdf",
            "vendor": "Acme Corp",
            "requested_by": "Analyst Agent",
            "requested_at": "2026-02-13 10:15",
            "amount": 2450.00,
            "description": "Price spike detected - 67% above vendor average",
            "risk": "high",
            "details": {
                "current_invoice": "$2,450.00",
                "vendor_average": "$1,465.00",
                "threshold": "50%"
            }
        },
        {
            "id": "apr_003",
            "type": "duplicate_charge",
            "document": "invoice_techsup_001.pdf",
            "vendor": "TechSupply Inc",
            "requested_by": "Anomaly Detection",
            "requested_at": "2026-02-12 16:45",
            "amount": 1500.00,
            "description": "Potential duplicate charges from same vendor on same day",
            "risk": "critical",
            "details": {
                "invoice_1": "INV-2026-0089",
                "invoice_2": "INV-2026-0090",
                "same_items": True
            }
        },
    ]

    for req in approval_requests:
        risk_color = {
            "critical": "red",
            "high": "orange",
            "medium": "yellow",
            "low": "green"
        }.get(req["risk"], "gray")

        with st.container(border=True):
            col_left, col_right = st.columns([4, 1])

            with col_left:
                st.markdown(f"**{req['type'].replace('_', ' ').title()}**")
                st.write(f"**Vendor:** {req['vendor']}")
                st.write(f"**Description:** {req['description']}")
                st.write(f"**Requested by:** {req['requested_by']} at {req['requested_at']}")
                st.write(f"**Amount:** ${req['amount']:,.2f}")

                with st.expander("View Details"):
                    for key, value in req["details"].items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")

            with col_right:
                st.markdown(f"<span style='color:{risk_color}'>●</span> {req['risk'].upper()}", unsafe_allow_html=True)
                st.write("")

                if st.button("Approve", key=f"approve_{req['id']}", type="primary"):
                    st.success(f"Approved {req['id']}")

                if st.button("Reject", key=f"reject_{req['id']}"):
                    st.error(f"Rejected {req['id']}")

                if st.button("Request Info", key=f"info_{req['id']}"):
                    st.info("Information request sent")

    st.divider()

    # Approval history
    st.subheader("Recent Approval History")

    history = [
        {"id": "apr_000", "type": "high_value_invoice", "vendor": "DataCorp", "status": "approved", "decided_by": "John D.", "decided_at": "2026-02-11 11:30", "amount": 8500.00},
        {"id": "apr_000", "type": "anomaly_review", "vendor": "SupplyCo", "status": "approved", "decided_by": "Jane S.", "decided_at": "2026-02-11 09:15", "amount": 3200.00},
        {"id": "apr_000", "type": "contract_renewal", "vendor": "SecureIT", "status": "rejected", "decided_by": "John D.", "decided_at": "2026-02-10 14:20", "amount": 12000.00},
    ]

    for h in history:
        status_icon = "✅" if h["status"] == "approved" else "❌"
        st.write(f"{status_icon} **{h['type'].replace('_', ' ').title()}** - {h['vendor']} - ${h['amount']:,.2f} - {h['decided_by']} at {h['decided_at']}")


__all__ = ["render_approvals_page"]
