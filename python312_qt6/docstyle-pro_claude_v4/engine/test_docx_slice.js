const E = require('./core/elements.js');
const C = require('./templates/template_01_classic.js').C;
const { Document, Packer } = require('docx');

async function main() {
    try {
        const table = E.table3col(["1", "2", "3", "4"], [["a", "b", "c", "d"]], C);
        const doc = new Document({
            sections: [{ children: [table] }]
        });
        await Packer.toBuffer(doc);
        console.log("No error on 4 columns.");
    } catch (err) {
        console.error(`Error stack: ${err.message}`);
    }
}

main();
