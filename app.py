import io
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cycle Time & Work Item Age", page_icon="⏱️", layout="wide")

st.title("⏱️ Cycle Time & Work Item Age")
st.caption("Upload a Jira issue-history export (CSV or Excel). I’ll compute cycle time and work item age by issue.")

with st.sidebar:
    st.header("Settings")
    tz_name = st.selectbox(
        "Timezone",
        options=pytz.all_timezones,
        index=pytz.all_timezones.index("America/New_York") if "America/New_York" in pytz.all_timezones else 0,
        help="Used for 'today' when computing Work Item Age."
    )
    in_progress_aliases = st.text_input(
        "Treat these as 'In Progress' (comma-separated)",
        value="IN PROGRESS,IN-PROGRESS,IN_PROGRESS,INPROGRESS",
        help="Status [new] values that count as the start of work."
    )
    done_aliases = st.text_input(
        "Treat these as 'Done' (comma-separated)",
        value="DONE,CLOSED,RESOLVED",
        help="Status [new] values that count as completed."
    )
    st.markdown("---")
    st.write("Columns expected (case insensitive):")
    st.code("Key, Date of change, Status, Status [new]")

uploaded = st.file_uploader("Upload your file", type=["xlsx", "xls", "csv"])

def normalize_status(s):
    return s.strip().upper() if isinstance(s, str) else s

def coerce_datetime(s):
    try:
        return pd.to_datetime(s, utc=False, errors="coerce")
    except Exception:
        return pd.NaT

def compute_metrics(df_raw, tz_name, in_prog_set, done_set):
    # Flexible column matching (case-insensitive)
    cols = {c.lower(): c for c in df_raw.columns}
    required = ["key", "date of change", "status", "status [new]"]
    missing = [c for c in required if c not in cols]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df_raw.rename(columns={
        cols["key"]: "Key",
        cols["date of change"]: "Date of change",
        cols["status"]: "Status",
        cols["status [new]"]: "Status [new]"
    }).copy()

    df["Status"] = df["Status"].apply(normalize_status)
    df["Status [new]"] = df["Status [new]"].apply(normalize_status)
    df["Date of change"] = df["Date of change"].apply(coerce_datetime)

    df = df.dropna(subset=["Key", "Date of change"])

    in_prog = (
        df[df["Status [new]"].isin(in_prog_set)]
        .groupby("Key", as_index=False)["Date of change"]
        .min()
        .rename(columns={"Date of change": "In Progress Date"})
    )

    done = (
        df[df["Status [new]"].isin(done_set)]
        .groupby("Key", as_index=False)["Date of change"]
        .min()
        .rename(columns={"Date of change": "Done Date"})
    )

    results = pd.merge(in_prog, done, on="Key", how="outer")

    local_tz = pytz.timezone(tz_name)
    today_local = datetime.now(tz=local_tz).date()

    def row_days(r):
        ip = r.get("In Progress Date", pd.NaT)
        dn = r.get("Done Date", pd.NaT)
        if pd.notna(ip):
            ip_d = ip.date()
            if pd.notna(dn):
                dn_d = dn.date()
                return (dn_d - ip_d).days + 1
            else:
                return (today_local - ip_d).days + 1
        return None

    def row_type(r):
        return "Cycle Time" if pd.notna(r.get("Done Date", pd.NaT)) else (
            "Work Item Age" if pd.notna(r.get("In Progress Date", pd.NaT)) else None
        )

    results["Days"] = results.apply(row_days, axis=1)
    results["Metric Type"] = results.apply(row_type, axis=1)

    unique_statuses = pd.unique(
        pd.concat([df["Status"].dropna(), df["Status [new]"].dropna()])
    )
    unique_statuses = sorted([s for s in unique_statuses if isinstance(s, str)])

    results = results.sort_values(by=["Metric Type", "Key"], ascending=[True, True])
    return results, unique_statuses

if uploaded:
    try:
        if uploaded.name.lower().endswith(".csv"):
            raw = pd.read_csv(uploaded)
        else:
            raw = pd.read_excel(uploaded)

        in_prog_set = set([s.strip().upper() for s in in_progress_aliases.split(",") if s.strip()])
        done_set = set([s.strip().upper() for s in done_aliases.split(",") if s.strip()])

        results, statuses = compute_metrics(raw, tz_name, in_prog_set, done_set)

        st.subheader("Results")
        st.dataframe(results, use_container_width=True)

        # Prepare Excel bytes for download
        output = io.BytesIO()
        results.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="cycle_time_and_age.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.subheader("Unique Status Values Found")
        st.write(", ".join(statuses) if statuses else "—")

        with st.expander("Troubleshooting / Assumptions"):
            st.markdown(
                "- **Cycle Time** = First **Done** date − First **In Progress** date + 1 day.\n"
                "- **Work Item Age** (no Done) = Today (in selected timezone) − First **In Progress** date + 1 day.\n"
                "- We detect transitions using **Status [new]**.\n"
                "- If your team uses different words for *In Progress* or *Done*, add them in the sidebar.\n"
                "- Expected columns (case-insensitive): **Key**, **Date of change**, **Status**, **Status [new]**."
            )
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Upload a CSV or Excel export with issue-history to begin.")
