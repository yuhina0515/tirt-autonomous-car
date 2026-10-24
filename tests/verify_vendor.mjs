// Run the real, downloaded CAGEBOT Blockly parser and Arduino generator headlessly.
// No login, user browser profile, robot connection, or upload is used.
// Usage: node verify_vendor.mjs <playwright-module> <vendor-js-dir> <xml> <output-ino>
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [modulePath,vendorDir,xmlPath,outPath]=process.argv.slice(2);
const {chromium}=await import(pathToFileURL(modulePath));
const browser=await chromium.launch({channel:'chrome',headless:true});
try {
 const page=await browser.newPage();
 await page.route('**/*',route=>route.abort());
 await page.setContent('<html><body></body></html>');
 for(const f of ['blockly_compressed.js','en.js','blocks_compressed01.js','arduino_compressed01.js'])
  await page.addScriptTag({path:path.join(vendorDir,f)});
 const xml=await fs.readFile(xmlPath,'utf8');
 const result=await page.evaluate(text=>{
  const ws=new Blockly.Workspace();
  const dom=Blockly.Xml.textToDom(text);
  Blockly.Xml.domToWorkspace(dom,ws);
  const unknown=ws.getAllBlocks(false).filter(b=>!Blockly.Arduino[b.type]).map(b=>b.type);
  if(unknown.length)throw Error('Missing vendor generators: '+unknown.join(','));
  const code=Blockly.Arduino.workspaceToCode(ws);
  const roundtrip=Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(ws));
  return {blocks:ws.getAllBlocks(false).length,code,roundtrip};
 },xml);
 await fs.writeFile(outPath,result.code,'utf8');
 await fs.writeFile(outPath+'.roundtrip.xml',result.roundtrip,'utf8');
 console.log(JSON.stringify({vendor_import:'PASS',blocks:result.blocks,
                            vendor_export:outPath,physical_acceptance:'NOT RUN'}));
} finally {await browser.close();}
