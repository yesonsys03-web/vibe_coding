const { execSync } = require('child_process');

for (let i = 1; i <= 50; i++) {
    const tpl = String(i).padStart(2, '0');
    try {
        console.log(`Testing template ${tpl}...`);
        execSync(`node engine/generate.js temp/test_all.json temp/output_${tpl}.docx --template ${tpl}`, { stdio: 'pipe' });
    } catch (err) {
        console.error(`Template ${tpl} failed:`);
        console.error(err.stderr.toString());
    }
}
console.log("Done checking all templates.");
