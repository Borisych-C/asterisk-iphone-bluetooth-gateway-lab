#!/usr/bin/env node
"use strict";

const { WebSocket } = require("undici");
const http = require("http");

function getJson(url) {
    return new Promise((resolve, reject) => {
        http.get(url, (response) => {
            let body = "";
            response.setEncoding("utf8");
            response.on("data", (chunk) => { body += chunk; });
            response.on("end", () => {
                try { resolve(JSON.parse(body)); }
                catch (error) { reject(error); }
            });
        }).on("error", reject);
    });
}

async function main() {
    const pages = await getJson("http://127.0.0.1:9229/json");
    const page = pages.find((candidate) => candidate.type === "page" && candidate.url.includes("/phone-probe/"));
    if (!page) throw new Error("Stage 1 Chrome page not found");

    const ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
        ws.addEventListener("open", resolve, { once: true });
        ws.addEventListener("error", reject, { once: true });
    });

    function evaluate(id, expression) {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error("Chrome evaluation timed out")), 5000);
            const listener = (event) => {
                const message = JSON.parse(event.data.toString());
                if (message.id !== id) return;
                ws.removeEventListener("message", listener);
                clearTimeout(timeout);
                resolve(message.result.result.value);
            };
            ws.addEventListener("message", listener);
            ws.send(JSON.stringify({ id, method: "Runtime.evaluate", params: { expression, returnByValue: true } }));
        });
    }

    const action = process.argv[2];
    if (action === "dial-echo") {
        await evaluate(10, `DialByLine("audio", null, "600", "Stage 1 Echo"); "dial requested"`);
    } else if (action === "hangup") {
        await evaluate(11, `endSession(newLineNumber); "hangup requested"`);
    } else if (action) {
        throw new Error("Unknown action: " + action);
    }

    const expression = `(() => {
        const line = typeof FindLineByNumber === "function" && typeof newLineNumber !== "undefined" ? FindLineByNumber(newLineNumber) : null;
        const pc = line && line.SipSession && line.SipSession.sessionDescriptionHandler ? line.SipSession.sessionDescriptionHandler.peerConnection : null;
        const candidateLines = (description) => description && description.sdp ? description.sdp.split("\\r\\n").filter((line) => line.startsWith("c=") || line.startsWith("a=candidate:") || line.startsWith("m=audio")) : [];
        return JSON.stringify({
        url: location.href,
        title: document.title,
        readyState: document.readyState,
        configurationError: document.documentElement.dataset.stage1ConfigurationError || null,
        sipLibrary: typeof SIP,
        serviceWorkerControlled: Boolean(navigator.serviceWorker && navigator.serviceWorker.controller),
        phoneHtmlBytes: document.querySelector("#Phone") ? document.querySelector("#Phone").innerHTML.length : null,
        loadingVisible: document.querySelector(".loading") ? getComputedStyle(document.querySelector(".loading")).display : null,
        initUiType: typeof InitUi,
        userAgentType: typeof userAgent,
        userAgentPresent: typeof userAgent !== "undefined" && Boolean(userAgent),
        profileConfigured: Boolean(localStorage.getItem("profileUserID")),
        peerConnection: pc ? {
            connectionState: pc.connectionState,
            iceConnectionState: pc.iceConnectionState,
            localCandidates: candidateLines(pc.localDescription),
            remoteCandidates: candidateLines(pc.remoteDescription)
        } : null,
        probeEvents: JSON.parse(localStorage.getItem("asterisk-pwa-stage1-log") || "[]").slice(-20)
        });
    })()`;

    const result = await evaluate(1, expression);

    ws.close();
    process.stdout.write(JSON.stringify(JSON.parse(result), null, 2) + "\n");
}

main().catch((error) => {
    process.stderr.write(error.stack + "\n");
    process.exit(1);
});
