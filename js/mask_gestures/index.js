import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

/*
 * Mask Editor 988 — configurable brush-size gesture.
 *
 * While the Mask Editor is open, a user-chosen modifier + mouse button is
 * rewritten into the editor's own Alt+Right-button brush adjust, so the
 * built-in size/hardness gesture runs without touching its internals.
 */

const SETTINGS = {
    enabled: "988.MaskEditor.Gesture.Enabled",
    modifier: "988.MaskEditor.Gesture.Modifier",
    button: "988.MaskEditor.Gesture.Button",
};

const CATEGORY = ["🦇988", "Mask Editor", "Brush Gesture"];
const MODS = ["ctrl", "alt", "shift", "meta"];
const BUTTONS = { left: 0, middle: 1, right: 2 };

const config = { enabled: true, modifiers: new Set(["ctrl"]), button: 0 };

function parseModifiers(value) {
    const mods = new Set();
    for (const part of String(value ?? "").toLowerCase().split("+")) {
        if (MODS.includes(part)) mods.add(part);
    }
    return mods;
}

function applyConfig(enabled, modifier, button) {
    config.enabled = Boolean(enabled);
    config.modifiers = parseModifiers(modifier);
    config.button = BUTTONS[button] ?? 0;
}

function matchesTrigger(event) {
    if (!config.enabled || event.button !== config.button) return false;
    for (const mod of MODS) {
        if (config.modifiers.has(mod) !== event[`${mod}Key`]) return false;
    }
    return true;
}

async function readSetting(id, fallback) {
    try {
        const value = await api.getSetting(id);
        if (value !== undefined && value !== null && value !== "") return value;
    } catch (e) {
        // Not stored yet (first run) — fall back to the default.
    }
    return fallback;
}

async function loadConfig() {
    const [enabled, modifier, button] = await Promise.all([
        readSetting(SETTINGS.enabled, true),
        readSetting(SETTINGS.modifier, "ctrl"),
        readSetting(SETTINGS.button, "left"),
    ]);
    applyConfig(enabled, modifier, button);
}

function installGesture() {
    const activePointers = new Map();
    const synthetic = new WeakSet();

    function dispatch(target, source, type, button, buttons) {
        const event = new PointerEvent(type, {
            bubbles: true,
            cancelable: true,
            composed: true,
            pointerId: source.pointerId,
            pointerType: "mouse",
            isPrimary: source.isPrimary,
            clientX: source.clientX,
            clientY: source.clientY,
            screenX: source.screenX,
            screenY: source.screenY,
            button,
            buttons,
            altKey: true,
        });
        synthetic.add(event);
        target.dispatchEvent(event);
    }

    document.addEventListener(
        "pointerdown",
        (event) => {
            if (synthetic.has(event) || event.pointerType !== "mouse") return;
            if (!matchesTrigger(event)) return;

            const zone = event.target.closest?.('[data-testid="pointer-zone"]');
            if (!zone) return;

            // Keep the trigger from reaching the editor as a plain draw/pan.
            event.preventDefault();
            event.stopPropagation();

            activePointers.set(event.pointerId, { zone, last: event });
            dispatch(zone, event, "pointerdown", 2, 2);
        },
        true,
    );

    document.addEventListener(
        "pointermove",
        (event) => {
            if (synthetic.has(event)) return;

            const active = activePointers.get(event.pointerId);
            if (!active) return;

            event.preventDefault();
            event.stopPropagation();

            active.last = event;
            dispatch(active.zone, event, "pointermove", -1, 2);
        },
        true,
    );

    for (const type of ["pointerup", "pointercancel"]) {
        document.addEventListener(
            type,
            (event) => {
                if (synthetic.has(event)) return;

                const active = activePointers.get(event.pointerId);
                if (!active) return;

                event.preventDefault();
                event.stopPropagation();

                activePointers.delete(event.pointerId);
                dispatch(active.zone, event, type, 2, 0);
            },
            true,
        );
    }

    // A button released outside the window can leave the editor stuck in its
    // brush-adjust state; the editor only settles on pointerup, so replay it.
    window.addEventListener("blur", () => {
        for (const [, active] of activePointers) {
            dispatch(active.zone, active.last, "pointerup", 2, 0);
        }
        activePointers.clear();
    });
}

app.registerExtension({
    name: "988.MaskEditorGestures",

    settings: [
        {
            id: SETTINGS.enabled,
            name: "Enable mask-editor brush gesture",
            type: "boolean",
            defaultValue: true,
            category: CATEGORY,
            tooltip:
                "Rewrite a modifier + mouse button in the Mask Editor into the editor's " +
                "own Alt+Right-button brush size/hardness adjust.",
            onChange: (value) => {
                config.enabled = Boolean(value);
            },
        },
        {
            id: SETTINGS.modifier,
            name: "Brush gesture modifier",
            type: "combo",
            options: [
                { text: "None", value: "none" },
                { text: "Ctrl", value: "ctrl" },
                { text: "Alt", value: "alt" },
                { text: "Shift", value: "shift" },
                { text: "Cmd/Meta", value: "meta" },
                { text: "Ctrl+Shift", value: "ctrl+shift" },
                { text: "Ctrl+Alt", value: "ctrl+alt" },
                { text: "Ctrl+Cmd", value: "ctrl+meta" },
                { text: "Alt+Shift", value: "alt+shift" },
                { text: "Alt+Cmd", value: "alt+meta" },
                { text: "Shift+Cmd", value: "shift+meta" },
            ],
            defaultValue: "ctrl",
            category: CATEGORY,
            tooltip:
                "Modifier held while pressing the mouse button. The trigger matches the " +
                "exact modifier set, so Ctrl does not fire for Ctrl+Shift.",
            onChange: (value) => {
                config.modifiers = parseModifiers(value);
            },
        },
        {
            id: SETTINGS.button,
            name: "Brush gesture mouse button",
            type: "combo",
            options: [
                { text: "Left", value: "left" },
                { text: "Middle", value: "middle" },
                { text: "Right", value: "right" },
            ],
            defaultValue: "left",
            category: CATEGORY,
            tooltip:
                "Mouse button that starts the gesture. Left/Right normally draw and Middle " +
                "pans, so avoid None+Left or Right unless you want to override those.",
            onChange: (value) => {
                config.button = BUTTONS[value] ?? 0;
            },
        },
    ],

    async setup() {
        await loadConfig();
        installGesture();
    },
});