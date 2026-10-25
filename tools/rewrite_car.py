"""Rebuild the active three-sensor CAGEBOT workspace from the preserved baseline.

This is a structural rewrite, not the temporal controller's build.py pipeline.
Export the resulting XML with the actual CAGEBOT Arduino generator.
"""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = 'https://developers.google.com/blockly/xml'
N = {'b': NS}
ET.register_namespace('', NS)
ET.register_namespace('html', 'http://www.w3.org/1999/xhtml')


def tag(name):
    return '{' + NS + '}' + name


def note(block, text):
    c = ET.SubElement(block, tag('comment'), pinned='false', h='100', w='380')
    c.text = text


def prune_chain(parent, name, remove):
    statement = parent.find("b:statement[@name='%s']" % name, N)
    first = statement.find('b:block', N)
    kept = []
    while first is not None:
        nxt = first.find('b:next', N)
        following = nxt.find('b:block', N) if nxt is not None else None
        if nxt is not None:
            first.remove(nxt)
        if first.get('id') not in remove and first.get('disabled') != 'true':
            kept.append(first)
        first = following
    statement.clear()
    statement.set('name', name)
    holder = statement
    for index, block in enumerate(kept):
        holder.append(block)
        if index < len(kept) - 1:
            holder = ET.SubElement(block, tag('next'))


def rewrite():
    root = ET.fromstring((ROOT / 'legacy/three_sensor_baseline/three_sensor_baseline.xml').read_text(encoding='utf-8'))
    main = root.find("b:block[@type='arduino_setup']", N)
    unused = {'SPEED_BACKWARD', 'SPEED_TURN_INNER_FINE', 'SPEED_TURN_PIVOT',
              'CROSS_HOLD', 'crossCount', 'dist'}
    setup_remove = {
        b.get('id') for b in main.findall('.//b:block', N)
        if b.get('type') == 'variables_declare'
        and b.find("b:field[@name='VAR']", N).text in unused
    }
    prune_chain(main, 'MySetup', setup_remove)
    # Outer ADCs stay available as raw telemetry but never enter F or sumW.
    prune_chain(main, 'MyLoop', {'n7018', 'n7050', 'sm0016', 'sm0060'})
    decision = main.find(".//b:block[@id='n7142']", N)
    old = {child.get('name'): deepcopy(child) for child in decision
           if child.tag in (tag('value'), tag('statement'))}
    tail = decision.find('b:next', N)
    if tail is not None:
        decision.remove(tail)
    decision.clear()
    decision.set('type', 'controls_if')
    decision.set('id', 'car_decision')
    ET.SubElement(decision, tag('mutation'), elseif='3', **{'else': '1'})
    # F=10 holds the previous command; then the original strict ADC turn checks.
    v = ET.SubElement(decision, tag('value'), name='IF0')
    eq = ET.SubElement(v, tag('block'), type='logic_compare', id='car_error_eq')
    ET.SubElement(eq, tag('field'), name='OP').text = 'EQ'
    a = ET.SubElement(eq, tag('value'), name='A')
    getter = ET.SubElement(a, tag('block'), type='variables_get', id='car_error_f')
    ET.SubElement(getter, tag('field'), name='VAR', id='vSensorF').text = 'sensorF'
    b = ET.SubElement(eq, tag('value'), name='B')
    num = ET.SubElement(b, tag('block'), type='math_number', id='car_error_ten')
    ET.SubElement(num, tag('field'), name='NUM').text = '10'
    ET.SubElement(decision, tag('statement'), name='DO0')
    for new, previous in ((1, 6), (2, 7), (3, 8)):
        for prefix in ('IF', 'DO'):
            child = old[prefix + str(previous)]
            child.set('name', prefix + str(new))
            if prefix == 'DO' and previous in (6, 7):
                # Original A3 if/else bodies are identical; keep one motor chain.
                body = deepcopy(child.find("b:block/b:statement[@name='DO0']/b:block", N))
                child.clear()
                child.set('name', prefix + str(new))
                child.append(body)
            decision.append(child)
    decision.append(old['ELSE'])
    if tail is not None:
        decision.append(tail)
    note(decision, 'F=10: hold. Left/right: original proportional steering. F=0: hold 40 loops, then stop. Otherwise forward. No latched stop or new route strategy.')
    # Remove unused helpers and disabled boot tone; keep the existing stop helper.
    for block in list(root.findall('b:block', N)):
        if block.get('type') == 'procedures_defnoreturn':
            if block.find("b:field[@name='NAME']", N).text != 'stop':
                root.remove(block)
    for parent in list(root.iter()):
        for child in list(parent):
            if child.get('disabled') == 'true':
                parent.remove(child)
    variables = root.find('b:variables', N)
    for variable in list(variables):
        if variable.text in unused:
            variables.remove(variable)
    main.set('x', '40')
    main.set('y', '-1400')
    note(main, 'Three-center-sensor baseline rewrite. A4/A3/A2 control only; A5/A1 raw telemetry. PWM100, threshold70, TURN_KP75. Button waits at boot only. LED behavior unchanged.')
    for block_id, text in (
        ('n0232', 'Read all five ADCs; preserve original raw telemetry.'),
        ('three1', 'Exclude A1 and A5 from decisions; control uses A4/A3/A2 only.'),
        ('n7010', 'Build F = 8*A4_on + 4*A3_on + 2*A2_on.'),
        ('sm0002', 'Position weights: A4=-1, A3=0, A2=+1. Integer proportional inner PWM; minimum5.'),
        ('n0210', 'Original 115200-baud raw ADC/F telemetry; no new capture protocol.'),
    ):
        note(main.find(".//b:block[@id='%s']" % block_id, N), text)
    ET.indent(root, space='  ')
    (ROOT / 'car.xml').write_text(ET.tostring(root, encoding='unicode') + '\n', encoding='utf-8')
    print('Rewrote car.xml from the preserved legacy XML; export Arduino next.')


if __name__ == '__main__':
    rewrite()
