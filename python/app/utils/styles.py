import streamlit as st

# Custom side-by-side ombre badges
# -- original function from Google AI; modified to expect a list
def create_ombre_badge(list: list, color_start="#5de488", color_end="#b37eff"):

    badge_html = ""
    for item in list:
        badge_html += f"""
        <div style="
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 12px;
            background: linear-gradient(90deg, {color_start}, {color_end});
            color: #0d1116;
            font-weight: 500;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            {item}
        </div> &nbsp;
        """
    st.markdown(badge_html, unsafe_allow_html=True)

