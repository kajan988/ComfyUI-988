/**
 * Model refresh API client for LM Studio 988.
 * @module model_refresh
 */

/**
 * Fetch the updated model list from the LM Studio server.
 * @param {object} api - ComfyUI API module (imported from "/scripts/api.js")
 * @returns {Promise<object>} JSON response with { success, message, models }
 */
export async function refreshModelList(api) {
    const resp = await api.fetchApi("/988/lm_studio/refresh_models", {
        method: "POST",
    });
    return resp.json();
}