(function () {
    "use strict";

    const runtime = window.stage1Runtime || {};
    if (!runtime.sipPassword || runtime.sipPassword.startsWith("__")) {
        document.documentElement.dataset.stage1ConfigurationError = "1";
        return;
    }

    const values = {
        profileUserID: "asterisk-pwa-stage1",
        profileName: "PWA Stage 1",
        wssServer: window.location.hostname,
        WebSocketPort: window.location.port || "443",
        ServerPath: "/flacmusic/asterisk-ws",
        SipDomain: "192.168.50.10",
        SipUsername: "1099",
        SipPassword: runtime.sipPassword,
        profileUser: "1099",
        VoiceMailSubscribe: "0",
        SubscribeToYourself: "0",
        ChatEngine: "SIMPLE",
        EnableVideoCalling: "0",
        EnableTextMessaging: "0",
        EnableTransfer: "0",
        EnableConference: "0",
        Notifications: "0",
        IceStunServerJson: "[]"
    };

    Object.entries(values).forEach(([key, value]) => localStorage.setItem(key, value));
})();
