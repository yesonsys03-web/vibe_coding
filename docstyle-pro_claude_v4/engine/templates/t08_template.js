/**
 * Template 08 — 컬러 팔레트만 교체
 */
const THEMES  = require('../core/colors');
const BASE    = require('./base_builder');
const THEME   = THEMES[8];
const build   = (parsed) => BASE.build(THEME, parsed);
module.exports = { build, THEME };
