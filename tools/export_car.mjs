// Export XML with locally installed CAGEBOT vendor generators; no tests or upload.
// Usage: node export_car.mjs <playwright entry> <vendor JS directory> <XML> <INO>
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [modulePath, vendorDir, xmlPath, inoPath] = process.argv.slice(2);
const {chromium} = await import(pathToFileURL(modulePath));
const browser = await chromium.launch({channel: 'chrome', headless: true});
try {
  const page = await browser.newPage();
  await page.route('**/*', route => route.abort());
  await page.setContent('<html><body></body></html>');
  for (const filename of ['blockly_compressed.js', 'en.js', 'blocks_compressed01.js', 'arduino_compressed01.js']) {
    await page.addScriptTag({path: path.join(vendorDir, filename)});
  }
  const source = await fs.readFile(xmlPath, 'utf8');
  const output = await page.evaluate(text => {
    const workspace = new Blockly.Workspace();
    Blockly.Xml.domToWorkspace(Blockly.Xml.textToDom(text), workspace);
    const missing = workspace.getAllBlocks(false).filter(b => !Blockly.Arduino[b.type]);
    if (missing.length) throw new Error('Missing CAGEBOT generators: ' + missing.map(b => b.type).join(','));
    return Blockly.Arduino.workspaceToCode(workspace);
  }, source);
  await fs.writeFile(inoPath, output, 'utf8');
  console.log('Exported Arduino from ' + xmlPath + ' to ' + inoPath);
} finally {
  await browser.close();
}
