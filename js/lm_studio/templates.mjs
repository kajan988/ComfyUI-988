/**
 * Template refresh API client for LM Studio 988.
 * @module templates
 */

/**
 * Fetch the current system message templates from the server.
 * @param {object} api - ComfyUI API module (imported from "/scripts/api.js")
 * @returns {Promise<object>} JSON response with { success, templates }
 */
export async function refreshTemplateDropdown(api) {
    const resp = await api.fetchApi("/988/lm_studio/refresh_templates", {
        method: "POST",
    });
    return resp.json();
}