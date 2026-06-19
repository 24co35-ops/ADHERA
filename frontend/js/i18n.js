/**
 * i18n.js — Adhera internationalisation scaffolding.
 *
 * Usage:
 *   import { t } from './i18n.js';
 *   t('btn.taken')  // → "Taken"
 *
 * To add a locale, set window.ADHERA_LANG to an object with the same keys
 * as en.js before this module initialises. Missing keys fall back to 'en'.
 */

import { en } from './locales/en.js';

const LOCALE_MAP = { en };

/** Active locale strings (defaults to English). */
const _strings = Object.assign({}, en, window.ADHERA_LANG ?? {});

/**
 * Translate a dot-notation key.
 * Falls back to the English value, then the raw key if both are missing.
 * @param {string} key
 * @returns {string}
 */
export function t(key) {
    return _strings[key] ?? en[key] ?? key;
}

// Expose on window so Alpine.js x-bind expressions can call $t() or window.t()
window.t = t;
