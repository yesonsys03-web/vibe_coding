/**
 * Template 10 — Royal Purple
 */
const THEMES  = require('../core/colors');
const BASE    = require('./base_builder');
const THEME   = THEMES[10];
const build   = (parsed) => BASE.build(THEME, parsed);
module.exports = { build, THEME };
