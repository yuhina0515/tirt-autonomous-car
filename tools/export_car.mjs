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
  const output = await page.evaluate(async text => {
    const workspace = new Blockly.Workspace();
    const dom = Blockly.Xml.textToDom(text);
    const warnings = [];
    Blockly.alert = message => warnings.push(String(message));
    window.alert = message => warnings.push(String(message));
    Blockly.Xml.domToWorkspace(dom, workspace);
    // Loading alone is insufficient: comparison onchange may detach bad inputs.
    await new Promise(resolve => setTimeout(resolve, 50));
    const disconnected = [];
    for (const element of dom.getElementsByTagName('block')) {
      let parent = element.parentNode;
      while (parent && parent.nodeName.toLowerCase() !== 'block') parent = parent.parentNode;
      const block = workspace.getBlockById(element.getAttribute('id'));
      const expected = parent ? parent.getAttribute('id') : null;
      const actual = block && block.getParent() ? block.getParent().id : null;
      if (!block || expected !== actual) disconnected.push(element.getAttribute('id') + ': expected parent ' + expected + ', got ' + actual);
    }
    if (warnings.length || disconnected.length) {
      throw new Error('CAGEBOT import rejected connections: ' + [...warnings, ...disconnected].join('; '));
    }
    const missing = workspace.getAllBlocks(false).filter(b => !Blockly.Arduino[b.type]);
    if (missing.length) throw new Error('Missing CAGEBOT generators: ' + missing.map(b => b.type).join(','));
    return Blockly.Arduino.workspaceToCode(workspace);
  }, source);
  await fs.writeFile(inoPath, output, 'utf8');
  console.log('Exported Arduino from ' + xmlPath + ' to ' + inoPath);
} finally {
  await browser.close();
}
