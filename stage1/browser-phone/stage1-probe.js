(function () {
    "use strict";

    const storageKey = "probeLog";
    const maxEntries = 600;
    let activeSession = null;
    let statsTimer = null;
    let panel = null;
    let output = null;

    function readLog() {
        try {
            return JSON.parse(localStorage.getItem(storageKey) || "[]");
        } catch (_) {
            return [];
        }
    }

    function writeLog(entries) {
        localStorage.setItem(storageKey, JSON.stringify(entries.slice(-maxEntries)));
    }

    function simplify(value) {
        if (value === undefined || value === null) return value;
        if (["string", "number", "boolean"].includes(typeof value)) return value;
        try {
            return JSON.parse(JSON.stringify(value));
        } catch (_) {
            return String(value);
        }
    }

    function log(event, details) {
        const entry = {
            at: new Date().toISOString(),
            monotonicMs: Math.round(performance.now()),
            event,
            visibility: document.visibilityState,
            online: navigator.onLine
        };
        if (details !== undefined) entry.details = simplify(details);
        const entries = readLog();
        entries.push(entry);
        writeLog(entries);
        console.log("[Stage1Probe]", entry);
        render();
    }

    async function sampleStats() {
        const pc = activeSession && activeSession.sessionDescriptionHandler &&
            activeSession.sessionDescriptionHandler.peerConnection;
        if (!pc || typeof pc.getStats !== "function") return;

        try {
            const media = [];
            const stats = await pc.getStats();
            stats.forEach((report) => {
                if ((report.type === "inbound-rtp" || report.type === "outbound-rtp") &&
                    (report.kind === "audio" || report.mediaType === "audio")) {
                    media.push({
                        direction: report.type,
                        bytes: report.bytesReceived ?? report.bytesSent ?? null,
                        packets: report.packetsReceived ?? report.packetsSent ?? null,
                        packetsLost: report.packetsLost ?? null,
                        jitter: report.jitter ?? null
                    });
                }
            });
            log("webrtc.stats", { connectionState: pc.connectionState, media });
        } catch (error) {
            log("webrtc.stats_error", { error: String(error) });
        }
    }

    function setSession(session, event) {
        if (session) activeSession = session;
        log(event || "sip.session", { state: session && session.state ? String(session.state) : null });
        if (!statsTimer) statsTimer = window.setInterval(sampleStats, 5000);
        window.setTimeout(sampleStats, 500);
    }

    function endSession(session) {
        log("sip.terminated", { state: session && session.state ? String(session.state) : null });
        activeSession = null;
        if (statsTimer) window.clearInterval(statsTimer);
        statsTimer = null;
    }

    function userAgentCreated(ua) {
        log("sip.user_agent_created");
        if (ua && ua.transport && ua.transport.stateChange) {
            ua.transport.stateChange.addListener((state) => log("sip.transport_state", { state: String(state) }));
        }
    }

    function formatLog() {
        return readLog().map((entry) => JSON.stringify(entry)).join("\n");
    }

    function render() {
        if (output) output.textContent = formatLog() || "No events yet.";
    }

    function createPanel() {
        const button = document.createElement("button");
        button.textContent = "Stage 1 log";
        button.setAttribute("aria-label", "Open Stage 1 diagnostic log");
        Object.assign(button.style, {
            position: "fixed", right: "10px", bottom: "10px", zIndex: "2147483647",
            padding: "9px 12px", border: "0", borderRadius: "18px",
            background: "#174ea6", color: "white", fontWeight: "600"
        });

        panel = document.createElement("div");
        Object.assign(panel.style, {
            display: "none", position: "fixed", inset: "8px", zIndex: "2147483647",
            background: "#fff", color: "#111", border: "2px solid #174ea6",
            borderRadius: "10px", padding: "10px", boxSizing: "border-box"
        });

        const toolbar = document.createElement("div");
        toolbar.style.marginBottom = "8px";
        [
            ["Close", () => { panel.style.display = "none"; }],
            ["Copy", async () => {
                try { await navigator.clipboard.writeText(formatLog()); log("ui.log_copied"); }
                catch (error) { log("ui.log_copy_failed", { error: String(error) }); }
            }],
            ["Sample now", sampleStats],
            ["Clear", () => { localStorage.removeItem(storageKey); log("ui.log_cleared"); }]
        ].forEach(([label, action]) => {
            const control = document.createElement("button");
            control.textContent = label;
            control.style.marginRight = "6px";
            control.addEventListener("click", action);
            toolbar.appendChild(control);
        });

        output = document.createElement("pre");
        Object.assign(output.style, {
            margin: "0", height: "calc(100% - 42px)", overflow: "auto",
            whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: "10px"
        });
        panel.append(toolbar, output);
        button.addEventListener("click", () => { render(); panel.style.display = "block"; });
        document.body.append(button, panel);
        render();
    }

    document.addEventListener("visibilitychange", () => {
        log("lifecycle.visibilitychange");
        sampleStats();
    });

    ["pagehide", "pageshow", "online", "offline", "freeze", "resume"]
        .forEach((event) => window.addEventListener(event, (detail) => {
            log("lifecycle." + event, event === "pagehide" || event === "pageshow" ? { persisted: detail.persisted } : undefined);
            if (event === "pageshow") sampleStats();
        }));

    window.addEventListener("load", () => {
        createPanel();
        if (document.documentElement.dataset.stage1ConfigurationError === "1") {
            log("configuration.error", { message: "stage1-runtime.js was not provisioned" });
            window.alert("Stage 1 is not provisioned: missing SIP runtime configuration.");
        } else {
            log("lifecycle.loaded", { userAgent: navigator.userAgent, standalone: navigator.standalone === true });
        }
    });

    window.Stage1Probe = { log, setSession, endSession, userAgentCreated, sampleStats };
})();
