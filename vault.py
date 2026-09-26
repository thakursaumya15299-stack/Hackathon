import streamlit as st
import os
import shutil
import hashlib

# -----------------------------
# Configuration
# -----------------------------

nodes = ["Node1", "Node2", "Node3"]

REPLICATION_FACTOR = 3
# -----------------------------
# Create node folder
# -----------------------------
for node in nodes:
    os.makedirs(node, exist_ok=True)
# -----------------------------
# Helper Functions
# -----------------------------

def get_checksum(filename):
    with open(filename, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


def get_all_files():
    all_files = set()

    for node in nodes:
        if os.path.exists(node):
            for file in os.listdir(node):
                all_files.add(file)

    return sorted(all_files)


def upload_file(uploaded_file):
    filename = uploaded_file.name

    # Create node folders if they do not exist
    for node in nodes:
        os.makedirs(node, exist_ok=True)

    # Save original file temporarily
    with open(filename, "wb") as file:
        file.write(uploaded_file.getbuffer())

    # Create replicas
    for node in nodes[:REPLICATION_FACTOR]:
        shutil.copy(filename, f"{node}/{filename}")

    st.success(
        f"File '{filename}' uploaded with "
        f"{REPLICATION_FACTOR} replicas!"
    )


def check_integrity(filename):
    available_nodes = []

    for node in nodes:
        path = f"{node}/{filename}"

        if os.path.exists(path):
            available_nodes.append(node)

    if len(available_nodes) < 2:
        return None

    original_hash = get_checksum(
        f"{available_nodes[0]}/{filename}"
    )

    results = {}

    for node in available_nodes:
        current_hash = get_checksum(
            f"{node}/{filename}"
        )

        if current_hash == original_hash:
            results[node] = "OK"
        else:
            results[node] = "CORRUPTED"

    return results


def repair_file(filename):

    healthy_node = None

    # Find a healthy copy
    for node in nodes:
        path = f"{node}/{filename}"

        if os.path.exists(path):
            healthy_node = node
            break

    if healthy_node is None:
        return False, "No healthy copy found!"

    source_path = f"{healthy_node}/{filename}"
    source_hash = get_checksum(source_path)

    repaired = []

    for node in nodes[:REPLICATION_FACTOR]:

        # Create node folder if it does not exist
        os.makedirs(node, exist_ok=True)

        path = f"{node}/{filename}"

        # Missing file
        if not os.path.exists(path):

            shutil.copy(source_path, path)

            repaired.append(
                f"{node} was missing and repaired"
            )

        # Corrupted file
        else:

            current_hash = get_checksum(path)

            if current_hash != source_hash:

                shutil.copy(source_path, path)

                repaired.append(
                    f"{node} was corrupted and repaired"
                )

    return True, repaired


# -----------------------------
# Create Node Folders
# -----------------------------

for node in nodes:
    os.makedirs(node, exist_ok=True)


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="Vault",
    page_icon="🔐",
    layout="wide"
)


# -----------------------------
# Header
# -----------------------------

st.title("🔐 VAULT")
st.subheader("Fault-Tolerant Distributed Object Storage")

st.write(
    "Upload files, create replicas, detect corruption "
    "and automatically repair damaged or missing copies."
)


# -----------------------------
# Dashboard
# -----------------------------

st.markdown("## 📊 System Dashboard")

col1, col2, col3, col4 = st.columns(4)

# Total nodes
col1.metric(
    "Total Nodes",
    len(nodes)
)

# Active nodes
active_nodes = sum(
    1 for node in nodes
    if os.path.exists(node)
)

col2.metric(
    "Active Nodes",
    active_nodes
)

# Total stored files
total_files = len(get_all_files())

col3.metric(
    "Stored Files",
    total_files
)

# Replication factor
col4.metric(
    "Replication",
    REPLICATION_FACTOR
)


st.divider()


# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.title("⚡ Vault Controls")

option = st.sidebar.radio(
    "Choose an operation",
    [
        "📤 Upload File",
        "🟢 Node Status",
        "🔧 Repair File",
        "🔐 Integrity Check",
        "📦 Storage View"
    ]
)


# -----------------------------
# Upload
# -----------------------------

if option == "📤 Upload File":

    st.header("📤 Upload File")

    uploaded_file = st.file_uploader(
        "Choose a file"
    )

    if uploaded_file:

        st.info(
            f"Selected file: {uploaded_file.name}"
        )

        if st.button(
            "🚀 Upload & Replicate",
            use_container_width=True
        ):

            upload_file(uploaded_file)


# -----------------------------
# Node Status
# -----------------------------

elif option == "🟢 Node Status":

    st.header("🟢 Node Status")

    for node in nodes:

        if os.path.exists(node):

            st.success(
                f"🟢 {node} — UP"
            )

        else:

            st.error(
                f"🔴 {node} — DOWN"
            )


# -----------------------------
# Repair
# -----------------------------

elif option == "🔧 Repair File":

    st.header("🔧 Repair Missing / Corrupted File")

    files = get_all_files()

    if not files:

        st.warning(
            "No files are currently stored."
        )

    else:

        filename = st.selectbox(
            "Select a file",
            files
        )

        if st.button(
            "🛠️ Repair File",
            use_container_width=True
        ):

            success, result = repair_file(filename)

            if success:

                st.success(
                    "Repair process completed!"
                )

                if result:

                    for message in result:
                        st.write("✅", message)

                else:

                    st.info(
                        "No repair was required. "
                        "All replicas are healthy."
                    )

            else:

                st.error(result)


# -----------------------------
# Integrity Check
# -----------------------------

elif option == "🔐 Integrity Check":

    st.header("🔐 File Integrity Verification")

    files = get_all_files()

    if not files:

        st.warning(
            "No files are currently stored."
        )

    else:

        filename = st.selectbox(
            "Select a file",
            files
        )

        if st.button(
            "🔍 Check Integrity",
            use_container_width=True
        ):

            results = check_integrity(filename)

            if results is None:

                st.warning(
                    "Not enough copies available "
                    "for comparison."
                )

            else:

                for node, status in results.items():

                    if status == "OK":

                        st.success(
                            f"🟢 {node} — File is OK"
                        )

                    else:

                        st.error(
                            f"🔴 {node} — File is CORRUPTED"
                        )


# -----------------------------
# Storage View
# -----------------------------

elif option == "📦 Storage View":

    st.header("📦 Vault Storage")

    files = get_all_files()

    if not files:

        st.info(
            "No files stored in Vault."
        )

    else:

        for filename in files:

            st.subheader(
                f"📄 {filename}"
            )

            cols = st.columns(3)

            for i, node in enumerate(nodes):

                path = f"{node}/{filename}"

                if os.path.exists(path):

                    cols[i].success(
                        f"🟢 {node}\n\n"
                        "COPY AVAILABLE"
                    )

                else:

                    cols[i].error(
                        f"🔴 {node}\n\n"
                        "MISSING"
                    )
