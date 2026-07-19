(function (root, factory) {
    const api = factory();
    if (typeof module === "object" && module.exports) module.exports = api;
    root.EagleBridgeAuthLogic = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    function token(value) {
        return typeof value === "string" ? value : "";
    }

    function unauthorizedAction(requestToken, latestToken) {
        const requested = token(requestToken);
        const latest = token(latestToken);
        if (latest && latest !== requested) return "retry-latest";
        if (requested && latest === requested) return "clear-rejected";
        return "recover";
    }

    function createStateUpdateQueue(readState, writeState) {
        if (typeof readState !== "function" || typeof writeState !== "function") {
            throw new TypeError("State update queue requires read and write functions");
        }
        let tail = Promise.resolve();
        return function updateState(changes) {
            const operation = tail.then(async () => {
                const current = await readState();
                const patch = typeof changes === "function" ? await changes(current) : changes;
                const next = { ...current, ...(patch && typeof patch === "object" ? patch : {}) };
                await writeState(next);
                return next;
            });
            tail = operation.then(() => undefined, () => undefined);
            return operation;
        };
    }

    return { unauthorizedAction, createStateUpdateQueue };
});
