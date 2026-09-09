from flask import Flask, request, jsonify, render_template_string
import platform
import shutil
import socket
import subprocess
import re
from datetime import datetime

app = Flask(__name__)

# ==========================================================
# KNOWLEDGE BASE
# RAG SOURCE
# ==========================================================

KNOWLEDGE_BASE = [

    {
        "title": "Wi-Fi Connection",
        "keywords": [
            "wifi", "wi-fi", "wireless",
            "network", "internet",
            "connection", "connect"
        ],
        "answer": """
1. Check whether Wi-Fi is switched ON.
2. Disconnect and reconnect to the Wi-Fi network.
3. Restart your router.
4. Forget the Wi-Fi network and reconnect.
5. Restart your computer.
6. If other devices also cannot connect, the network/router may be the problem.
"""
    },

    {
        "title": "Slow Computer",
        "keywords": [
            "slow", "lag", "hang",
            "freeze", "performance",
            "computer slow", "pc slow"
        ],
        "answer": """
1. Close unnecessary applications.
2. Restart the computer.
3. Check available disk space.
4. Remove unnecessary startup applications.
5. Check whether too many programs are running.
6. Run a malware/security scan.
"""
    },

    {
        "title": "Password and Login",
        "keywords": [
            "password", "login",
            "signin", "sign in",
            "account", "locked",
            "forgot password"
        ],
        "answer": """
1. Check whether Caps Lock is enabled.
2. Verify your username.
3. Enter the correct password.
4. Use password reset if you forgot the password.
5. If the account is locked, contact the administrator.
"""
    },

    {
        "title": "Printer Problem",
        "keywords": [
            "printer", "printing",
            "print", "paper",
            "printer error"
        ],
        "answer": """
1. Check whether the printer is powered ON.
2. Check printer network/USB connection.
3. Make sure the correct printer is selected.
4. Check the printer queue.
5. Remove stuck print jobs.
6. Check paper and ink/toner.
7. Restart the printer.
"""
    },

    {
        "title": "Software/Application Error",
        "keywords": [
            "software", "application",
            "app", "program",
            "crash", "error",
            "not opening"
        ],
        "answer": """
1. Close and reopen the application.
2. Restart the computer.
3. Check whether the application is updated.
4. Check available disk space.
5. Run the application again.
6. Reinstall the application if the problem continues.
"""
    },

    {
        "title": "Internet Problem",
        "keywords": [
            "internet", "website",
            "browser", "online",
            "offline", "no internet"
        ],
        "answer": """
1. Check your network connection.
2. Restart the router.
3. Restart your computer.
4. Try opening another website.
5. Check DNS/network settings.
6. If all devices have the same issue, contact network support.
"""
    },

    {
        "title": "Storage Problem",
        "keywords": [
            "disk", "storage",
            "space", "drive",
            "full", "low storage"
        ],
        "answer": """
1. Check available disk space.
2. Delete unnecessary files.
3. Empty the recycle bin.
4. Remove temporary files.
5. Uninstall unused applications.
6. Keep sufficient free space on the system drive.
"""
    },

    {
        "title": "General IT Problem",
        "keywords": [
            "problem", "issue",
            "help", "not working",
            "troubleshoot"
        ],
        "answer": """
I could not identify a specific IT category.

Try these basic troubleshooting steps:

1. Restart the affected application.
2. Restart your computer.
3. Check your internet connection.
4. Check available disk space.
5. Note down any error message.
6. Create a support ticket if the issue continues.
"""
    }

]


# ==========================================================
# RAG ENGINE
# Lightweight Retrieval-Augmented Generation
# No external AI API required
# ==========================================================

def clean_words(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    return set(text.split())


def rag_search(query):

    query_words = clean_words(query)

    results = []

    for item in KNOWLEDGE_BASE:

        keyword_words = set()

        for keyword in item["keywords"]:
            keyword_words.update(
                clean_words(keyword)
            )

        matched = query_words.intersection(
            keyword_words
        )

        score = len(matched)

        if score > 0:

            results.append({
                "title": item["title"],
                "answer": item["answer"].strip(),
                "score": score,
                "matched": list(matched)
            })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:3]


# ==========================================================
# AGENT
# ==========================================================

def agent_understand(query):

    text = query.lower()

    if any(x in text for x in [
        "wifi",
        "wi-fi",
        "wireless",
        "network",
        "internet",
        "connection"
    ]):
        category = "Network Issue"

    elif any(x in text for x in [
        "slow",
        "lag",
        "hang",
        "freeze",
        "performance"
    ]):
        category = "Performance Issue"

    elif any(x in text for x in [
        "password",
        "login",
        "signin",
        "sign in",
        "account",
        "locked"
    ]):
        category = "Account Issue"

    elif any(x in text for x in [
        "printer",
        "printing",
        "print"
    ]):
        category = "Printer Issue"

    elif any(x in text for x in [
        "software",
        "application",
        "app",
        "program",
        "crash",
        "error"
    ]):
        category = "Software Issue"

    elif any(x in text for x in [
        "disk",
        "storage",
        "space",
        "drive"
    ]):
        category = "Storage Issue"

    else:
        category = "General IT Issue"

    return category


# ==========================================================
# TOOLS
# ==========================================================

def tool_network():

    try:

        socket.create_connection(
            ("8.8.8.8", 53),
            timeout=2
        )

        return {
            "name": "Network Diagnostic",
            "status": "success",
            "message":
                "Internet connectivity is available."
        }

    except:

        return {
            "name": "Network Diagnostic",
            "status": "warning",
            "message":
                "Internet connectivity could not be verified."
        }


def tool_dns():

    try:

        socket.gethostbyname(
            "google.com"
        )

        return {
            "name": "DNS Check",
            "status": "success",
            "message":
                "DNS resolution is working."
        }

    except:

        return {
            "name": "DNS Check",
            "status": "warning",
            "message":
                "DNS resolution failed."
        }


def tool_system():

    os_name = platform.system()

    version = platform.release()

    machine = platform.machine()

    processor = platform.processor()

    return {
        "name": "System Inspector",
        "status": "success",
        "message":
            f"{os_name} {version} | "
            f"{machine} | "
            f"{processor or 'Processor detected'}"
    }


def tool_disk():

    try:

        usage = shutil.disk_usage("/")

        total = usage.total / (1024 ** 3)

        free = usage.free / (1024 ** 3)

        percentage = (
            usage.free /
            usage.total
        ) * 100

        if percentage < 10:
            status = "warning"
        else:
            status = "success"

        return {
            "name": "Disk Analyzer",
            "status": status,
            "message":
                f"{free:.1f} GB free / "
                f"{total:.1f} GB total"
        }

    except:

        return {
            "name": "Disk Analyzer",
            "status": "warning",
            "message":
                "Disk information unavailable."
        }


# ==========================================================
# TICKET TOOL
# ==========================================================

tickets = []


def create_ticket(issue, category):

    ticket_number = (
        "HD-" +
        str(1001 + len(tickets))
    )

    ticket = {

        "id": ticket_number,

        "issue": issue,

        "category": category,

        "status": "Open",

        "created": datetime.now().strftime(
            "%d-%m-%Y %I:%M %p"
        )
    }

    tickets.append(ticket)

    return ticket


# ==========================================================
# AGENT TOOL SELECTION
# ==========================================================

def select_tools(category, query):

    text = query.lower()

    selected = []

    if category == "Network Issue":

        selected.append("network")

        selected.append("dns")

    elif category == "Performance Issue":

        selected.append("system")

        selected.append("disk")

    elif category == "Storage Issue":

        selected.append("disk")

    elif category == "Software Issue":

        selected.append("system")

        selected.append("disk")

    elif "computer" in text or "pc" in text:

        selected.append("system")

    return selected


def execute_tools(tool_list):

    results = []

    for tool in tool_list:

        if tool == "network":

            results.append(
                tool_network()
            )

        elif tool == "dns":

            results.append(
                tool_dns()
            )

        elif tool == "system":

            results.append(
                tool_system()
            )

        elif tool == "disk":

            results.append(
                tool_disk()
            )

    return results


# ==========================================================
# COMPLETE AI AGENT PIPELINE
# ==========================================================

def run_agent(query):

    # STEP 1
    category = agent_understand(
        query
    )

    # STEP 2
    retrieved = rag_search(
        query
    )

    # STEP 3
    selected_tools = select_tools(
        category,
        query
    )

    # STEP 4
    tool_results = execute_tools(
        selected_tools
    )

    # STEP 5
    if retrieved:

        best = retrieved[0]

        answer = (
            f"🔎 **Issue detected:** "
            f"{category}\n\n"

            f"📚 **Knowledge Retrieved:** "
            f"{best['title']}\n\n"

            f"🛠️ **Recommended Solution:**\n"
            f"{best['answer']}"
        )

    else:

        answer = (
            f"🔎 **Issue detected:** "
            f"{category}\n\n"

            "I couldn't find an exact knowledge "
            "match. Try restarting the affected "
            "system and create a support ticket "
            "if the problem continues."
        )

    return {

        "answer": answer,

        "category": category,

        "rag": retrieved,

        "tools": tool_results,

        "tool_count":
            len(tool_results)

    }


# ==========================================================
# UI
# ==========================================================

HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>NeuraDesk AI</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {

    font-family:
    "Segoe UI",
    Arial,
    sans-serif;

    background:
    radial-gradient(
        circle at 20% 10%,
        #172554,
        #020617 45%,
        #000814
    );

    color: #e5e7eb;

    min-height: 100vh;
}


/* ===============================
   LAYOUT
================================ */

.app {

    display: flex;

    min-height: 100vh;
}


/* ===============================
   SIDEBAR
================================ */

.sidebar {

    width: 255px;

    background:
    rgba(15,23,42,.88);

    border-right:
    1px solid rgba(148,163,184,.15);

    padding: 25px 18px;

}

.logo {

    display: flex;

    gap: 12px;

    align-items: center;

    margin-bottom: 40px;

}

.logoIcon {

    width: 48px;
    height: 48px;

    border-radius: 15px;

    display: flex;

    align-items: center;
    justify-content: center;

    font-size: 25px;

    background:
    linear-gradient(
        135deg,
        #38bdf8,
        #8b5cf6
    );

    box-shadow:
    0 0 35px
    rgba(56,189,248,.35);

}

.logo h2 {

    font-size: 20px;

}

.logo p {

    color: #94a3b8;

    font-size: 12px;

    margin-top: 3px;

}

.section {

    color: #64748b;

    font-size: 10px;

    letter-spacing: 2px;

    margin: 15px 8px;

}

.menu {

    padding: 14px;

    margin: 5px 0;

    border-radius: 13px;

    color: #94a3b8;

    cursor: pointer;

}

.menu.active {

    color: white;

    background:
    linear-gradient(
        90deg,
        rgba(56,189,248,.16),
        rgba(139,92,246,.12)
    );

    border:
    1px solid
    rgba(56,189,248,.18);

}

.online {

    position: absolute;

    bottom: 25px;

    width: 215px;

    padding: 14px;

    border-radius: 15px;

    background:
    rgba(34,197,94,.06);

    border:
    1px solid
    rgba(34,197,94,.15);

    font-size: 12px;

}

.dot {

    display: inline-block;

    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: #22c55e;

    box-shadow:
    0 0 10px #22c55e;

}


/* ===============================
   MAIN
================================ */

.main {

    flex: 1;

    padding: 25px;

}

.header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 22px;

}

.header h1 {

    font-size: 32px;

}

.header p {

    color: #94a3b8;

    margin-top: 5px;

}

.activeBadge {

    padding: 11px 18px;

    border-radius: 30px;

    color: #86efac;

    border:
    1px solid
    rgba(34,197,94,.25);

    background:
    rgba(34,197,94,.06);

}


/* ===============================
   GRID
================================ */

.grid {

    display: grid;

    grid-template-columns:
    minmax(0,1fr)
    350px;

    gap: 20px;

}


/* ===============================
   CHAT
================================ */

.chat {

    height:
    calc(100vh - 125px);

    min-height: 600px;

    display: flex;

    flex-direction: column;

    border-radius: 24px;

    overflow: hidden;

    background:
    rgba(15,23,42,.78);

    border:
    1px solid
    rgba(148,163,184,.13);

}

.chatTop {

    padding: 20px;

    display: flex;

    gap: 12px;

    align-items: center;

    border-bottom:
    1px solid
    rgba(148,163,184,.1);

}

.orb {

    width: 45px;
    height: 45px;

    border-radius: 50%;

    background:
    radial-gradient(
        circle,
        #38bdf8,
        #6366f1,
        #111827
    );

    box-shadow:
    0 0 30px
    rgba(56,189,248,.45);

}

.chatTop small {

    color: #64748b;

}

.messages {

    flex: 1;

    overflow-y: auto;

    padding: 22px;

}

.msg {

    max-width: 78%;

    padding: 15px 17px;

    margin-bottom: 15px;

    border-radius: 18px;

    white-space: pre-wrap;

    line-height: 1.6;

}

.bot {

    background:
    #182235;

    border:
    1px solid
    rgba(148,163,184,.1);

}

.user {

    margin-left: auto;

    background:
    linear-gradient(
        135deg,
        #2563eb,
        #7c3aed
    );

}


/* ===============================
   INPUT
================================ */

.inputArea {

    padding: 15px;

    border-top:
    1px solid
    rgba(148,163,184,.1);

}

.inputBox {

    display: flex;

    padding: 7px;

    border-radius: 16px;

    background:
    #020617;

    border:
    1px solid
    rgba(148,163,184,.16);

}

.inputBox input {

    flex: 1;

    background: transparent;

    border: none;

    outline: none;

    color: white;

    padding: 12px;

    font-size: 14px;

}

.send {

    width: 46px;
    height: 46px;

    border-radius: 13px;

    background:
    linear-gradient(
        135deg,
        #38bdf8,
        #6366f1
    );

    color: white;

    font-size: 20px;

    cursor: pointer;

}

.quick {

    display: flex;

    gap: 7px;

    margin-top: 9px;

    flex-wrap: wrap;

}

.quick button {

    padding: 8px 12px;

    border-radius: 20px;

    color: #94a3b8;

    background:
    #111827;

    border:
    1px solid
    rgba(148,163,184,.12);

    cursor: pointer;

}


/* ===============================
   RIGHT PANEL
================================ */

.right {

    display: flex;

    flex-direction: column;

    gap: 15px;

}

.card {

    background:
    rgba(15,23,42,.76);

    border:
    1px solid
    rgba(148,163,184,.12);

    border-radius: 20px;

    padding: 18px;

}

.card h3 {

    margin-bottom: 14px;

}

.pipeline {

    padding: 12px;

    border-radius: 13px;

    background:
    #121c2d;

    margin-bottom: 8px;

    border-left:
    3px solid #38bdf8;

}

.pipeline small {

    color: #64748b;

    display: block;

    margin-top: 4px;

}

.ragItem {

    padding: 11px;

    border-radius: 11px;

    background:
    #111827;

    margin-bottom: 8px;

}

.ragScore {

    font-size: 11px;

    color: #67e8f9;

    margin-top: 4px;

}

.tool {

    padding: 10px;

    border-radius: 10px;

    background:
    rgba(34,197,94,.06);

    border:
    1px solid
    rgba(34,197,94,.12);

    margin-bottom: 8px;

    font-size: 12px;

}

.ticket {

    width: 100%;

    padding: 13px;

    border: none;

    border-radius: 13px;

    background:
    linear-gradient(
        135deg,
        #7c3aed,
        #2563eb
    );

    color: white;

    cursor: pointer;

    font-size: 14px;

}


/* ===============================
   RESPONSIVE
================================ */

@media(max-width:900px) {

    .sidebar {
        display: none;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .right {
        display: none;
    }

    .main {
        padding: 12px;
    }

}

</style>

</head>


<body>


<div class="app">


<!-- SIDEBAR -->

<div class="sidebar">

    <div class="logo">

        <div class="logoIcon">
            ✦
        </div>

        <div>

            <h2>NeuraDesk</h2>

            <p>
                AI IT Operations
            </p>

        </div>

    </div>


    <div class="section">
        WORKSPACE
    </div>


    <div class="menu active">
        ◈ &nbsp; AI Helpdesk
    </div>

    <div class="menu">
        ◉ &nbsp; Diagnostics
    </div>

    <div class="menu">
        ▣ &nbsp; Knowledge Base
    </div>

    <div class="menu">
        ◫ &nbsp; Support Tickets
    </div>


    <div class="online">

        <span class="dot"></span>

        &nbsp; AI Agent Online

        <br>

        <small style="color:#64748b">
            Agent • RAG • Tools
        </small>

    </div>

</div>



<!-- MAIN -->

<div class="main">


    <div class="header">

        <div>

            <h1>
                IT Helpdesk AI Agent
            </h1>

            <p>
                Intelligent troubleshooting &
                automated diagnostics
            </p>

        </div>


        <div class="activeBadge">

            ● AGENT ACTIVE

        </div>

    </div>



    <div class="grid">


        <!-- CHAT -->

        <div class="chat">


            <div class="chatTop">

                <div class="orb"></div>

                <div>

                    <b>
                        NeuraDesk Agent
                    </b>

                    <small>
                        <br>
                        Agent • RAG • Tools
                    </small>

                </div>

            </div>



            <div
                class="messages"
                id="messages"
            >

                <div class="msg bot">

                    👋 Hello! I'm NeuraDesk.

                    I am your AI IT Support Agent.

                    Describe your IT problem and I will:

                    🔎 Understand the issue
                    📚 Search the knowledge base
                    🛠 Run diagnostic tools
                    💡 Give troubleshooting steps
                    🎫 Create a support ticket

                </div>

            </div>



            <div class="inputArea">


                <div class="inputBox">

                    <input
                        id="input"
                        placeholder="Example: My Wi-Fi is not working..."
                        autocomplete="off"
                    >

                    <button
                        class="send"
                        onclick="sendMessage()"
                    >
                        ➜
                    </button>

                </div>


                <div class="quick">

                    <button
                    onclick="askQuick('My Wi-Fi is not connecting')">
                        📶 Wi-Fi
                    </button>

                    <button
                    onclick="askQuick('My computer is very slow')">
                        🐌 Slow PC
                    </button>

                    <button
                    onclick="askQuick('I forgot my password and cannot login')">
                        🔐 Login
                    </button>

                    <button
                    onclick="askQuick('My printer is not printing')">
                        🖨 Printer
                    </button>

                </div>

            </div>


        </div>



        <!-- RIGHT -->

        <div class="right">


            <div class="card">

                <h3>
                    ⚡ Agent Pipeline
                </h3>


                <div class="pipeline">

                    <b>
                        01 — Understand
                    </b>

                    <small>
                        Analyze user issue
                    </small>

                </div>


                <div class="pipeline">

                    <b>
                        02 — RAG Retrieval
                    </b>

                    <small>
                        Retrieve relevant knowledge
                    </small>

                </div>


                <div class="pipeline">

                    <b>
                        03 — Tool Selection
                    </b>

                    <small>
                        Decide required diagnostics
                    </small>

                </div>


                <div class="pipeline">

                    <b>
                        04 — Action
                    </b>

                    <small>
                        Execute tools
                    </small>

                </div>

            </div>



            <div class="card">

                <h3>
                    📚 Retrieved Knowledge
                </h3>

                <div id="rag">

                    <small style="color:#64748b">
                        Waiting for query...
                    </small>

                </div>

            </div>



            <div class="card">

                <h3>
                    🛠 Live Tools
                </h3>

                <div id="tools">

                    <small style="color:#64748b">
                        Waiting for agent...
                    </small>

                </div>

            </div>



            <div class="card">

                <h3>
                    🎫 Support
                </h3>

                <button
                    class="ticket"
                    onclick="createTicket()"
                >

                    + Create Support Ticket

                </button>

            </div>


        </div>


    </div>

</div>

</div>



<script>


let lastIssue = "";


// =================================================
// ADD MESSAGE
// =================================================

function addMessage(text, type) {

    const box =
        document.getElementById(
            "messages"
        );

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "msg " + type;

    div.innerText = text;

    box.appendChild(div);

    box.scrollTop =
        box.scrollHeight;

}


// =================================================
// QUICK QUESTIONS
// =================================================

function askQuick(text) {

    document.getElementById(
        "input"
    ).value = text;

    sendMessage();

}


// =================================================
// SEND MESSAGE
// =================================================

async function sendMessage() {

    const input =
        document.getElementById(
            "input"
        );

    const query =
        input.value.trim();

    if (!query) {

        return;

    }


    lastIssue = query;


    addMessage(
        query,
        "user"
    );


    input.value = "";


    addMessage(
        "🧠 Agent is analyzing your issue...",
        "bot"
    );


    try {

        const response =
            await fetch(
                "/ask",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        query: query
                    })

                }
            );


        const data =
            await response.json();


        const messages =
            document.getElementById(
                "messages"
            );


        messages.lastElementChild.remove();


        addMessage(
            data.answer,
            "bot"
        );


        // ==============================
        // RAG RESULTS
        // ==============================

        const rag =
            document.getElementById(
                "rag"
            );


        if (data.rag.length > 0) {

            rag.innerHTML =
                data.rag.map(
                    item => `

                    <div class="ragItem">

                        <b>
                            ${item.title}
                        </b>

                        <div class="ragScore">
                            Match score:
                            ${item.score}
                        </div>

                    </div>

                    `
                ).join("");

        } else {

            rag.innerHTML =
                "<small>No matching knowledge found.</small>";

        }


        // ==============================
        // TOOLS
        // ==============================

        const tools =
            document.getElementById(
                "tools"
            );


        if (data.tools.length > 0) {

            tools.innerHTML =
                data.tools.map(
                    item => `

                    <div class="tool">

                        <b>
                            ${item.name}
                        </b>

                        <br>

                        ${item.message}

                    </div>

                    `
                ).join("");

        } else {

            tools.innerHTML =
                "<small>No diagnostic tools required.</small>";

        }


    }

    catch(error) {

        const messages =
            document.getElementById(
                "messages"
            );

        messages.lastElementChild.remove();


        addMessage(
            "❌ Cannot connect to the AI backend. Make sure app.py is running.",
            "bot"
        );

        console.error(error);

    }

}


// =================================================
// ENTER KEY
// =================================================

document.getElementById(
    "input"
).addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter"
        ) {

            sendMessage();

        }

    }
);


// =================================================
// CREATE TICKET
// =================================================

async function createTicket() {

    if (!lastIssue) {

        alert(
            "First describe your IT problem."
        );

        return;

    }


    try {

        const response =
            await fetch(
                "/ticket",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        issue: lastIssue
                    })

                }
            );


        const data =
            await response.json();


        addMessage(
            "🎫 " +
            data.message +
            "\\n\\nTicket ID: " +
            data.ticket.id +
            "\\nStatus: " +
            data.ticket.status,
            "bot"
        );

    }

    catch(error) {

        alert(
            "Ticket creation failed."
        );

    }

}

</script>


</body>

</html>

"""


# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def home():

    return render_template_string(
        HTML
    )


@app.route(
    "/ask",
    methods=["POST"]
)
def ask():

    data = request.get_json()

    query = data.get(
        "query",
        ""
    ).strip()


    if not query:

        return jsonify({

            "answer":
                "Please describe your IT problem.",

            "category":
                "Unknown",

            "rag": [],

            "tools": []

        })
    result = run_agent(query)
    return jsonify(result)


@app.route(
    "/ticket",
    methods=["POST"]
)
def ticket():

    data = request.get_json()

    issue = data.get(
        "issue",
        "Unknown issue"
    )

    category =agent_understand(issue)
    ticket =  create_ticket(
                issue,
                category
            )


    return jsonify({

        "message":
            f"Support ticket {ticket['id']} created successfully!",

        "ticket":
            ticket

    })


@app.route("/tickets")
def get_tickets():

    return jsonify(
        tickets
    )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("       NEURADESK AI HELPDESK")
    print("========================================")
    print("Agent       : ACTIVE")
    print("RAG         : ACTIVE")
    print("Tools       : ACTIVE")
    print("Ticketing   : ACTIVE")
    print("Database    : NOT REQUIRED")
    print("LLM API     : NOT REQUIRED")
    print("========================================")
    print("Open:")
    print("http://127.0.0.1:5000")
    print("========================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
