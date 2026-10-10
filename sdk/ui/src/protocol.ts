/** postMessage protocol between the admin panel shell and a module UI in its iframe. */

/** iframe -> shell: the page loaded; send a token. */
export const READY = "h4h:ready";
/** iframe -> shell: the token is about to expire or was rejected; send a fresh one. */
export const TOKEN_REQUEST = "h4h:token-request";
/** shell -> iframe: `{ type, token }`, an admin token addressed to this module. */
export const TOKEN = "h4h:token";
